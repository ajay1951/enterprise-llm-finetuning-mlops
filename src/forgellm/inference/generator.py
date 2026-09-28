import torch
from transformers import PreTrainedModel, PreTrainedTokenizer


class ForgeGenerator:
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer):
        self.model = model
        self.tokenizer = tokenizer
        self.device = model.device

    def chat_loop(self):
        print("ForgeLLM Chat")
        print("────────────────────────")
        print("Type 'exit' to quit.\n")
        
        while True:
            try:
                user_input = input("You: ")
                if user_input.strip().lower() in ["exit", "quit"]:
                    break
                
                messages = [{"role": "user", "content": user_input}]
                
                try:
                    prompt = self.tokenizer.apply_chat_template(
                        messages, tokenize=False, add_generation_prompt=True
                    )
                except Exception:
                    prompt = f"User: {user_input}\nAssistant:"
                    
                from transformers import TextStreamer
                
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
                
                # Stream the output in real-time
                streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
                
                # Handle special stop tokens for models like Qwen which use <|im_end|>
                stop_token_ids = [self.tokenizer.eos_token_id]
                if "<|im_end|>" in self.tokenizer.vocab:
                    stop_token_ids.append(self.tokenizer.convert_tokens_to_ids("<|im_end|>"))
                
                print("\nAssistant: ", end="", flush=True)
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs, 
                        max_new_tokens=150,  # Lowered so it doesn't rant forever
                        temperature=0.7,
                        top_p=0.9,
                        repetition_penalty=1.2, # Punish the model for repeating the same words!
                        do_sample=True,
                        pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                        eos_token_id=stop_token_ids,
                        streamer=streamer
                    )
                print("\n")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
