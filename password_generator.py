import random, string, pyaes, os, math

LOWERCASE_LETTERS = list(string.ascii_lowercase)
UPPERCASE_LETTERS = list(string.ascii_uppercase)
DIGIT_CHARACTERS = list(string.digits)
SPECIAL_CHARACTERS = list("!@#$%^&*()-_=+[{]};:'\",<.>/?\\|`~")
SEPARATOR_LINE = "-" * 72

with open('config/words') as word_file:
    WORD_LIST = [line.strip() for line in word_file]

def generate_encryption_key(key_length=16):
    return os.urandom(key_length)

def encrypt_and_save_password(password, encryption_key, output_filename="encrypted_password.bin"):
    with open(output_filename, 'wb') as file:
        file.write(pyaes.AESModeOfOperationCTR(encryption_key).encrypt(password.encode()))
    print(f"Password encrypted and saved to '{output_filename}'")

def decrypt_and_show_password(encryption_key, input_filename="encrypted_password.bin"):
    if not os.path.exists(input_filename):
        print(f"No encrypted file found at '{input_filename}'")
        return
    with open(input_filename, 'rb') as file:
        decrypted_password = pyaes.AESModeOfOperationCTR(encryption_key).decrypt(file.read())
    print("Decrypted password\n" + decrypted_password.decode())

def main_menu():
    password_characters = []
    user_choice = input(
        'Generate Password, Check Password Strength, or Decrypt Password File?\n'
        '1. Generate Password\n2. Check Password Strength\n3. Decrypt Password File\n'
    )
    if user_choice == "1":
        print(SEPARATOR_LINE)
        password_option = input(
            'What kind of password would you like?\n'
            '1. Easy (Easy to remember, but weak)\n'
            '2. Complex (Secure, but not as easy to remember)\n'
            '3. Random (Very Secure, but very difficult to remember)\n'
            '4. Custom\n'
        )
        success, password_characters = generate_password(password_option, password_characters)
        if success:
            print(SEPARATOR_LINE)
            if input("Would you like to encrypt and save this password to a file? (y/n): ").lower() == 'y':
                encryption_key = generate_encryption_key()
                encrypt_and_save_password("".join(map(str, password_characters)), encryption_key)
                print(SEPARATOR_LINE + "\nSave this encryption key safely. You will need it to decrypt your password:\n" + encryption_key.hex())
    elif user_choice == "2":
        print(SEPARATOR_LINE)
        password_input = input('Password:\n')
        if len(password_input) < 100:
            check_password_strength(password_input)
        else:
            print("Too long, please try again.\n" + SEPARATOR_LINE)
            main_menu()
    elif user_choice == "3":
        print(SEPARATOR_LINE)
        try:
            decrypt_and_show_password(bytes.fromhex(input("Enter your encryption key (hex format):\n")))
        except:
            print("Invalid key format. Make sure you enter the key in hex.")
    else:
        print("Incorrect, please try again\n" + SEPARATOR_LINE)
        main_menu()

def generate_password(password_option, password_characters):
    password_characters.clear()
    success = True
    if password_option == '3':
        for _ in range(random.randint(18, 24)):
            char_type = random.choice(('digit', 'lowercase', 'uppercase', 'special'))
            password_characters.append(
                random.randint(1, 9) if char_type == 'digit' else
                random.choice(LOWERCASE_LETTERS) if char_type == 'lowercase' else
                random.choice(UPPERCASE_LETTERS) if char_type == 'uppercase' else
                random.choice(SPECIAL_CHARACTERS)
            )
    elif password_option == '1':
        password_characters += [random.choice(WORD_LIST), str(random.randint(0, 9)), str(random.randint(0, 9))]
    elif password_option == '2':
        for _ in range(3):
            password_characters += [
                random.randint(1, 9) if (char_type := random.choice(('digit', 'lower', 'upper'))) == 'digit' else
                random.choice(LOWERCASE_LETTERS) if char_type == 'lower' else
                random.choice(UPPERCASE_LETTERS)
                for _ in range(6)
            ]
            password_characters.append('-')
        password_characters.pop()
    elif password_option == '4':
        password_length = int(input('Length of Password:\n'))
        char_types = []
        if input('Would you like lowercase letters? (y or n):\n') == "y":
            char_types.append('lowercase')
        if input('Would you like uppercase letters? (Y or n):\n') == "y":
            char_types.append('uppercase')
        if input('Would you like numbers? (y or n):\n') == "y":
            char_types.append('digit')
        if input('Would you like special characters? (y or n):\n') == "y":
            char_types.append('special')
        for _ in range(password_length):
            char_type = random.choice(char_types)
            password_characters.append(
                random.randint(1, 9) if char_type == 'digit' else
                random.choice(LOWERCASE_LETTERS) if char_type == 'lowercase' else
                random.choice(UPPERCASE_LETTERS) if char_type == 'uppercase' else
                random.choice(SPECIAL_CHARACTERS)
            )
    else:
        print("Incorrect, please try again\n" + SEPARATOR_LINE)
        success = False
        main_menu()
    if success:
        print(SEPARATOR_LINE + "\nHere is your Password:")
        print(*password_characters, sep='')
    return success, password_characters

def check_password_strength(password):
    print(SEPARATOR_LINE)
    has_lowercase = has_uppercase = has_special = has_digit = False
    score = charset_size = 0
    for char in password:
        if not has_lowercase and char in LOWERCASE_LETTERS:
            has_lowercase, score, charset_size = True, score + 1, charset_size + len(LOWERCASE_LETTERS)
        if not has_uppercase and char in UPPERCASE_LETTERS:
            has_uppercase, score, charset_size = True, score + 1, charset_size + len(UPPERCASE_LETTERS)
        if not has_special and char in SPECIAL_CHARACTERS:
            has_special, score, charset_size = True, score + 1, charset_size + len(SPECIAL_CHARACTERS)
        if not has_digit and char in DIGIT_CHARACTERS:
            has_digit, score, charset_size = True, score + 1, charset_size + len(DIGIT_CHARACTERS)
    score += 1 if len(password) >= 8 else 2
    print([
        "Error",
        "Password Security = Very Weak",
        "Password Security = Weak",
        "Password Security = Ok",
        "Password Security = Secure",
        "Password Security = Very Secure"
    ][min(score, 5)])
    if score < 5:
        print("Suggestions to improve your password:")
        if not has_lowercase:
            print("- Add some lowercase letters.")
        if not has_uppercase:
            print("- Add some uppercase letters.")
        if not has_digit:
            print("- Add some numbers.")
        if not has_special:
            print("- Add some special characters.")
        if len(password) < 12:
            print("- Make your password 12 characters long.")
    print(SEPARATOR_LINE + "\nBrute-force attack estimation:")
    guesses_per_second = 1_630_000_000_000_000
    total_combinations = math.pow(charset_size, len(password)) if charset_size else 0
    print(format_time(total_combinations / guesses_per_second if total_combinations else 0))

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f} minutes"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.2f} hours"
    days = hours / 24
    if days < 365:
        return f"{days:.2f} days"
    return f"{days / 365:.2f} years"

main_menu()
