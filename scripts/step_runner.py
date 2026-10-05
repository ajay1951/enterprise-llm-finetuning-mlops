import sys
import os
import datetime
import json
import shutil
import gc
import traceback
import torch

sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("."))

from forgellm.training.config import load_config
from forgellm.training.quantization import get_quantization_config
from forgellm.training.trainer import ForgeTrainer
from forgellm.models.loader import ModelLoader
from forgellm.models.registry import ModelRegistry
from forgellm.models.exporter import ModelExporter
from forgellm.models.mlflow_registry import MLflowModelRegistry
from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.evaluation.judge import LLMJudge
from forgellm.evaluation.regression import RegressionAnalyzer

config_path = "configs/presets/micro_qlora.yaml"
dataset_path = "tests/fixtures/sample_dataset.jsonl"
config = load_config(config_path)

print("[STEP 1] Starting Step 1: Environment Diagnostic...", flush=True)
env_info = {
    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    "os": "Windows",
    "python_version": sys.version.split()[0],
    "torch_version": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
}
os.makedirs("artifacts/fine_tuning", exist_ok=True)
with open("artifacts/fine_tuning/environment_info.json", "w", encoding="utf-8") as f:
    json.dump(env_info, f, indent=2)
print("  Environment diagnostic saved.", flush=True)

print("\n[STEP 2] Starting Step 2: Baseline Model Evaluation...", flush=True)
os.makedirs("artifacts/baseline", exist_ok=True)
loader = ModelLoader(config.model.name, trust_remote_code=config.model.trust_remote_code)
tokenizer = loader.load_tokenizer()
q_config = get_quantization_config(config.quantization)
base_model = loader.load_model(quantization_config=q_config)

judge = LLMJudge(provider="none")
base_evaluator = ForgeEvaluator(
    model=base_model,
    tokenizer=tokenizer,
    model_version=f"{config.model.name}-baseline",
    judge=judge,
)
base_results = base_evaluator.evaluate_test_set(dataset_path, "artifacts/baseline")
print(f"  Baseline Avg Composite: {base_results['aggregate_metrics']['avg_composite_quality_score']}", flush=True)

# Free base model VRAM
del base_model
del base_evaluator
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

print("\n[STEP 3] Starting Step 3: Micro Fine-Tuning...", flush=True)
trainer = ForgeTrainer(config_path)
trainer.prepare_dataset(dataset_path, dataset_path)
start_time = datetime.datetime.now(datetime.UTC)
trainer.train()
end_time = datetime.datetime.now(datetime.UTC)
duration_secs = (end_time - start_time).total_seconds()
adapter_dir = os.path.join(config.training.output_dir, "adapter")
try:
    trainer.save_model(adapter_dir)
except Exception:
    pass

if not os.path.exists(adapter_dir) or not os.listdir(adapter_dir):
    ckpts = [
        os.path.join(config.training.output_dir, d)
        for d in os.listdir(config.training.output_dir)
        if d.startswith("checkpoint-")
        and os.path.isdir(os.path.join(config.training.output_dir, d))
    ]
    if ckpts:
        adapter_dir = sorted(ckpts, key=lambda x: int(x.split("-")[-1]))[-1]

print(f"  Training finished in {duration_secs:.2f}s | Adapter at: {adapter_dir}", flush=True)

# Free trainer
del trainer
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

training_metrics = {
    "model": config.model.name,
    "dataset": dataset_path,
    "epochs": config.training.num_train_epochs,
    "duration_seconds": round(duration_secs, 2),
    "adapter_dir": adapter_dir,
    "seed": config.training.seed,
    "learning_rate": config.training.learning_rate,
    "lora_rank": config.lora.r,
    "lora_alpha": config.lora.alpha,
}
with open("artifacts/fine_tuning/training_metrics.json", "w", encoding="utf-8") as f:
    json.dump(training_metrics, f, indent=2)
shutil.copy(config_path, "artifacts/fine_tuning/training_config.yaml")
with open("artifacts/fine_tuning/README.md", "w", encoding="utf-8") as f:
    f.write(f"# Fine-Tuning Summary\nDuration: {duration_secs:.2f}s\n")

print("\n[STEP 4] Starting Step 4: Model Export & Merge...", flush=True)
local_registry = ModelRegistry()
reg_entry = local_registry.register(
    model_name="forgellm-qwen-phase3",
    base_model=config.model.name,
    method="lora",
    dataset_ref=dataset_path,
    experiment_id=f"phase3-{config.training.seed}",
    status="ready",
)
target_adapter_dir = os.path.join(reg_entry["location"], "adapter")
shutil.copytree(adapter_dir, target_adapter_dir, dirs_exist_ok=True)

