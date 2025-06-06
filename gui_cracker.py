import itertools
import string
import time
import threading
from multiprocessing import Pool, cpu_count, get_context
import tkinter as tk
from tkinter import ttk, messagebox

def detect_charset(password):
    charset = ''
    if any(c.islower() for c in password):
        charset += string.ascii_lowercase
    if any(c.isupper() for c in password):
        charset += string.ascii_uppercase
    if any(c.isdigit() for c in password):
        charset += string.digits
    if any(c in string.punctuation for c in password):
        charset += string.punctuation
    return charset

def worker(args):
    target, charset, length, prefixes = args
    attempts = 0
    for prefix in prefixes:
        for combo in itertools.product(charset, repeat=length - len(prefix)):
            guess = prefix + ''.join(combo)
            attempts += 1
            if guess == target:
                return guess, attempts
    return None, attempts

def chunk_prefixes(charset, num_chunks):
    chunk_size = (len(charset) + num_chunks - 1) // num_chunks
    return [charset[i:i + chunk_size] for i in range(0, len(charset), chunk_size)]

def log_results(password, attempts, elapsed, speed):
    with open("bruteforce_log.txt", "w") as f:
        f.write(f"Password found: {password}\n")
        f.write(f"Attempts: {attempts}\n")
        f.write(f"Time: {elapsed:.2f}s\n")
        f.write(f"Speed: {speed:.2f} attempts/sec\n")

def parallel_brute_force_crack(target, charset, max_length, update_callback, stop_event):
    num_workers = cpu_count()
    ctx = get_context("spawn")
    start_time = time.time()
    total_attempts = 0
    overall_total = sum(len(charset) ** l for l in range(1, max_length + 1))

    for length in range(1, max_length + 1):
        if stop_event.is_set():
            update_callback("Cracking stopped.")
            return None

        prefixes_chunks = chunk_prefixes(charset, num_workers)
        args = [(target, charset, length, chunk) for chunk in prefixes_chunks]

        with ctx.Pool(num_workers) as pool:
            results = pool.map_async(worker, args)
            found = None

            while not results.ready():
                if stop_event.is_set():
                    pool.terminate()
                    update_callback("Cracking stopped.")
                    return None
                elapsed = time.time() - start_time
                est_attempts = total_attempts + (len(charset) ** (length - 1)) * len(prefixes_chunks[0])
                percent = min(100 * est_attempts / overall_total, 100)
                speed = est_attempts / elapsed if elapsed > 0 else 0
                update_callback(f"Attempts: {est_attempts} | Speed: {speed:.2f}/s | Progress: {percent:.2f}% | Time: {elapsed:.2f}s", percent)
                time.sleep(0.5)

            for res, attempts in results.get():
                total_attempts += attempts
                if res:
                    found = res
                    break

            if found:
                elapsed = time.time() - start_time
                speed = total_attempts / elapsed if elapsed > 0 else 0
                update_callback(f"Password found: {found} in {elapsed:.2f}s, {total_attempts} attempts. Speed: {speed:.2f}/s", 100)
                log_results(found, total_attempts, elapsed, speed)
                return found

    update_callback("Password not found.", 100)
    return None

class BruteForceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Cracker Simulator")
        self.root.configure(bg="#1e1e1e")

        self.stop_event = threading.Event()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", background="#333", foreground="white", relief="flat")
        style.map("TButton", background=[("active", "#555")])
        style.configure("TProgressbar", troughcolor="#333", background="#4CAF50")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = tk.Frame(self.root, bg="#1e1e1e", padx=20, pady=20)
        main_frame.grid(sticky="nsew")

        self.label = tk.Label(main_frame, text="Enter Password:", bg="#1e1e1e", fg="white")
        self.label.grid(row=0, column=0, sticky="ew")

        self.entry = tk.Entry(main_frame, show="*", bg="#333", fg="white", insertbackground="white")
        self.entry.grid(row=1, column=0, sticky="ew", pady=5)

        self.progress_label = tk.Label(main_frame, text="Progress will appear here.", bg="#1e1e1e", fg="white")
        self.progress_label.grid(row=2, column=0, sticky="ew", pady=5)

        self.progressbar = ttk.Progressbar(main_frame, length=400, mode="determinate")
        self.progressbar.grid(row=3, column=0, sticky="ew", pady=5)

        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.grid(row=4, column=0, pady=10)

        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_cracking)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_cracking, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        main_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure((0, 1), weight=1)

    def update_status(self, message, percent=None):
        self.progress_label.config(text=message)
        if percent is not None:
            self.progressbar["value"] = percent
        self.root.update_idletasks()

    def start_cracking(self):
        password = self.entry.get().strip()
        if not password:
            messagebox.showerror("Error", "Please enter a password.")
            return

        self.stop_event.clear()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progressbar["value"] = 0
        charset = detect_charset(password)
        max_length = len(password)

        def run_crack():
            try:
                parallel_brute_force_crack(
                    password,
                    charset,
                    max_length,
                    self.update_status,
                    self.stop_event
                )
            finally:
                self.start_button.config(state=tk.NORMAL)
                self.stop_button.config(state=tk.DISABLED)

        threading.Thread(target=run_crack, daemon=True).start()

    def stop_cracking(self):
        self.stop_event.set()
        self.update_status("Stopping...", None)

if __name__ == "__main__":
    root = tk.Tk()
    app = BruteForceGUI(root)
    root.mainloop()
