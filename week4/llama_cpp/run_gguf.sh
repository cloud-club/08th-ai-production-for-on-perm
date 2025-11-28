#!/bin/bash

# 실행 파일 경로
CLI_PATH="./llama.cpp/build/bin/llama-cli"
MODEL_PATH="./gemma-3-4b-it.gguf"

# 실행 파일 확인
if [ ! -f "$CLI_PATH" ]; then
    echo "Error: llama-cli not found. Please run 'python build_gguf.py' first."
    exit 1
fi

# 모델 파일 확인
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file not found at $MODEL_PATH."
    exit 1
fi

echo "Starting llama.cpp with Gemma 3..."
echo "Options: -ngl 99 (GPU Offload), -c 4096 (Context), -cnv (Chat Mode)"

# 실행
$CLI_PATH -m $MODEL_PATH -cnv -ngl 99 -c 4096 --temp 0.7
