import os, time, string
from datetime import datetime

try:
    import cupy as cp # type: ignore
except ImportError:
    print("CuPy is not installed. Please install it with 'pip install cupy-cuda11x' for your CUDA version.")
    exit(1)

if not cp.cuda.runtime.getDeviceCount():
    print("No CUDA-capable GPU detected.")
    exit(1)

class Style:
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

# Utility to get a dynamic batch size based on available GPU memory
def get_dynamic_batch_size(length, charset_size, safety_factor=0.85, max_batch=2_000_000):
    try:
        free_mem = cp.cuda.Device().mem_info[0]  # Free bytes
        bytes_per_guess = length  # 1 byte per char
        # Add some overhead for arrays, and double as a safety margin
        max_guesses = int(free_mem * safety_factor // (bytes_per_guess * 2))
        return max(1, min(max_batch, max_guesses))
    except Exception as e:
        print(f"{Style.RED}Couldn't determine GPU memory, using default batch size. Error: {e}{Style.RESET}")
        return 500_000

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

def log_results(password, attempts, elapsed, speed):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Yy-%mm-%dd_%H-%M-%S")
    base_filename = f"log_{timestamp}_{password}.log"
    log_path = os.path.join(log_dir, base_filename)
    count = 1
    while os.path.exists(log_path):
        count += 1
        base_filename = f"log_{timestamp}_{password}_{count}.log"
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

def print_progress_bar(total_attempts, speed, percent, bar_total=40):
    filled = int(bar_total * percent / 100)
    green_part = '\033[42m' + ' ' * filled
    red_part = '\033[41m' + ' ' * (bar_total - filled)
    bar = green_part + red_part + '\033[0m'
    print(f"\r {Style.YELLOW}Attempts: {Style.WHITE}{Style.UNDERLINE}{total_attempts}{Style.RESET} |  {Style.CYAN}Speed: {Style.WHITE}{Style.UNDERLINE}{speed:.2f}/s{Style.RESET} | {Style.MAGENTA}Progress: {Style.WHITE}{Style.UNDERLINE}{percent:.2f}%{Style.RESET} | {bar}", end="")

def gpu_brute_force_crack(target, charset, max_length, batch_size=None, progress_update_interval=0.5):
    target_gpu = cp.array([ord(c) for c in target], dtype=cp.uint8)
    start_time = time.time()
    total_attempts = 0
    overall_total = sum(len(charset) ** l for l in range(1, max_length + 1))
    print(f"Brute-forcing on GPU, charset size {len(charset)}, target length ≤ {max_length}")

    found = None
    last_progress_update = time.time()
    for length in range(1, max_length + 1):
        total_combos = len(charset) ** length
        current_batch_size = batch_size or get_dynamic_batch_size(length, len(charset))
        for batch_start in range(0, total_combos, current_batch_size):
            this_batch_size = min(current_batch_size, total_combos - batch_start)
            try:
                guesses_gpu = int_to_str_batch(batch_start, this_batch_size, length, charset)
                matches = cp.all(guesses_gpu == target_gpu[None, :], axis=1)
                found_indices = cp.where(matches)[0]
            except cp.cuda.memory.OutOfMemoryError:
                print(f"{Style.RED}\nOut of GPU memory. Try reducing batch size.{Style.RESET}")
                return None
            total_attempts += this_batch_size

            elapsed = time.time() - start_time
            speed = total_attempts / elapsed if elapsed > 0 else 0
            percent = 100 * total_attempts / overall_total if overall_total else 0

            # Throttle progress updates for very fast GPUs
            if time.time() - last_progress_update > progress_update_interval or found_indices.size > 0:
                print_progress_bar(total_attempts, speed, percent)
                last_progress_update = time.time()

            if found_indices.size > 0:
                found_idx = int(found_indices[0].get())
                guess_chars = guesses_gpu[found_idx].get()
                found = ''.join(chr(c) for c in guess_chars)
                print("\033[2K\r", end="")  # Clear line
                print(f"\n{Style.GREEN}Password found: {Style.WHITE}{Style.UNDERLINE}{found}{Style.RESET}{Style.GREEN}, check log (logs/log_{datetime.now().strftime('%Yy-%mm-%dd_%H-%M-%S')}_{found}.log) for details.{Style.RESET}")
                log_results(found, total_attempts, elapsed, speed)
                return found
    print("\nPassword not found.")
    return None

if __name__ == "__main__":
    try:
        print(Style.BLUE + "\n--- GPU Password Cracker ---" + Style.RESET)

        target = input(Style.BLUE + "\nEnter the password to crack for simulation (slow for 8+ digits): " + Style.RESET).strip()
        charset = ''.join(s for s in [string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation, ' '] if any(c in s for c in target))

        print(Style.GREEN + f"Using charset: {charset}" + Style.RESET)

        max_length =  len(target)

        batch_size_input = input(Style.MAGENTA + f"Batch size (auto for blank, a batch size is the amount of GPU kernels running simultaneously): " + Style.RESET).strip()
        batch_size = int(batch_size_input) if batch_size_input else 1_000_000  # Default batch size
        
        gpu_brute_force_crack(target, charset, max_length, batch_size)
    except KeyboardInterrupt:
        print(Style.RED + "\nExiting due to keyboard interrupt." + Style.RESET)
    except Exception as e:
        print(f"{Style.RED}Error: {e}{Style.RESET}")