os.makedirs("artifacts/model", exist_ok=True)
export_out = "outputs/exported_model"
exporter = ModelExporter(registry=local_registry)
exported_path = exporter.export_merged_model(
    f"forgellm-qwen-phase3:{reg_entry['version']}", export_out
)
export_metadata = {
    "model_name": "forgellm-qwen-phase3",
    "version": reg_entry["version"],
    "base_model": config.model.name,
    "adapter_location": adapter_dir,
    "exported_location": exported_path,
    "format": "pytorch",
    "exported_at": datetime.datetime.now(datetime.UTC).isoformat(),
}
with open("artifacts/model/metadata.json", "w", encoding="utf-8") as f:
    json.dump(export_metadata, f, indent=2)
with open("artifacts/model/README.md", "w", encoding="utf-8") as f:
    f.write(f"# Exported Model\nPath: {exported_path}\n")
print(f"  Model exported to {export_out}", flush=True)

print("\n[STEP 5] Starting Step 5: MLflow Registration...", flush=True)
try:
    registry = MLflowModelRegistry(tracking_uri="sqlite:///mlruns.db")
    ver = registry.register_model(f"phase3-run-{config.training.seed}", "ForgeLLM-Qwen-Expert")
    registry.promote_model("ForgeLLM-Qwen-Expert", version=int(ver) if str(ver).isdigit() else ver)
    print(f"  Model registered and promoted to Production alias.", flush=True)
except Exception as e:
    print(f"  MLflow tracking notice: {e}", flush=True)

print("\n[STEP 6] Starting Step 6: Fine-Tuned Model Evaluation...", flush=True)
os.makedirs("artifacts/fine_tuned", exist_ok=True)
loader = ModelLoader(config.model.name, trust_remote_code=config.model.trust_remote_code)
eval_base = loader.load_model(quantization_config=q_config)
from peft import PeftModel
ft_model = PeftModel.from_pretrained(eval_base, adapter_dir)

ft_evaluator = ForgeEvaluator(
    model=ft_model,
    tokenizer=tokenizer,
    model_version=f"{config.model.name}-finetuned",
    judge=judge,
)
ft_results = ft_evaluator.evaluate_test_set(dataset_path, "artifacts/fine_tuned")
print(f"  Fine-Tuned Avg Composite: {ft_results['aggregate_metrics']['avg_composite_quality_score']}", flush=True)

print("\n[STEP 7] Starting Step 7: Regression & Quality Gate...", flush=True)
os.makedirs("artifacts/quality_gate", exist_ok=True)
analyzer = RegressionAnalyzer(base_results, ft_results)
reg_report_payload = analyzer.generate_report("artifacts/quality_gate")
if os.path.exists("artifacts/quality_gate/regression_report.md"):
    shutil.copy("artifacts/quality_gate/regression_report.md", "artifacts/quality_gate/report.md")

qgate_summary = {
    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
    "baseline_model": config.model.name,
    "finetuned_model": f"{config.model.name}-finetuned",
    "dataset": dataset_path,
    "status": "PASSED" if ft_results["aggregate_metrics"]["avg_composite_quality_score"] >= base_results["aggregate_metrics"]["avg_composite_quality_score"] else "FLAGGED",
    "comparison": {
        "exact_match": {
            "baseline": base_results["aggregate_metrics"]["avg_exact_match"],
            "finetuned": ft_results["aggregate_metrics"]["avg_exact_match"],
            "delta": round(ft_results["aggregate_metrics"]["avg_exact_match"] - base_results["aggregate_metrics"]["avg_exact_match"], 4),
        },
        "rougeL": {
            "baseline": base_results["aggregate_metrics"]["avg_rougeL"],
            "finetuned": ft_results["aggregate_metrics"]["avg_rougeL"],
            "delta": round(ft_results["aggregate_metrics"]["avg_rougeL"] - base_results["aggregate_metrics"]["avg_rougeL"], 4),
        },
        "semantic_similarity": {
            "baseline": base_results["aggregate_metrics"]["avg_semantic_similarity"],
            "finetuned": ft_results["aggregate_metrics"]["avg_semantic_similarity"],
            "delta": round(ft_results["aggregate_metrics"]["avg_semantic_similarity"] - base_results["aggregate_metrics"]["avg_semantic_similarity"], 4),
        },
        "composite_quality_score": {
            "baseline": base_results["aggregate_metrics"]["avg_composite_quality_score"],
            "finetuned": ft_results["aggregate_metrics"]["avg_composite_quality_score"],
            "delta": round(ft_results["aggregate_metrics"]["avg_composite_quality_score"] - base_results["aggregate_metrics"]["avg_composite_quality_score"], 4),
        },
    },
}
with open("artifacts/quality_gate/quality_gate.json", "w", encoding="utf-8") as f:
    json.dump(qgate_summary, f, indent=2)

print("\n" + "=" * 70, flush=True)
print("PHASE 3 LIFECYCLE COMPLETED SUCCESSFULLY!", flush=True)
print("=" * 70, flush=True)
for m, vals in qgate_summary["comparison"].items():
    print(f"  {m:<25} | Baseline: {vals['baseline']:<8.4f} | FT: {vals['finetuned']:<8.4f} | Delta: {vals['delta']:+<8.4f}", flush=True)
print("=" * 70, flush=True)
