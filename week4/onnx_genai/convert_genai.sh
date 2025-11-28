#!/bin/bash

# 모델 경로 (상위 디렉토리에 있다고 가정)
MODEL_PATH="../../gemma-3-1b-it"
OUTPUT_PATH="./onnx-model-1b"

echo "Converting Gemma 3 (1B) to ONNX GenAI format..."
echo "Settings: int4 quantization, CPU execution, exclude_embeds=0 (Text Mode)"

# OOM 방지를 위한 설정
export OMP_NUM_THREADS=4

# 변환 실행
# exclude_embeds=0: 텍스트 입력을 받기 위해 임베딩 레이어 포함 (필수)
python -m onnxruntime_genai.models.builder \
    -m $MODEL_PATH \
    -o $OUTPUT_PATH \
    -p int4 \
    -e cpu \
    --extra_options exclude_embeds=0

echo "Conversion complete!"
