
## 1. ollam install
```bash
$ mkdir ollam && cd ollama
$ curl -fsSL https://ollama.com/install.sh | sh

# output
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
>>> NVIDIA GPU installed
```

```bash
$ systemctl enable --now ollama
```

- ollama가 gpu를 인식했는지 확인
```bash
$ journalctl -u ollama -b | grep -i nvidia
Nov 22 08:10:47 gpu-inference-vm ollama[29140]: time=2025-11-22T08:10:47.760+09:00 level=INFO source=types.go:42 msg="inference compute" id=GPU-5b419f64-406d-db30-3dbc-1ef4ac4d891a filter_id="" library=CUDA compute=8.6 name=CUDA0 description="NVIDIA GeForce RTX 3060 Ti" libdirs=ollama,cuda_v12 driver=13.0 pci_id=0000:01:00.0 type=discrete total="8.0 GiB" available="7.6 GiB"
```

## 2. run model 
- [모델 성능 벤치마크 사이트](https://artificialanalysis.ai/leaderboards/models?size_class=tiny)
	- [스몰 모델 (4B ~ 40B)](https://artificialanalysis.ai/models/open-source/small)
	- [Tiny Model (<= 4B)](https://artificialanalysis.ai/models/open-source/tiny)

### 2-1. Phi-3.5 Mini
- 대중적인 엣지 디바이스용 모델
```bash
$ ollama run phi3.5
```

### 2-2. Qwen 3 4B 2507
 - 고성능 범용
```bash
$ ollama run qwen3:4b-thinking
```

### 2-3. Deepseek
#### 1) DeepSeek-R1 8B
```bash
$ ollama run deepseek-r1:8b
```

#### 2) DeepSeek-R1 1.5B
- 초경량 엣지 테스트
```bash
$ ollama run deepseek-r1:1.5b
```


## 3. Model 테스트
1. "strawberry"라는 단어에 'r'이 몇 개 들어있는지 논리적으로 설명하고 답을 말해줘.
2. 파이썬으로 퀵 정렬(Quick Sort)을 구현하는 코드를 작성하고, 각 라인을 한글로 주석 달아서 설명해줘.
	1. 코딩 문제의 경우, 
		1. 파라미터가 작은 모델(deepseek-r1:1.5b)은 GPU Mem 사용률이 높지 않지만, 결과 출력가지는 시간이 오래 걸린다. 하지만 속도는 확실히 빠르다.
		2. deepseek-r1:8b 같은 모델들은 추론에 걸리는 시간이 짧은 것인지, 결과 도출 속도도 빠르고, 출력 포멧까지 깔끔했다. GPU Mem 사용량도 95% 이상을 사용할 정도로 높았다.