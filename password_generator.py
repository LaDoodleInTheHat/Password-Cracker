import random, string, pyaes, os, math

L, U, N, S = list(string.ascii_lowercase), list(string.ascii_uppercase), list(string.digits), list("!@#$%^&*()-_=+[{]};:'\",<.>/?\\|`~")
W, LB = [], "-"*72
with open('words') as f: W = [l.strip() for l in f]

def gen_key(l=16): return os.urandom(l)
def encrypt(p, k, fn="encrypted_password.bin"):
    with open(fn, 'wb') as f: f.write(pyaes.AESModeOfOperationCTR(k).encrypt(p.encode()))
    print(f"Password encrypted and saved to '{fn}'")
def decrypt(k, fn="encrypted_password.bin"):
    if not os.path.exists(fn): print(f"No encrypted file found at '{fn}'"); return
    with open(fn, 'rb') as f: d = pyaes.AESModeOfOperationCTR(k).decrypt(f.read())
    print("Decrypted password\n"+d.decode())

def activate():
    p = []
    c = input('Generate Password, Check Password Strength, or Decrypt Password File?\n1. Generate Password\n2. Check Password Strength\n3. Decrypt Password File\n')
    if c == "1":
        print(LB)
        t = input('What kind of password would you like?\n1. Easy (Easy to remember, but weak)\n2. Complex (Secure, but not as easy to remember)\n3. Random (Very Secure, but very difficult to remember)\n4. Custom\n')
        f, p = gen_pass(t, p)
        if f:
            print(LB)
            if input("Would you like to encrypt and save this password to a file? (y/n): ").lower() == 'y':
                k = gen_key()
                encrypt("".join(map(str, p)), k)
                print(LB+"\nSave this encryption key safely. You will need it to decrypt your password:\n"+k.hex())
    elif c == "2":
        print(LB)
        pw = input('Password:\n')
        if len(pw) < 100: check_pass(pw)
        else: print("Too long, please try again.\n"+LB); activate()
    elif c == "3":
        print(LB)
        try: decrypt(bytes.fromhex(input("Enter your encryption key (hex format):\n")))
        except: print("Invalid key format. Make sure you enter the key in hex.")
    else: print("Incorrect, please try again\n"+LB); activate()

def gen_pass(t, p):
    p.clear(); f = True
    if t == '3':
        for _ in range(random.randint(18,24)):
            c = random.choice(('num','lowercase','uppercase','special'))
            p.append(random.randint(1,9) if c=='num' else random.choice(eval(c[0].upper())))
    elif t == '1': p += [random.choice(W),str(random.randint(0,9)),str(random.randint(0,9))]
    elif t == '2':
        for _ in range(3):
            for _ in range(6):
                c = random.choice(('num','letter','capital'))
                p.append(random.randint(1,9) if c=='num' else random.choice(L if c=='letter' else U))
            p.append('-')
        p.pop()
    elif t == '4':
        l = int(input('Length of Password:\n'))
        props = []
        if input('Would you like lowercase letters? (y or n):\n')=="y": props.append('lowercase')
        if input('Would you like uppercase letters? (Y or n):\n')=="y": props.append('uppercase')
        if input('Would you like numbers? (y or n):\n')=="y": props.append('num')
        if input('Would you like special characters? (y or n):\n')=="y": props.append('special')
        for _ in range(l):
            c = random.choice(props)
            p.append(random.randint(1,9) if c=='num' else random.choice(eval(c[0].upper())))
    else: print("Incorrect, please try again\n"+LB); f = False; activate()
    if f: print(LB+"\nHere is your Password:"); print(*p,sep='')
    return f, p

def check_pass(pw):
    print(LB)
    l, u, s, n, sc, cs = False, False, False, False, 0, 0
    for c in pw:
        if not l and c in L: l, sc, cs = True, sc+1, cs+len(L)
        if not u and c in U: u, sc, cs = True, sc+1, cs+len(U)
        if not s and c in S: s, sc, cs = True, sc+1, cs+len(S)
        if not n and c in N: n, sc, cs = True, sc+1, cs+len(N)
    sc += 1 if len(pw)>=8 else 2
    print(["Error","Password Security = Very Weak","Password Security = Weak","Password Security = Ok","Password Security = Secure","Password Security = Very Secure"][min(sc,5)])
    if sc<5:
        print("Suggestions to improve your password:")
        if not l: print("- Add some lowercase letters.")
        if not u: print("- Add some uppercase letters.")
        if not n: print("- Add some numbers.")
        if not s: print("- Add some special characters.")
        if len(pw)<12: print("- Make your password 12 characters long.")
    print(LB+"\nBrute-force attack estimation:")
    g = 1_630_000_000_000_000
    tc = math.pow(cs,len(pw)) if cs else 0
    print(fmt_time(tc/g if tc else 0))

def fmt_time(s):
    if s<60: return f"{s:.2f} seconds"
    m=s/60
    if m<60: return f"{m:.2f} minutes"
    h=m/60
    if h<24: return f"{h:.2f} hours"
    d=h/24
    if d<365: return f"{d:.2f} days"
    return f"{d/365:.2f} years"

activate()
