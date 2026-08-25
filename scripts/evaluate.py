import argparse
import sys
import os
import json
from forgellm.training.config import load_config
from forgellm.training.quantization import get_quantization_config
from forgellm.models.loader import ModelLoader
from forgellm.evaluation.evaluator import ForgeEvaluator
from peft import PeftModel

def main():
    parser = argparse.ArgumentParser(description="Evaluate ForgeLLM models")
    parser.add_argument("--config", type=str, required=True, help="Path to training config YAML")
    parser.add_argument("--test_file", type=str, default="data/test/test.jsonl", help="Path to test JSONL")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
        
    print("Evaluating Base Model...")
    loader = ModelLoader(config.model.name, trust_remote_code=config.model.trust_remote_code)
    tokenizer = loader.load_tokenizer()
    
    # We apply 4-bit quantization for evaluation to fit in low VRAM
    q_config = get_quantization_config(config.quantization)
    base_model = loader.load_model(quantization_config=q_config)
    
    base_evaluator = ForgeEvaluator(base_model, tokenizer)
    base_results_path = os.path.join(config.training.output_dir, "evaluation", "base_results.json")
    base_results = base_evaluator.evaluate_test_set(args.test_file, base_results_path)
    
    print("Evaluating Fine-Tuned Model...")
    adapter_path = os.path.join(config.training.output_dir, "adapter")
    if not os.path.exists(adapter_path):
        print(f"Adapter not found at {adapter_path}. Run training first.")
        sys.exit(1)
        
    finetuned_model = PeftModel.from_pretrained(base_model, adapter_path)
    finetuned_evaluator = ForgeEvaluator(finetuned_model, tokenizer)
    finetuned_results_path = os.path.join(config.training.output_dir, "evaluation", "finetuned_results.json")
    finetuned_results = finetuned_evaluator.evaluate_test_set(args.test_file, finetuned_results_path)
    
    print("Generating Comparison...")
    comparison = []
    for base_res, ft_res in zip(base_results, finetuned_results):
        comparison.append({
            "prompt": base_res["prompt"],
            "base_response": base_res["generated"],
            "finetuned_response": ft_res["generated"]
        })
        
    comp_path = os.path.join(config.training.output_dir, "evaluation", "comparison.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
        
    print(f"Evaluation complete. Results saved to {os.path.dirname(comp_path)}")

if __name__ == "__main__":
    main()
