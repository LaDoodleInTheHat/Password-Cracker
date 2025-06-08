#include <iostream>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cmath>
#include <iomanip>

using namespace std;

atomic<bool> found(false);
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

    cout << "\r[";
    for (int i = 0; i < bar_width; ++i) {
        if (i < pos) cout << "=";
        else if (i == pos) cout << ">";
        else cout << " ";
    }
    cout << "] ";
    cout << fixed << setprecision(2) << percent << "% ";
    cout << "Speed: " << static_cast<size_t>(total_attempts / elapsed) << " attempts/sec ";
    cout.flush();
}

void worker(const string& target, const string& charset, int length, size_t prefix_len,
            size_t start_idx, size_t end_idx, atomic<size_t>& total_attempts,
            size_t overall_total, chrono::steady_clock::time_point start_time) {

    size_t charset_size = charset.size();

    size_t last_progress_update = 0;

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
            if (attempt_now % 100000 == 0 && !found) {
                lock_guard<mutex> lock(cout_mutex);
                auto now = chrono::steady_clock::now();
                double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();
                print_progress(attempt_now, overall_total, elapsed);
            }

            if (guess == target) {
                lock_guard<mutex> lock(cout_mutex);
                auto now = chrono::steady_clock::now();
                double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();

                cout << "\n\nPassword found: " << guess << endl;
                cout << "Total attempts: " << attempt_now << endl;
                cout << "Elapsed time: " << elapsed << " seconds" << endl;
                cout << "Speed: " << static_cast<size_t>(attempt_now / elapsed) << " attempts/sec\n";
                found = true;
                return;
            }
        }
    }
}

void parallel_brute_force(const string& target, const string& charset, int max_length) {
    size_t num_threads = thread::hardware_concurrency();
    cout << "Brute-forcing with " << num_threads << " threads\n";

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
        cout << "\nPassword not found.\n";
    }
}

int main() {
    string target;
    cout << "Enter password to crack: ";
    getline(cin, target);

    string charset;
    for (char c : target) {
        if (islower(c) && charset.find_first_of("abcdefghijklmnopqrstuvwxyz") == string::npos) charset += "abcdefghijklmnopqrstuvwxyz";
        if (isupper(c) && charset.find_first_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ") == string::npos) charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if (isdigit(c) && charset.find_first_of("0123456789") == string::npos) charset += "0123456789";
        if (ispunct(c) && charset.find(c) == string::npos) charset += c;
        if (isspace(c) && charset.find(' ') == string::npos) charset += ' ';
    }

    cout << "Using charset: " << charset << "\n";

    parallel_brute_force(target, charset, target.length());

    cout << "\nPress Enter to exit...";
    cin.get();
    return 0;
}
