import os
import subprocess
import sys

def run_command(command):
    print(f"Running: {command}")
    subprocess.check_call(command, shell=True)

def main():
    # 1. Clone llama.cpp
    if not os.path.exists("llama.cpp"):
        print("Cloning llama.cpp...")
        run_command("git clone https://github.com/ggml-org/llama.cpp")
    
    # 2. Build llama.cpp
    print("Building llama.cpp...")
    os.chdir("llama.cpp")
    run_command("cmake -B build")
    run_command("cmake --build build --config Release")
    
    # 3. Install Python dependencies for conversion
    print("Installing dependencies...")
    run_command("pip install -r requirements.txt")
    
    # 4. Convert Model to GGUF
    # 모델 경로: 상위 디렉토리에 있는 gemma-3-4b-it을 가정
    model_path = os.path.abspath("../../gemma-3-4b-it")
    output_path = os.path.abspath("../gemma-3-4b-it.gguf")
    
    if os.path.exists(model_path):
        print(f"Converting model from {model_path}...")
        run_command(f"python convert_hf_to_gguf.py {model_path} --outfile {output_path}")
        print(f"Conversion complete: {output_path}")
    else:
        print(f"Model not found at {model_path}. Please download the model first.")

if __name__ == "__main__":
    main()
