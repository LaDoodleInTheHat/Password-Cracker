#include <iostream>
#include <vector>
#include <thread>
#include <mutex>
#include <atomic>
#include <chrono>
#include <cmath>

using namespace std;

atomic<bool> found(false);
mutex cout_mutex;

void worker(const string& target, const string& charset, int length, const vector<string>& prefixes, atomic<size_t>& total_attempts) {
    size_t charset_size = charset.size();
    vector<size_t> indices(length);

    for (const auto& prefix : prefixes) {
        size_t suffix_len = length - prefix.size();

        size_t total_combos = pow(charset_size, suffix_len);
        for (size_t i = 0; i < total_combos && !found; ++i) {
            // Build guess
            size_t n = i;
            string guess = prefix;
            for (size_t j = 0; j < suffix_len; ++j) {
                guess += charset[n % charset_size];
                n /= charset_size;
            }

            total_attempts++;

            if (guess == target) {
                lock_guard<mutex> lock(cout_mutex);
                cout << "\nPassword found: " << guess << endl;
                found = true;
                return;
            }
        }
    }
}

vector<string> generate_prefixes(const string& charset, size_t prefix_len) {
    vector<string> prefixes;
    size_t charset_size = charset.size();
    size_t total_prefixes = pow(charset_size, prefix_len);

    for (size_t i = 0; i < total_prefixes; ++i) {
        size_t n = i;
        string prefix;
        for (size_t j = 0; j < prefix_len; ++j) {
            prefix += charset[n % charset_size];
            n /= charset_size;
        }
        prefixes.push_back(prefix);
    }
    return prefixes;
}

void parallel_brute_force(const string& target, const string& charset, int max_length) {
    size_t num_threads = thread::hardware_concurrency();
    cout << "Brute-forcing with " << num_threads << " threads\n";

    atomic<size_t> total_attempts(0);
    auto start_time = chrono::steady_clock::now();

    for (int length = 1; length <= max_length && !found; ++length) {
        size_t prefix_len = (length > 2) ? 2 : 1;
        vector<string> prefixes = generate_prefixes(charset, prefix_len);

        size_t chunk_size = (prefixes.size() + num_threads - 1) / num_threads;

        vector<thread> threads;
        for (size_t t = 0; t < num_threads; ++t) {
            size_t start = t * chunk_size;
            size_t end = min(start + chunk_size, prefixes.size());
            vector<string> chunk(prefixes.begin() + start, prefixes.begin() + end);

            threads.emplace_back(worker, ref(target), ref(charset), length, move(chunk), ref(total_attempts));
        }

        for (auto& th : threads) {
            th.join();
        }
    }

    auto end_time = chrono::steady_clock::now();
    chrono::duration<double> elapsed = end_time - start_time;

    if (!found) {
        cout << "Password not found.\n";
    }

    cout << "Total attempts: " << total_attempts << "\n";
    cout << "Elapsed time: " << elapsed.count() << "s\n";
    cout << "Speed: " << total_attempts / elapsed.count() << " attempts/sec\n";
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

    return 0;
}
