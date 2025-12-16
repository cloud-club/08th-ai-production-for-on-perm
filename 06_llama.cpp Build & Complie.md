
- [llama.cpp Docs | how to build](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md)
	- [CUDA](https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md#cuda)

### install to build
```bash
$ apt-get install -y cmake
$ apt-get install libcurl4-openssl-dev
```

### Override Compute Capability Specifications
1. 사용하는 NVIDIA GPU의 Compute Compability 를 메모한다. GPU 별 Compability는 다음의 NVIDIA 공식 문서에서 확인 가능
	1. https://developer.nvidia.com/cuda-gpus
	2. GeForce RTX 3060 Ti  : 8.6
2. build 시 해당 compability를 명시하여 build 함으로써 이슈 예방 가능
3. e.g.
```bash
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86"
```

### Overriding the CUDA Version
1. 시스템에 여러 버전의 cuda 가 설치돼있고, llama.cpp 를 해당 버전에 맞게 컴파일하기를 원한다면,
   빌드 옵션에 `CMAKE_CUDA_COMPILEER` 을 명시한다.
```bash
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/opt/cuda-11.7/bin/nvcc -DCMAKE_INSTALL_RPATH="/opt/cuda-11.7/lib64;\$ORIGIN" -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON
```

## 1. llama.cpp build
### 1.1 build 디렉터리 생성
- 현재 환경에는 cuda-13.0으로 1개만 설치돼있다.
- 다음 명령으로 빌드 디렉터리 생성
```bash
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86"
```

### 1.2 컴파일
```bash
cmake --build build --config Release
```
