import onnxruntime_genai as og
import os

def main():
    # 모델 경로 (변환된 ONNX 모델이 있는 폴더)
    model_path = os.path.abspath("./onnx-model-1b")
    
    # 모델이 없으면 변환 안내
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        print("Please run './convert_genai.sh' first.")
        return

    print(f"Loading model from {model_path}...")
    try:
        # Change to model directory to avoid path issues with tokenizer config
        original_cwd = os.getcwd()
        os.chdir(model_path)
        model = og.Model(".")
        tokenizer = og.Tokenizer(model)
        os.chdir(original_cwd)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    print("\nModel loaded! Type 'exit' or 'quit' to stop.\n")

    while True:
        prompt = input("User: ")
        if prompt.lower() in ["exit", "quit"]:
            break

        # 프롬프트 포맷팅 (Gemma Chat Template)
        # <start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n
        formatted_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        tokens = tokenizer.encode(formatted_prompt)

        params = og.GeneratorParams(model)
        # repetition_penalty: 무한 반복 방지
        params.set_search_options(max_length=1024, repetition_penalty=1.2)
        
        generator = og.Generator(model, params)
        generator.append_tokens(tokens)

        print("AI: ", end='', flush=True)
        
        while not generator.is_done():
            generator.generate_next_token()
            new_token = generator.get_next_tokens()[0]
            print(tokenizer.decode(new_token), end='', flush=True)

        print("\n")

    print("Bye!")

if __name__ == "__main__":
    main()
