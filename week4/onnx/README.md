# Standard ONNX (Optimum) 실행 가이드

이 디렉토리는 `Hugging Face Optimum`을 사용하여 모델을 표준 ONNX 포맷으로 변환하고 실행하는 방법을 설명합니다.

## 1. 사전 준비

```bash
pip install optimum[onnxruntime] transformers
```

## 2. 모델 변환 (`export_onnx.py`)

`optimum-cli`를 사용하여 PyTorch 모델을 ONNX로 변환합니다.

- **주의**: Gemma 3는 아직 Optimum에서 지원하지 않아 변환이 불가능합니다.
- 이 예제에서는 **Gemma 2 (2B)** 모델을 사용합니다.

```bash
python export_onnx.py
```

## 3. 실행 (`run_onnx.py`)

`ORTModelForCausalLM` 클래스를 사용하여 변환된 ONNX 모델을 로드하고 추론합니다.
이 방식은 Python 런타임을 사용하므로 `ONNX Runtime GenAI` 방식보다 속도가 느릴 수 있습니다.

```bash
python run_onnx.py
```
