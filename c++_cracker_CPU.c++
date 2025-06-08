#include <iostream>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cmath>
#include <iomanip>

using namespace std;

// Style class (same as Python version)
struct Style {
    static constexpr const char* BLACK = "\033[30m";
    static constexpr const char* RED = "\033[31m";
    static constexpr const char* GREEN = "\033[32m";
    static constexpr const char* YELLOW = "\033[33m";
    static constexpr const char* BLUE = "\033[34m";
    static constexpr const char* MAGENTA = "\033[35m";
    static constexpr const char* CYAN = "\033[36m";
    static constexpr const char* WHITE = "\033[37m";
    static constexpr const char* UNDERLINE = "\033[4m";
    static constexpr const char* RESET = "\033[0m";
    static constexpr const char* GREEN_BG = "\033[42m";
    static constexpr const char* RED_BG = "\033[41m";
};

atomic<bool> found(false);
atomic<bool> done_printing(false);
mutex cout_mutex;

string int_to_prefix(size_t idx, size_t prefix_len, const string& charset) {
    size_t charset_size = charset.size();
    string prefix(prefix_len, ' ');
    for (int i = prefix_len - 1; i >= 0; --i) {
        prefix[i] = charset[idx % charset_size];
        idx /= charset_size;
    }
    return prefix;
}

void print_progress(size_t total_attempts, size_t overall_total, double elapsed) {
    double percent = (overall_total > 0) ? (100.0 * total_attempts / overall_total) : 0.0;
    int bar_width = 40;
    int pos = static_cast<int>(bar_width * percent / 100.0);

    // Build colored progress bar
    cout << "\r " << Style::YELLOW << "Attempts: " << Style::WHITE << Style::UNDERLINE << total_attempts << Style::RESET;
    cout << " | " << Style::CYAN << "Speed: " << Style::WHITE << Style::UNDERLINE << static_cast<size_t>(total_attempts / elapsed) << "/s" << Style::RESET;
    cout << " | " << Style::MAGENTA << "Elapsed: " << Style::WHITE << Style::UNDERLINE << fixed << setprecision(2) << elapsed << "s" << Style::RESET;
    cout << " | " << Style::GREEN << "Progress: " << Style::RESET;
    for (int i = 0; i < bar_width; ++i) {
        if (i < pos) cout << Style::GREEN_BG << " " << Style::RESET << Style::GREEN;
        else cout << Style::RED_BG << " " << Style::RESET << Style::GREEN;
    }
    cout << Style::RESET << "";
    cout << Style::WHITE << fixed << setprecision(2) << percent << "%" << Style::RESET;
    cout.flush();
}

void worker(const string& target, const string& charset, int length, size_t prefix_len,
            size_t start_idx, size_t end_idx, atomic<size_t>& total_attempts,
            size_t overall_total, chrono::steady_clock::time_point start_time) {

    size_t charset_size = charset.size();

    for (size_t prefix_idx = start_idx; prefix_idx < end_idx && !found; ++prefix_idx) {
        string prefix = int_to_prefix(prefix_idx, prefix_len, charset);
        size_t suffix_len = length - prefix_len;

        size_t total_combos = pow(charset_size, suffix_len);

        for (size_t i = 0; i < total_combos && !found; ++i) {
            // Build guess
            size_t n = i;
            string guess = prefix;
            for (size_t j = 0; j < suffix_len; ++j) {
                guess += charset[n % charset_size];
                n /= charset_size;
            }

            size_t attempt_now = ++total_attempts;

            // Occasionally print progress (every 100000 attempts)
            if (attempt_now % 100000 == 0 && !found && !done_printing) {
                lock_guard<mutex> lock(cout_mutex);
                auto now = chrono::steady_clock::now();
                double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();
                print_progress(attempt_now, overall_total, elapsed);
            }

            if (guess == target) {
                lock_guard<mutex> lock(cout_mutex);
                auto now = chrono::steady_clock::now();
                double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();

                cout << string(100, ' ') << flush; // Clear line
                cout << Style::GREEN << "\nPassword found: " << Style::WHITE << Style::UNDERLINE << guess << Style::RESET << Style::GREEN;
                cout << "\nTotal attempts: " << total_attempts;
                cout << "\nElapsed time: " << elapsed << " seconds";
                cout << "\nSpeed: " << static_cast<size_t>(total_attempts / elapsed) << " attempts/sec\n";
                cout << string(100, ' ') << flush; // Clear line
                done_printing = true; // tell other threads to stop printing
                this_thread::sleep_for(chrono::milliseconds(300)); // give 300ms pause for stray prints
                found = true;
                return;
            }
        }
    }
}

void parallel_brute_force(const string& target, const string& charset, int max_length) {
    size_t num_threads = thread::hardware_concurrency();
    cout << Style::YELLOW << "Brute-forcing with " << num_threads << " threads" << Style::RESET << "\n";

    atomic<size_t> total_attempts(0);
    auto start_time = chrono::steady_clock::now();

    size_t overall_total = 0;
    for (int l = 1; l <= max_length; ++l) {
        overall_total += pow(charset.size(), l);
    }

    for (int length = 1; length <= max_length && !found; ++length) {
        size_t prefix_len = (length > 2) ? 2 : 1;
        size_t total_prefixes = pow(charset.size(), prefix_len);

        size_t chunk_size = (total_prefixes + num_threads - 1) / num_threads;

        vector<thread> threads;

        for (size_t t = 0; t < num_threads; ++t) {
            size_t start_idx = t * chunk_size;
            size_t end_idx = min(start_idx + chunk_size, total_prefixes);

            threads.emplace_back(worker, ref(target), ref(charset), length, prefix_len,
                                 start_idx, end_idx, ref(total_attempts),
                                 overall_total, start_time);
        }

        for (auto& th : threads) {
            th.join();
        }
    }

    if (!found) {
        cout << Style::RED << "\nPassword not found.\n" << Style::RESET;
    }
}

int main() {
    string target;
    cout << Style::YELLOW << "-- CPU Password Cracker -- \n" << Style::RESET;
    cout << Style::BLUE << "\nEnter password to crack: " << Style::RESET;
    getline(cin, target);

    string charset;
    for (char c : target) {
        if (islower(c) && charset.find_first_of("abcdefghijklmnopqrstuvwxyz") == string::npos) charset += "abcdefghijklmnopqrstuvwxyz";
        if (isupper(c) && charset.find_first_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ") == string::npos) charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if (isdigit(c) && charset.find_first_of("0123456789") == string::npos) charset += "0123456789";
        if (ispunct(c) && charset.find(c) == string::npos) charset += c;
        if (isspace(c) && charset.find(' ') == string::npos) charset += ' ';
    }

    cout << Style::GREEN << "Detected charset: " << charset << Style::RESET << "\n";

    parallel_brute_force(target, charset, target.length());

    cout << "\nPress Enter to exit...";
    cin.get();
    return 0;
}
