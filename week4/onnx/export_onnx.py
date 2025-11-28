import os
import subprocess
import sys

def main():
    # Gemma 2 2B 모델 (Standard ONNX는 Gemma 3 미지원)
    # 로컬에 다운로드된 모델이 있다면 경로를 지정, 없으면 HF Hub ID 사용
    model_id = "google/gemma-2-2b-it" 
    output_dir = "./onnx-model-gemma2"
    
    print(f"Exporting {model_id} to ONNX using Optimum...")
    print("Note: This uses Standard ONNX (Optimum), not GenAI.")
    
    # Optimum CLI 명령어 실행
    # 필요한 패키지: pip install optimum[onnxruntime]
    cmd = [
        "optimum-cli", "export", "onnx",
        "--model", model_id,
        output_dir,
        "--task", "text-generation-with-past"
    ]
    
    try:
        subprocess.check_call(cmd)
        print(f"Export complete! Model saved to {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Export failed: {e}")
        print("Ensure you have 'optimum' and 'onnxruntime' installed.")

if __name__ == "__main__":
    main()
