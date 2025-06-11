import itertools, os, string, time
from multiprocessing import cpu_count, get_context
from datetime import datetime as dt

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

def worker(args):
    target, charset, length, prefixes = args
    attempts = 0
    charset_tuple = tuple(charset)
    target_str = target
    for prefix in prefixes:
        suffix_len = length - len(prefix)
        if suffix_len == 0:
            guess = prefix
            attempts += 1 # Check if prefix is the target
            if guess == target_str:
                return guess, attempts
        else:
            # Use bytes if all input is ascii for slight performance gain
            for combo in itertools.product(charset_tuple, repeat=suffix_len):
                guess = prefix + ''.join(combo)
                attempts += 1
                if guess == target_str:
                    return guess, attempts
    return None, attempts

def chunk_prefixes(charset, num_chunks, prefix_len=2):
    # Use prefix_len=2 for more even work distribution for longer passwords
    prefixes = [''.join(p) for p in itertools.product(charset, repeat=prefix_len)]
    chunk_size = (len(prefixes) + num_chunks - 1) // num_chunks
    return [prefixes[i:i + chunk_size] for i in range(0, len(prefixes), chunk_size)]

def parallel_brute_force_crack(target, charset, max_length):
    num_workers = cpu_count()
    print(f"Brute-forcing with {num_workers} workers, charset size {len(charset)} and target length {max_length}")

    ctx = get_context("spawn")
    start_time = time.time()
    total_attempts = 0
    overall_total = sum(len(charset) ** l for l in range(1, max_length + 1))

    for length in range(1, max_length + 1):
        prefix_len = 2 if length > 2 else 1
        prefixes_chunks = chunk_prefixes(charset, num_workers, prefix_len=prefix_len)
        args = [(target, charset, length, chunk) for chunk in prefixes_chunks]
        with ctx.Pool(num_workers) as pool:
            results = pool.map_async(worker, args)
            found = None
            last_update = 0
            # Progress reporting loop
            while not results.ready():
                now = time.time()
                if now - last_update > 0.01: # Only update every 0.01s
                    completed = sum(pool._cache[k]._value is not None for k in pool._cache)
                    est_attempts = total_attempts + completed * (len(charset) ** (length - prefix_len)) * len(prefixes_chunks[0])
                    percent = 100 * est_attempts / overall_total if overall_total else 0
                    bar_total = 40
                    filled = int(bar_total * percent / 100)
                    green_part = '\033[42m' + ' ' * filled
                    red_part = '\033[41m' + ' ' * (bar_total - filled)
                    elapsed = now - start_time
                    bar = green_part + red_part + '\033[0m'
                    speed = round(est_attempts / elapsed if elapsed > 0 else 0, 2)
                    print(f"\r {style.YELLOW}Attempts: {style.WHITE}{style.UNDERLINE}{est_attempts}{style.RESET} |  {style.CYAN}Speed: {style.WHITE}{style.UNDERLINE}{speed:.2f}/s{style.RESET} | {style.GREEN}[{bar}]{style.RESET} {percent:.2f}%", end="", flush=True)
                    last_update = now
                time.sleep(0.05)
            for res, attempts in results.get():
                total_attempts += attempts
                if res:
                    found = res
                    break
            if found:
                elapsed = time.time() - start_time
                speed = total_attempts / elapsed if elapsed > 0 else 0
                print("\033[2K\r", end="")  # Clear the entire line and move cursor to start
                print(f"\n{style.GREEN}Password found: {style.WHITE}{style.UNDERLINE}{found}{style.RESET}{style.GREEN}, check log (logs/log_{found}.txt) for details.{style.RESET}")
                log_results(found, total_attempts, elapsed, speed)
                return found

    print("\nPassword not found.")
    return None

def log_results(password, attempts, elapsed, speed):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = dt.now().strftime("%Yy-%mm-%dd_%H-%M-%S")
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
        print(style.YELLOW + "-- CPU Password Cracker -- \n" + style.RESET)
        target = input(style.BLUE + "\nEnter the password to crack for simulation (slow for 8+ digits): " + style.RESET).strip()
        charset = ''.join(s for s in [string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation, ' '] if any(c in s for c in target))
        print(style.GREEN + f"Detected charset: {charset}" + style.RESET)
        max_length = len(target)
        parallel_brute_force_crack(target, charset, max_length)
    except KeyboardInterrupt:
        print(style.RED + "\nExiting due to keyboard interrupt." + style.RESET)
    except Exception as e:
        print(style.RED + f"\nAn error occurred: {e}" + style.RESET)