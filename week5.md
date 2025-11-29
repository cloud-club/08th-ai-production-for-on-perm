## What I did

1. Install git-lfs
2. Install git-xet
3. Build llama.cpp
	- Install missed packages
	- `CMakeLists.txt #L12` (Build Variants)
	- CPU
		- `cmake -Bbuild`
		- `cmake --build build --config Release`
	- GPU
		- `cmake -Bbuild -DGGML_CUDA=ON`
		- `cmake --build build --config Release`
4. apt install {nvidia-cuda-toolkit, libcurl4-openssl-dev}
5. unavailable `nvidia-smi` on jetson-orin-nano
	- `sudo tegrastats` instead
6. llama.cpp cli flags
	- https://github.com/ggml-org/llama.cpp/blob/master/tools/main/README.md
7. Installed jtop
	- https://github.com/rbonghi/jetson_stats
8. Used [uv](https://docs.astral.sh/uv/) for managing venv and dependencies effectively
9. [optimum-cli](https://github.com/huggingface/optimum)
	- `uv add optimum[onnx]`
	- issues for gemma3 support
		- https://github.com/huggingface/optimum-onnx/pull/70
10. onnxruntime
	- https://onnxruntime.ai/getting-started
	- https://onnxruntime.ai/docs/tutorials/iot-edge/
	- compatibility
		- https://onnxruntime.ai/docs/reference/compatibility.html

