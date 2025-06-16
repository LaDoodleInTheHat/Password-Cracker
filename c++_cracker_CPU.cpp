#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cmath>
#include <iomanip>

#include "include/json.hpp"
using json = nlohmann::json;

using namespace std;

// Style class
struct Style {
    static constexpr const char* RESET = "\033[0m";
    static constexpr const char* RED = "\033[31m";
    static constexpr const char* GREEN = "\033[32m";
    static constexpr const char* BLUE = "\033[34m";
    static constexpr const char* CYAN = "\033[36m";
    static constexpr const char* BOLD = "\033[1m";
};

atomic<bool> found(false);
atomic<bool> done_printing(false);
atomic<bool> printing_final(false);
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

    cout << "\r" << Style::CYAN << " Attempts: " << Style::RESET << total_attempts;
    cout << Style::CYAN << " | Speed: " << Style::RESET << static_cast<size_t>(total_attempts / elapsed) << "/s";
    cout << Style::CYAN << " | Elapsed: " << Style::RESET << fixed << setprecision(2) << elapsed << "s";
    cout << Style::CYAN << " | [" << Style::RESET;
    for (int i = 0; i < bar_width; ++i) {
        if (i < pos)
            cout << Style::GREEN << "=" << Style::RESET;
        else
            cout << Style::BLUE << "-" << Style::RESET;
    }
    cout << Style::CYAN << "] " << Style::RESET;
    cout << fixed << setprecision(2) << percent << "%";
    cout.flush();
}

void worker(const string& target, const string& charset, int length, size_t prefix_len,
            size_t start_idx, size_t end_idx, atomic<size_t>& total_attempts,
            size_t overall_total, chrono::steady_clock::time_point start_time,
            size_t progress_interval, bool enable_progress) {

    size_t charset_size = charset.size();

    for (size_t prefix_idx = start_idx; prefix_idx < end_idx && !found; ++prefix_idx) {
        string prefix = int_to_prefix(prefix_idx, prefix_len, charset);
        size_t suffix_len = length - prefix_len;

        size_t total_combos = pow(charset_size, suffix_len);

        for (size_t i = 0; i < total_combos && !found; ++i) {
            size_t n = i;
            string guess = prefix;
            for (size_t j = 0; j < suffix_len; ++j) {
                guess += charset[n % charset_size];
                n /= charset_size;
            }

            size_t attempt_now = ++total_attempts;

            if (attempt_now % progress_interval == 0 && !found && !done_printing && !printing_final && enable_progress) {
                lock_guard<mutex> lock(cout_mutex);
                if (!printing_final) {
                    auto now = chrono::steady_clock::now();
                    double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();
                    print_progress(attempt_now, overall_total, elapsed);
                }
            }

            if (guess == target) {
                lock_guard<mutex> lock(cout_mutex);
                printing_final = true;

                auto now = chrono::steady_clock::now();
                double elapsed = chrono::duration_cast<chrono::duration<double>>(now - start_time).count();

                cout << "\033[2K\r" << flush;
                cout << "\n" << Style::GREEN << Style::BOLD << "Password found: " << Style::RESET << Style::GREEN << guess << Style::RESET;
                cout << "\n" << Style::CYAN << "Total attempts: " << Style::RESET << total_attempts;
                cout << "\n" << Style::CYAN << "Elapsed time: " << Style::RESET << elapsed << " seconds";
                cout << "\n" << Style::CYAN << "Speed: " << Style::RESET << static_cast<size_t>(total_attempts / elapsed) << " attempts/sec\n";

                this_thread::sleep_for(chrono::milliseconds(300));
                done_printing = true;
                found = true;
                return;
            }
        }
    }
}

void parallel_brute_force(const string& target, const string& charset, int max_length,
                          size_t progress_interval, bool enable_progress) {

    size_t num_threads = thread::hardware_concurrency();
    cout << Style::BLUE << "Brute-forcing with " << num_threads << " threads" << Style::RESET << "\n";

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
                                 overall_total, start_time, progress_interval, enable_progress);
        }

        for (auto& th : threads) {
            th.join();
        }
    }

    if (!found) {
        cout << "\n" << Style::RED << "Password not found." << Style::RESET << "\n";
    }
}

int main() {
    size_t progress_interval = 100000;
    bool enable_progress = true;

    try {
        ifstream config_file("config/c++_config.json");
        if (!config_file.is_open()) throw runtime_error("Could not open config/c++_config.json");

        json config;
        config_file >> config;

        progress_interval = config.value("progress_interval", 100000);
        enable_progress = config.value("enable_progress", true);

        cout << Style::CYAN << "Using progress_interval: " << Style::RESET << progress_interval << "\n";
        cout << Style::CYAN << "Progress display enabled: " << Style::RESET << (enable_progress ? "YES" : "NO") << "\n";

    } catch (const exception& e) {
        cout << Style::RED << "Config error: " << e.what() << ". Using defaults." << Style::RESET << "\n";
    }

    string target;
    cout << Style::BOLD << Style::BLUE << "-- CPU Password Cracker --" << Style::RESET << "\n";
    cout << "\nEnter password to crack: ";
    getline(cin, target);

    string charset;
    for (char c : target) {
        if (islower(c) && charset.find_first_of("abcdefghijklmnopqrstuvwxyz") == string::npos) charset += "abcdefghijklmnopqrstuvwxyz";
        if (isupper(c) && charset.find_first_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ") == string::npos) charset += "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        if (isdigit(c) && charset.find_first_of("0123456789") == string::npos) charset += "0123456789";
        if (ispunct(c) && charset.find("~!@#$%^&*()-_=+[]{}|;:',.<>?/") == string::npos) charset += "~!@#$%^&*()-_=+[]{}|;:',.<>?/";
        if (isspace(c) && charset.find(' ') == string::npos) charset += ' ';
    }

    if (charset.empty()) {
        cout << Style::RED << "Error: No valid characters found in the target password." << Style::RESET << "\n";
        cout << "Please ensure the password contains valid characters (letters, digits, punctuation).\n";
        cout << "\nPress Enter to exit...";
        cin.get();
        return 1;
    }

    cout << Style::CYAN << "Detected charset: " << Style::RESET << charset << "\n";

    parallel_brute_force(target, charset, target.length(), progress_interval, enable_progress);

    cout << "\nPress Enter to exit...";
    cin.get();
    return 0;
}
