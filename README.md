# Password Cracker 🔓

A high-performance brute-force password cracking simulation tool for educational and benchmarking purposes. Supports both CPU (parallelized using multiprocessing) and GPU (via CUDA/CuPy) acceleration. Real-time progress, speed, and logging are provided for both backends.

---

## Features ✨

- **Brute-Force Cracking**: Tries all possible combinations for a given password using a customizable charset. 🔍
- **CPU Mode**: Utilizes all available CPU cores with Python multiprocessing for fast cracking. 🖥️
- **GPU Mode**: Leverages CUDA-capable GPUs using [CuPy](https://cupy.dev/) for massive parallelism and superior speed (NVIDIA GPUs required). ⚡
- **Dynamic Batch Sizing**: GPU mode automatically adapts batch sizes based on available GPU memory. 📦
- **Real-Time Feedback**: Colorful, live progress bars and speed reporting. 📊
- **Auto Charset Detection**: Detects required charset based on the target password, or customize as needed. 🧩
- **Detailed Logging**: Results are logged to `logs/` with all relevant statistics and a copy of the latest run. 📝

---

## Requirements 🛠️

- **Python 3.13.4+** 🐍
- For CPU: No special dependencies (uses standard library).
- For GPU: [CuPy](https://cupy.dev/) with a CUDA-capable NVIDIA GPU and appropriate CUDA drivers. 💻
  - Install CuPy (replace `11x` with your CUDA version):  
    ```
    pip install cupy-cuda11x
    ```
- See [CuPy Installation](https://docs.cupy.dev/en/stable/install.html) if unsure about your CUDA version. ❓

---

## Usage 🚀

### 1. CPU Cracker

```bash
python password_cracker_CPU.py
```

- Enter the password to simulate cracking. 🔑
- The script will auto-detect the charset or you can modify the code to customize it.
- Progress is shown live; results are logged in `logs/`. 📂

### 2. GPU Cracker

```bash
python password_cracker_GPU.py
```

- Enter the password, and (optionally) a custom charset, max length, and batch size. 📝
- Requires a supported NVIDIA GPU and CuPy. 🖥️
- Progress and results are displayed and logged. 📈

### 3. Password Generator

In the folder there is a file called ```password_generator.py``` and this is credited to @Takadoo75

```bash
python password_generator.py
```

- Decrypt and encrypt a password file using hex
- Test password strength
- Generate password

---

## Notes 📝

- **Performance**: GPU mode is vastly faster, especially for longer target passwords and large charsets. ⚡
- **Security**: This repository is for educational and benchmarking purposes only—do **not** use for unauthorized access. 🔒
- **Password Length**: Brute-force time grows exponentially. For long passwords or large charsets, even GPU mode can take a very long time. ⏳
- **Logging**: Each successful crack writes a detailed log to `logs/`, including attempts, time, and speed. 📑
- **Finalisation**: The GPU acceleration hasn't been finalised and could be buggy and not finished.
- **Generator**: The Generator calculates time by assuming there is about 1.3 trillion attempts/s
- **C++**: a c plus, plus version is coming!

---

## Disclaimer ⚠️

This tool is intended for legal, ethical, and educational use only. The authors are not responsible for any misuse.  
(oh and btw it isn't practical for any offline attacks either, 🙂 )

---

## Credits

- @MEGA-COOKIE-MONSTER for coding it.
- @Takadoo75 for inspiring me to build it and for the password generator file.

# Have Fun! 🎉 - LaDoodleInTheHat / Takadoo75