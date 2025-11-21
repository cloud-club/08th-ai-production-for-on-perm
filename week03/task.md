## 간단 실습 
--- 
### 1. GCP에서 VM 인스턴스 생성
- N2 4코어 32GB (토론토 리전)
### 2. Ollama 설치
``` bash
g7910trio@model-server:~$ curl -fsSL https://ollama.com/install.sh | sh
>>> Installing ollama to /usr/local
>>> Downloading Linux amd64 bundle
######################################################################## 100.0%
>>> Creating ollama user...
>>> Adding ollama user to render group...
>>> Adding ollama user to video group...
>>> Adding current user to ollama group...
>>> Creating ollama systemd service...
>>> Enabling and starting ollama service...
Created symlink /etc/systemd/system/default.target.wants/ollama.service → /etc/systemd/system/ollama.service.
>>> The Ollama API is now available at 127.0.0.1:11434.
>>> Install complete. Run "ollama" from the command line.
WARNING: No NVIDIA/AMD GPU detected. Ollama will run in CPU-only mode.
g7910trio@model-server:~$ ollama --version
ollama version is 0.13.0
```

### 3. 모델 다운로드
- Ollama가 지원하는 SLM 모델 파일을 선택해서 다운로드 + 로컬 저장 → Ollama에 모델 설치됨
```
ollama pull phi3:mini
ollama list
```

### 4. 모델 실행
- 모델 로딩해서 추론 수행
    - 모델 로딩 → 프롬프트 전처리(이전 대화 컨텍스트 연결) → 토크나이징 → 추론(입력 토큰 받아 한 토큰씩 생성) → 디토크나이징 & 스트리밍(디코드해서 문자로 변환하는 동시에 클라이언트에 전송하여 실시간으로 읽히게 함)
``` bash
g7910trio@model-server:~$ ollama run phi3:mini "Explain how to make curry in a simple way"
Making delicious and easy-toinspired Curry:

Ingredients you'll need:
* Oil or cooking spray
* Onion, finely diced (1 large onion)
...
```