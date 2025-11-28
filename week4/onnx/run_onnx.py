from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer
import os

def main():
    model_dir = "./onnx-model-gemma2"
    
    if not os.path.exists(model_dir):
        print(f"Error: Model directory '{model_dir}' not found.")
        print("Please run 'python export_onnx.py' first.")
        return

    print(f"Loading model from {model_dir} using Optimum ORT...")
    
    # Optimum의 ORTModelForCausalLM을 사용하여 ONNX 모델 로드
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = ORTModelForCausalLM.from_pretrained(model_dir)

    print("Model loaded successfully.")
    
    while True:
        prompt = input("\nUser: ")
        if prompt.lower() in ["exit", "quit"]:
            break
            
        inputs = tokenizer(prompt, return_tensors="pt")

        print("AI: ", end="", flush=True)
        gen_tokens = model.generate(**inputs, max_new_tokens=100)
        
        # 입력 프롬프트 제외하고 출력
        output = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]
        print(output[len(prompt):])

if __name__ == "__main__":
    main()
