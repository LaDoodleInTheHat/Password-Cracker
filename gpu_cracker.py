import cupy as cp
import string
import os
import time
from datetime import datetime

class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# Parameters
BATCH_SIZE = 500_000  # Tune based on GPU memory

def int_to_str_batch(start_idx, batch_size, length, charset):
    """Convert integer indices to batch of strings as integer arrays"""
    charset_size = len(charset)
    indices = cp.arange(start_idx, start_idx + batch_size, dtype=cp.uint64)
    
    chars_idx = cp.zeros((batch_size, length), dtype=cp.uint8)
    for pos in reversed(range(length)):
        chars_idx[:, pos] = indices % charset_size
        indices //= charset_size

    charset_gpu = cp.array([ord(c) for c in charset], dtype=cp.uint8)
    chars = charset_gpu[chars_idx]
    return chars

def gpu_brute_force_crack(target, charset, max_length):
    target_gpu = cp.array([ord(c) for c in target], dtype=cp.uint8)
    start_time = time.time()
    total_attempts = 0

    overall_total = sum(len(charset) ** l for l in range(1, max_length + 1))
    print(f"Brute-forcing on GPU, charset size {len(charset)}, target length ≤ {max_length}")

    found = None

    for length in range(1, max_length + 1):
        total_combos = len(charset) ** length
        for batch_start in range(0, total_combos, BATCH_SIZE):
            current_batch_size = min(BATCH_SIZE, total_combos - batch_start)
            guesses_gpu = int_to_str_batch(batch_start, current_batch_size, length, charset)
            matches = cp.all(guesses_gpu == target_gpu[None, :], axis=1)

            found_indices = cp.where(matches)[0]
            total_attempts += current_batch_size

            elapsed = time.time() - start_time
            speed = total_attempts / elapsed if elapsed > 0 else 0
            percent = 100 * total_attempts / overall_total if overall_total else 0

            # Progress bar
            bar_total = 40
            filled = int(bar_total * percent / 100)
            green_part = '\033[42m' + ' ' * filled
            red_part = '\033[41m' + ' ' * (bar_total - filled)
            bar = green_part + red_part + '\033[0m'

            print(f"\r {style.YELLOW}Attempts: {style.WHITE}{style.UNDERLINE}{total_attempts}{style.RESET} |  {style.CYAN}Speed: {style.WHITE}{style.UNDERLINE}{speed:.2f}/s{style.RESET} | {style.RED}Progress: {bar} | {style.GREEN}Elapsed: {style.WHITE}{style.UNDERLINE}{elapsed:.2f}s{style.RESET} ", end="", flush=True)

            if found_indices.size > 0:
                found_idx = int(found_indices[0].get())
                guess_chars = guesses_gpu[found_idx].get()
                found = ''.join(chr(c) for c in guess_chars)
                
                print("\033[2K\r", end="")  # Clear line
                print(f"\n{style.GREEN}Password found: {style.WHITE}{style.UNDERLINE}{found}{style.RESET}{style.GREEN}, check log (logs/log_{found}.txt) for details.{style.RESET}")
                log_results(found, total_attempts, elapsed, speed)
                return found

    print("\nPassword not found.")
    return None

def log_results(password, attempts, elapsed, speed):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Yy-%mm-%dd_%H-%M-%S")
    base_filename = f"log_{password}_{timestamp}.log"
    log_path = os.path.join(log_dir, base_filename)
    count = 1
    while os.path.exists(log_path):
        count += 1
        base_filename = f"log_{password}_{timestamp}_{count}.txt"
        log_path = os.path.join(log_dir, base_filename)

    log_content = (
        f"Password found: {password}\n"
        f"Attempts: {attempts}\n"
        f"Time: {elapsed:.2f}s\n"
        f"Speed: {speed:.2f} attempts/sec\n"
    )
    with open(log_path, "w") as f:
        f.write(log_content)

    latest_log_path = os.path.join(log_dir, "latest.log")
    with open(latest_log_path, "w") as f:
        f.write(log_content)

if __name__ == "__main__":
    try:
        target = input(style.BLUE + "\nEnter the password to crack for simulation (slow for 8+ digits): " + style.RESET).strip()
        charset = ''.join(s for s in [string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation, ' '] if any(c in s for c in target))

        print(style.GREEN + f"Detected charset: {charset}" + style.RESET)
        max_length = len(target)
        gpu_brute_force_crack(target, charset, max_length)
    except KeyboardInterrupt:
        print(style.RED + "\nExiting due to keyboard interrupt." + style.RESET)
