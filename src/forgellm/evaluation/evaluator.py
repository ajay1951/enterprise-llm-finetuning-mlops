import os
import json
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

class ForgeEvaluator:
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.device = model.device

    def generate_response(self, prompt: str, max_new_tokens: int = 256) -> str:
        messages = [{"role": "user", "content": prompt}]
        
        # Apply chat template if available
        try:
            prompt_formatted = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            prompt_formatted = f"User: {prompt}\nAssistant:"

        inputs = self.tokenizer(prompt_formatted, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=max_new_tokens,
                temperature=0.0, # Greedy for reproducibility
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
        generated_text = self.tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return generated_text.strip()
        
    def evaluate_test_set(self, test_file: str, output_path: str):
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"Test file not found: {test_file}")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        results = []
        
        with open(test_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # Find user prompt
                    prompt = next(msg["content"] for msg in record["messages"] if msg["role"] == "user")
                    expected = next((msg["content"] for msg in record["messages"] if msg["role"] == "assistant"), "")
                    
                    response = self.generate_response(prompt)
                    results.append({
                        "prompt": prompt,
                        "expected": expected,
                        "generated": response
                    })
                except Exception as e:
                    print(f"Skipping malformed test line: {e}")
                    
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        return results
