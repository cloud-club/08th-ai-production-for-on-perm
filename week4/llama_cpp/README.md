# llama.cpp 실행 가이드

이 디렉토리는 `llama.cpp`를 사용하여 GGUF 모델을 빌드하고 실행하는 방법을 설명합니다.

## 1. 사전 준비

- Python 3.11 권장
- `cmake` 설치 필요 (`brew install cmake`)
- Hugging Face 모델 (`gemma-3-4b-it`)이 `week4/` 상위 디렉토리에 있어야 함

## 2. 빌드 및 변환 (`build_gguf.py`)

이 스크립트는 다음 작업을 수행합니다:

1. `llama.cpp` 리포지토리 클론
2. `cmake`를 사용한 빌드 (Metal GPU 가속 포함)
3. Python 의존성 설치
4. HF 모델을 GGUF 포맷으로 변환

```bash
python build_gguf.py
```

## 3. 실행 (`run_gguf.sh`)

변환된 GGUF 모델을 로드하여 대화형 인터페이스를 실행합니다.

```bash
chmod +x run_gguf.sh
./run_gguf.sh
```

### 주요 옵션 설명

- `-ngl 99`: 모든 레이어를 GPU(Metal)에 오프로드 (최대 성능)
- `-c 4096`: 컨텍스트 길이 설정
- `-cnv`: 대화 모드 (Conversation Mode)
