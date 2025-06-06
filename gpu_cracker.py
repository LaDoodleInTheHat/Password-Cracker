import cupy as cp
import string
import itertools
import math
import time

# Your target
target = input("Enter target password: ").strip()
target_length = len(target)
charset = ''.join(s for s in [string.ascii_lowercase, string.ascii_uppercase, string.digits, string.punctuation, ' '] if any(c in s for c in target))

charset_size = len(charset)
target_gpu = cp.array([ord(c) for c in target], dtype=cp.uint8)

# Batch size — tradeoff between GPU memory and speed
BATCH_SIZE = 500_000

def int_to_str_batch(start_idx, batch_size, length):
    """Convert integer indices to batch of strings as integer arrays"""
    indices = cp.arange(start_idx, start_idx + batch_size, dtype=cp.uint64)
    
    # Base conversion: each number is a base-len(charset) number representing one guess
    chars_idx = cp.zeros((batch_size, length), dtype=cp.uint8)
    
    for pos in reversed(range(length)):
        chars_idx[:, pos] = indices % charset_size
        indices //= charset_size
        
    # Now convert indices to actual characters
    charset_gpu = cp.array([ord(c) for c in charset], dtype=cp.uint8)
    chars = charset_gpu[chars_idx]
    return chars

def batch_brute_force():
    total_combinations = charset_size ** target_length
    print(f"Total combinations: {total_combinations:,}")
    
    start_time = time.time()
    found = None
    attempts = 0
    
    for batch_start in range(0, total_combinations, BATCH_SIZE):
        current_batch_size = min(BATCH_SIZE, total_combinations - batch_start)
        
        guesses_gpu = int_to_str_batch(batch_start, current_batch_size, target_length)
        
        # Compare each row with target
        matches = cp.all(guesses_gpu == target_gpu[None, :], axis=1)
        
        # Check if any match found
        found_indices = cp.where(matches)[0]
        
        attempts += current_batch_size
        
        elapsed = time.time() - start_time
        speed = attempts / elapsed if elapsed > 0 else 0
        
        percent = 100 * (batch_start + current_batch_size) / total_combinations
        print(f"\rAttempts: {attempts:,} | Speed: {speed:,.2f} /s | Progress: {percent:.2f}%", end="", flush=True)
        
        if found_indices.size > 0:
            found_idx = int(found_indices[0].get())
            guess_chars = guesses_gpu[found_idx].get()
            found = ''.join(chr(c) for c in guess_chars)
            break
    
    print()
    if found:
        print(f"\nPassword FOUND: {found}")
    else:
        print("\nPassword not found.")

if __name__ == "__main__":
    batch_brute_force()
