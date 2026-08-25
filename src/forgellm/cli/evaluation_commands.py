import typer
import os
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from forgellm.experiments.manager import ExperimentManager
from forgellm.dataset.registry import DatasetRegistry
from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.training.quantization import get_quantization_config
from transformers import BitsAndBytesConfig
import torch

app = typer.Typer(help="Evaluation commands.")
console = Console()
exp_manager = ExperimentManager()
dataset_registry = DatasetRegistry()

@app.command(name="evaluate")
def run_evaluate(experiment_id: str):
    """Evaluate an experiment (Base vs Fine-Tuned)."""
    exp = exp_manager.storage.get_experiment(experiment_id)
    if not exp:
        typer.secho(f"Experiment {experiment_id} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    ds_info = dataset_registry.get_version_info(exp.dataset, exp.dataset_version)
    if not ds_info or not ds_info.get("val_path"):
        typer.secho(f"Validation dataset not found for {exp.dataset}:{exp.dataset_version}.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    exp_dir = Path(".forgellm/experiments") / experiment_id
    results_dir = exp_dir / "results"
    results_dir.mkdir(exist_ok=True)
    
    console.print(f"[cyan]Evaluating Experiment {experiment_id}[/cyan]")
    
    # Fast quantization config
    q_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=False,
    )
    
    from forgellm.models.loader import ModelLoader
    from peft import PeftModel
    
    # 1. Evaluate Base Model
    console.print("[yellow]Loading Base Model...[/yellow]")
    loader = ModelLoader(exp.model)
    tokenizer = loader.load_tokenizer()
    base_model = loader.load_model(quantization_config=q_config)
    
    console.print("[yellow]Evaluating Base Model...[/yellow]")
    base_evaluator = ForgeEvaluator(base_model, tokenizer)
    base_results = base_evaluator.evaluate_test_set(ds_info["val_path"], str(results_dir / "base_results.json"))
    
    # Free memory
    del base_model
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    
    # 2. Evaluate Fine-Tuned Model
    # Find adapter path by searching models for this experiment ID
    from forgellm.models.registry import ModelRegistry
    model_registry = ModelRegistry()
    
    model_info = None
    models = model_registry.list_models()
    for m in models:
        versions = model_registry.list_versions(m)
        for v in versions:
            if v.get("experiment") == experiment_id:
                model_info = v
                break
        if model_info:
            break
    
    if not model_info or model_info["status"] != "ready":
        typer.secho("Trained adapter not found or not ready.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    adapter_path = os.path.join(model_info["location"], "adapter")
    
    console.print("[yellow]Loading Fine-Tuned Model...[/yellow]")
    base_model = loader.load_model(quantization_config=q_config)
    ft_model = PeftModel.from_pretrained(base_model, adapter_path)
    
    console.print("[yellow]Evaluating Fine-Tuned Model...[/yellow]")
    ft_evaluator = ForgeEvaluator(ft_model, tokenizer)
    ft_results = ft_evaluator.evaluate_test_set(ds_info["val_path"], str(results_dir / "ft_results.json"))
    
    # Generate Comparison
    comparison = []
    for base_res, ft_res in zip(base_results, ft_results):
        comparison.append({
            "prompt": base_res["prompt"],
            "base_response": base_res["generated"],
            "ft_response": ft_res["generated"]
        })
        
    with open(results_dir / "comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)
        
    # Print Table
    table = Table(title=f"Evaluation Results ({len(comparison)} examples)")
    table.add_column("Metric", style="cyan")
    table.add_column("Base Model", style="magenta")
    table.add_column("Fine-Tuned Model", style="green")
    
    # For now, just compare structural differences or simple metrics
    base_avg_len = sum(len(c["base_response"]) for c in comparison) / max(1, len(comparison))
    ft_avg_len = sum(len(c["ft_response"]) for c in comparison) / max(1, len(comparison))
    
    table.add_row("Examples", str(len(comparison)), str(len(comparison)))
    table.add_row("Avg Response Length", f"{base_avg_len:.1f} chars", f"{ft_avg_len:.1f} chars")
    
    console.print(table)
    console.print(f"[bold green]Comparison saved to {results_dir}/comparison.json[/bold green]")
