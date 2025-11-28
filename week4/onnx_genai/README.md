# ONNX Runtime GenAI 실행 가이드

이 디렉토리는 Microsoft의 **ONNX Runtime GenAI**를 사용하여 LLM을 최적화된 방식으로 실행하는 방법을 설명합니다.
이 방식은 **Gemma 3**와 같은 최신 모델을 지원하며, C++ 기반의 최적화된 루프를 사용하여 매우 빠릅니다.

## 1. 사전 준비

```bash
pip install onnxruntime-genai
```

- Hugging Face 모델 (`gemma-3-1b-it`)이 `week4/` 상위 디렉토리에 있어야 함.

## 2. 모델 변환 (`convert_genai.sh`)

`onnxruntime_genai.models.builder`를 사용하여 모델을 `int4`로 양자화하고 변환합니다.

```bash
chmod +x convert_genai.sh
./convert_genai.sh
```

### 주요 설정

- `-p int4`: 4비트 정수 양자화 (메모리 절약, 속도 향상)
- `-e cpu`: CPU 실행 모드 (Mac ARM 최적화)
- `--extra_options exclude_embeds=0`: 텍스트 입력을 받기 위해 필수 (Gemma 3 멀티모달 특성 대응)

## 3. 실행 (`run_genai.py`)

변환된 모델을 로드하여 실시간 대화를 수행합니다.

```bash
python run_genai.py
```

### 특징

- **속도**: Standard ONNX보다 훨씬 빠름.
- **메모리**: `int4` 적용으로 매우 가벼움 (1B 모델 기준 약 1GB 내외).
- **기능**: `repetition_penalty` 등이 적용되어 자연스러운 대화 가능.
