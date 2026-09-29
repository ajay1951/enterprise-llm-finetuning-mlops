import argparse
import json
import os
import sys

from peft import PeftModel

from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.evaluation.regression import RegressionAnalyzer
from forgellm.models.loader import ModelLoader
from forgellm.training.config import load_config
from forgellm.training.quantization import get_quantization_config


def main():
    parser = argparse.ArgumentParser(description="Evaluate ForgeLLM models")
    parser.add_argument(
        "--config", type=str, required=True, help="Path to training config YAML"
    )
    parser.add_argument(
        "--test_file",
        type=str,
        default="data/test/test.jsonl",
        help="Path to test JSONL",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    eval_out_dir = os.path.join(config.training.output_dir, "evaluation")
    os.makedirs(eval_out_dir, exist_ok=True)

    print("Evaluating Base Model...")
    loader = ModelLoader(
        config.model.name, trust_remote_code=config.model.trust_remote_code
    )
    tokenizer = loader.load_tokenizer()

    q_config = get_quantization_config(config.quantization)
    base_model = loader.load_model(quantization_config=q_config)

    base_evaluator = ForgeEvaluator(
        base_model, tokenizer, model_version=f"{config.model.name}-base"
    )
    base_results_dir = os.path.join(eval_out_dir, "base_results")
    base_results = base_evaluator.evaluate_test_set(args.test_file, base_results_dir)

    print("Evaluating Fine-Tuned Model...")
    adapter_path = os.path.join(config.training.output_dir, "adapter")
    if not os.path.exists(adapter_path):
        print(f"Adapter not found at {adapter_path}. Run training first.")
        sys.exit(1)

    finetuned_model = PeftModel.from_pretrained(base_model, adapter_path)
    finetuned_evaluator = ForgeEvaluator(
        finetuned_model, tokenizer, model_version=f"{config.model.name}-finetuned"
    )
    finetuned_results_dir = os.path.join(eval_out_dir, "finetuned_results")
    finetuned_results = finetuned_evaluator.evaluate_test_set(
        args.test_file, finetuned_results_dir
    )

    print("Generating Comparison...")
    comparison = []
    for base_res, ft_res in zip(base_results["results"], finetuned_results["results"]):
        comparison.append(
            {
                "prompt": base_res["prompt"],
                "expected": base_res["expected"],
                "base_response": base_res["generated"],
                "finetuned_response": ft_res["generated"],
                "base_metrics": base_res["objective_metrics"],
                "finetuned_metrics": ft_res["objective_metrics"],
            }
        )

    comp_path = os.path.join(eval_out_dir, "comparison.json")
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    print("Running Regression Analysis...")
    analyzer = RegressionAnalyzer(base_results, finetuned_results)
    analyzer.generate_report(eval_out_dir)

    print(f"Evaluation complete. Results saved to {eval_out_dir}")


if __name__ == "__main__":
    main()
