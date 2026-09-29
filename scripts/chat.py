import argparse
import os
import sys

from peft import PeftModel

from forgellm.inference.generator import ForgeGenerator
from forgellm.models.loader import ModelLoader


def main():
    parser = argparse.ArgumentParser(description="ForgeLLM Chat Interface")
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to output dir containing adapter and config, or HF model id",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default="Qwen/Qwen2.5-0.5B",
        help="Base model ID if loading an adapter",
    )
    args = parser.parse_args()

    print("Loading model...")
    loader = ModelLoader(args.base_model)
    tokenizer = loader.load_tokenizer()

    # Apply 4-bit quantization to ensure fast inference on low VRAM GPUs
    import torch
    from transformers import BitsAndBytesConfig

    q_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=False,
    )
    model = loader.load_model(quantization_config=q_config)

    # If the provided model path is a directory and has adapter config, load PEFT
    if os.path.exists(args.model) and os.path.exists(
        os.path.join(args.model, "adapter_config.json")
    ):
        print(f"Loading LoRA adapter from {args.model}")
        model = PeftModel.from_pretrained(model, args.model)
    elif os.path.exists(os.path.join(args.model, "adapter", "adapter_config.json")):
        adapter_path = os.path.join(args.model, "adapter")
        print(f"Loading LoRA adapter from {adapter_path}")
        model = PeftModel.from_pretrained(model, adapter_path)
    else:
        # User might have passed a base model directly
        print(f"Running raw model: {args.base_model}")

    generator = ForgeGenerator(model, tokenizer)
    generator.chat_loop()


if __name__ == "__main__":
    main()
