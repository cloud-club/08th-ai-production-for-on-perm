### 과제 개요
1. GGUF + llama.cpp
2. ONNX + ONNX 런타임

-> 한 모델을 두 가지 방식으로 돌려보기

## 실습
---
### 1. VM 준비
### 2. HuggingFace 로그인 + SSH Key 등록
``` bash
ssh-keygen 
    
# pubkey 복사해서 HuggingFace에 등록 후 SSH 테스트
ssh -T git@hf.co
```
    
### 3. 모델 돌려보기
``` bash
# git-lfs 설치
sudo apt install git-lfs -y
git lfs install
            
# git-xet 설치
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/huggingface/xet-core/refs/heads/main/git_xet/install.sh | sh
```
    
### 3-1. GGUF + llama.cpp
        
   1. GGUF 모델 clone
      
``` bash
# Gemma3 GGUF 모델 clone
## HF의 Google 레포에서 모델 목록 확인 가능
git clone git@hf.co:google/gemma-3-1b-it-qat-q4_0-gguf

# 안돼서 https로 연결
git clone https://huggingface.co/google/gemma-3-1b-it-qat-q4_0-gguf

```
   
  2. llama.cpp 직접 빌드
``` bash
# llama.cpp clone
https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

# cmake 설치 
sudo apt list --installed | grep cmake
sudo apt install cmake

# c++ 컴파일러 설치 
sudo apt update
sudo apt install g++
    
# libcurl4-openssl-dev 설치
sudo apt list | grep libcurl
sudo apt install libcurl4-openssl-dev

# cmake를 이용해 빌드
## llama.cpp 소스 코드 분석해서 build 디렉터리 생성 후 그 안에 빌드 정보(Makefile) 생성
cmake -B build
## cpu 확인
lscpu | grep "^CPU(s):"
## 방금 생성한 설정을 기반으로 build 디렉터리에 실행 파일 생성 (cpu 4개 사용해서)
cmake --build build --config Release -j4
```


3. llama.cpp로 모델 실행

``` bash
cd build


./bin/llama-cli \
  -m ~/gemma-3-1b-it-qat-q4_0-gguf/gemma-3-1b-it-q4_0.gguf \
  -p "안녕?"

. user
안녕? 
 model
안녕하세요! 무엇을 도와드릴까요? 😊


> 네 이름은 뭐야
저는 Google에서 학습한 대규모 언어 모델입니다. 칭호는 없지만, 여러분의 질문에 답변하거나 정보를 제공하는 데 도움을 드릴 수 있습니다.

> 서울에 첫눈이 언제 올지 예측해줘
서울의 첫눈은 예측하기 어렵지만, 일반적으로 11월 말에서 12월 초에 올 확률이 높아집니다. 

*   **최근 추세:** 최근 몇 년 동안 서울의 첫눈은 점점 늦어지고 있습니다.
*   **예측:** 2024년 12월은 아직 늦었지만, 11월 중순부터 12월 초까지 늦어질 가능성이 있습니다.
*   **예측 기관:** 
    *   **기상청:** 2024년 12월 15일 기상청 예보를 통해 서울의 첫눈을 예측했습니다. 
    *   **기상정보획:** 기상정보획부의 예보 자료를 참고하여 서울의 첫눈 날짜를 예측하고 있습니다.

**참고:** 기상청의 예보는 변경될 수 있으므로, 항상 최신 정보를 확인하는 것이 좋습니다.

더 궁금한 점이 있으시면 언제든지 물어보세요!

```

### 3-2. ONNX + ONNX 런타임
1. 양자화되지 않은 원본 모델을 clone
``` bash
git clone https://huggingface.co/google/gemma-3-1b-it-qat-q4_0-unquantized
```

2. python 환경 준비
3. python 코드로 직접 세션을 만들어 추론 호출