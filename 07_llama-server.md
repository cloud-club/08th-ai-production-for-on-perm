

## 1. 서버 실행하기

### 모델별 최적 컨텍스트 길이 확인
1. huggingFace 등에서 모델 설명란 확인
2. `llama-cli`로 체크
```bash
./llama.cpp/build/bin/llama-cli -m model.gguf -ngl 0 --verbose 2>&1 | grep -E "context_length|n_ctx|n_layer"
```

#### 일반적인 컨텍스트 길이
```bash
# 일반 대화
-c 8192

# 긴 문서 처리
-c 32768

# 최대 성능 (메모리 충분한 경우)
-c 131072
```


### `llama-server` 실행
```bash
./build/bin/llama-server \
  -m model.gguf \
  -c 4096 \
  -ngl -1 \
  --host 0.0.0.0 \
  --port 8080
```

**주요 옵션 설명:**
- `-m`: GGUF 모델 파일 경로
- `-c`: 컨텍스트 크기 (토큰 수)
	- 실행 시 명시 안하면 기본값으로 4069이 들어가는 것 같다.
- `-ngl`: GPU에 로드할 레이어 수 (숫자가 클수록 더 많이 GPU 사용, -1은 전체)
- `--host`: 서버 바인딩 주소 (0.0.0.0은 외부 접근 허용)
- `--port`: 서버 포트