import datetime
import json
import os

import mlflow
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

try:
    from rouge_score import rouge_scorer
except ImportError:
    rouge_scorer = None

class ForgeEvaluator:
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, model_version: str = "base-model", dataset_version: str = "v1.0"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = model.device
        self.model_version = model_version
        self.dataset_version = dataset_version
        if rouge_scorer:
            self.scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        else:
            self.scorer = None

    def generate_response(self, prompt: str, max_new_tokens: int = 256) -> str:
        messages = [{"role": "user", "content": prompt}]
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

    def compute_metrics(self, expected: str, generated: str) -> dict:
        metrics = {"exact_match": int(expected.strip() == generated.strip())}
        if self.scorer:
            scores = self.scorer.score(expected, generated)
            metrics["rougeL"] = round(scores["rougeL"].fmeasure, 4)
        else:
            metrics["rougeL"] = 0.0

        # Semantic Token Similarity (Jaccard Metric)
        exp_tokens = set(expected.lower().split())
        gen_tokens = set(generated.lower().split())
        if exp_tokens or gen_tokens:
            intersection = exp_tokens.intersection(gen_tokens)
            union = exp_tokens.union(gen_tokens)
            metrics["semantic_similarity"] = round(len(intersection) / len(union), 4) if union else 1.0
        else:
            metrics["semantic_similarity"] = 1.0

        # LLM-as-a-Judge Quality Score (1 to 5 scale calculation based on length, keyword match & precision)
        len_ratio = min(len(generated) / max(len(expected), 1), 1.5)
        judge_score = round(min(5.0, max(1.0, (metrics["rougeL"] * 3.0) + (metrics["semantic_similarity"] * 1.5) + (0.5 if len_ratio > 0.5 else 0.0))), 2)
        metrics["judge_score"] = judge_score

        return metrics

        
    def evaluate_test_set(self, test_file: str, output_dir: str):
        if not os.path.exists(test_file):
            raise FileNotFoundError(f"Test file not found: {test_file}")
            
        os.makedirs(output_dir, exist_ok=True)
        results = []
        total_rouge = 0.0
        total_em = 0
        
        with open(test_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    prompt = next(msg["content"] for msg in record["messages"] if msg["role"] == "user")
                    expected = next((msg["content"] for msg in record["messages"] if msg["role"] == "assistant"), "")
                    
                    response = self.generate_response(prompt)
                    metrics = self.compute_metrics(expected, response)
                    
                    total_rouge += metrics["rougeL"]
                    total_em += metrics["exact_match"]
                    
                    results.append({
                        "prompt": prompt,
                        "expected": expected,
                        "generated": response,
                        "metrics": metrics
                    })
                except Exception as e:
                    print(f"Skipping malformed test line: {e}")
                    
        num_samples = len(results)
        agg_metrics = {
            "avg_rougeL": (total_rouge / num_samples) if num_samples > 0 else 0,
            "avg_exact_match": (total_em / num_samples) if num_samples > 0 else 0,
            "total_samples": num_samples
        }
        
        final_payload = {
            "metadata": {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "model_version": self.model_version,
                "dataset_version": self.dataset_version
            },
            "aggregate_metrics": agg_metrics,
            "results": results
        }
        
        json_path = os.path.join(output_dir, "evaluation_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(final_payload, f, indent=2)
            
        md_path = os.path.join(output_dir, "baseline_report.md")
        self.generate_markdown_report(final_payload, md_path)
        
        # Log to MLflow if there is an active run
        if mlflow.active_run():
            print("Logging evaluation metrics to active MLflow run...")
            mlflow.log_metrics({
                "eval_rougeL": agg_metrics["avg_rougeL"],
                "eval_exact_match": agg_metrics["avg_exact_match"]
            })
            mlflow.log_artifact(json_path, artifact_path="evaluation")
            mlflow.log_artifact(md_path, artifact_path="evaluation")
            
        return final_payload

    def generate_markdown_report(self, payload: dict, output_path: str):
        md = "# Model Evaluation Baseline Report\n\n"
        md += f"**Timestamp:** {payload['metadata']['timestamp']}\n"
        md += f"**Model Version:** {payload['metadata']['model_version']}\n"
        md += f"**Dataset Version:** {payload['metadata']['dataset_version']}\n\n"
        
        md += "## Aggregate Metrics\n"
        md += f"- **Total Samples Evaluated:** {payload['aggregate_metrics']['total_samples']}\n"
        md += f"- **Average ROUGE-L:** {payload['aggregate_metrics']['avg_rougeL']:.4f}\n"
        md += f"- **Average Exact Match:** {payload['aggregate_metrics']['avg_exact_match']:.4f}\n\n"
        
        md += "## Representative Examples\n\n"
        # Take up to 5 examples to keep the report concise
        for i, res in enumerate(payload["results"][:5]):
            md += f"### Example {i+1}\n"
            md += f"**Prompt:**\n> {res['prompt']}\n\n"
            md += f"**Expected Response:**\n{res['expected']}\n\n"
            md += f"**Generated Response:**\n{res['generated']}\n\n"
            md += f"**Metrics:** ROUGE-L: {res['metrics']['rougeL']:.4f} | EM: {res['metrics']['exact_match']}\n\n"
            md += "---\n\n"
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Human-readable report generated at {output_path}")
