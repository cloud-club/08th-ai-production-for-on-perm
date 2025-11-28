# Week 4

## 이번주 목표

1. huggingface 가입 및 ssh key 등록

- 계정 생성 후 ssh key 등록 완료

2. gemma3-1b 또는 4b it qat gguf 모델 git clone (ssh) (git-lfs, git-xet 설치 필요)

```bash
# 사전에 hugging face 홈페이지에서 무슨 동의가 있어야 함
git clone git@hf.co:google/gemma-3-1b-it
```

3. llama.cpp 본인 런타임에 맞게 직접 빌드해보기 (패키지 가져오는 거 x 직접 빌드해야함)

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release


```

4. llama.cpp로 gguf 모델 구동

- python 3.11 버전 아래로 설치하는 것을 권장
- 3.14로 했더니 안되서 하나씩 내려보니 3.11에서 잘됨
- llama.cpp의 경우 4b 모델도 잘 실행되며, 별도의 자원 제한 없이 OOM 발생하지 않은 상태로 빌드, 실행이 가능

```bash
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python convert_hf_to_gguf.py ../gemma-3-4b-it --outfile models/gemma-3-4b-it.gguf
./build/bin/llama-cli -m models/gemma-3-4b-it.gguf -cnv -ngl 99
```

![alt text](image.png)

5. (정확히 맞는지 모르겠음) onnx로 gemma3-1b 또는 4b it (unquantized도 될 것 같이 보임) onnx 변환 후 onnx 런타임에 모델 구동

- onnx의 경우 gemma3를 onnx에서 실행가능하도록 변환시에 오류가 발생
- onnx의 변환 라이브러리가 gemma3에서 지원하지 않아서 발생하는 문제로 추정

```
ValueError: Trying to export a gemma3_text model, that is a custom or unsupported architecture, but no custom onnx configuration was passed as `custom_onnx_configs`.
```

- onnx genai 프로젝트를 사용해서 LLM 구동 진행
- onnx gen ai를 사용하여 gemma3-4B으로 실행하였는데, OOM이 발생하여 1B으로 변경
- onnx gen ai의 경우 onnx runtime과 달리, 내장 Tokenizer를 사용하는 생성형 AI를 위해 MS에서 만든 런타임임, 외장 Tokenizer를 사용하는 ONNX하고는 다름

**onnx gen ai**

```bash
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv venv
source venv/bin/activate
./venv/bin/pip install onnxruntime-genai
OMP_NUM_THREADS=8 python -m onnxruntime_genai.models.builder -m ../gemma-3-1b-it -o ./onnx-model-1b -p int4 -e cpu --extra_options exclude_embeds=0
```

6. 마크다운 요약

이번주 진행한 것

1. huggingface에서 gemma3 모델을 SafeTensors형식으로 다운로드
2. llama.cpp를 직접 빌드하여 런타임 환경에서 실행
3. SafeTensors 타입을 llama.cpp에서 실행하기 위한 GGUF 형식으로 변경 후 GGUF 파일을 llama.cpp로 실행
4. SafeTensors 타입을 onnx 포맷으로 변경해서 onnx runtime에서 실행하는 것 => gemma3가 onnx 빌드를 지원하지 않아, onnx-genai를 사용하여 빌드 및 런타임을 사용하여 실행

### 모델 형식 별 차이점 잘 정리해둔 블로그

https://huggingface.co/blog/ngxson/common-ai-model-formats
