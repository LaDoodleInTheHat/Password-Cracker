import sys
import time

# ANSI colors
RED = "\033[41m"    # Red background
GREEN = "\033[42m"  # Green background
RESET = "\033[0m"   # Reset color

def colorful_loading_bar(total=50, delay=0.1):
    print("Installing:")
    for i in range(total + 1):
        green_part = GREEN + ' ' * i
        red_part = RED + ' ' * (total - i)
        bar = green_part + red_part + RESET
        percent = (i / total) * 100
        sys.stdout.write(f"\r{bar} {percent:5.1f}%")
        sys.stdout.flush()
        time.sleep(delay)
    print("\nDone!")

colorful_loading_bar()

colorful_loading_bar(100, 0.05)  # Example usage with a longer bar and shorter delay