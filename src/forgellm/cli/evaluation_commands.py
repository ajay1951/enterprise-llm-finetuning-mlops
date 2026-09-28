import json
import os
from pathlib import Path

import mlflow
import torch
import typer
from rich.console import Console
from rich.table import Table
from transformers import BitsAndBytesConfig

from forgellm.dataset.registry import DatasetRegistry
from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.experiments.manager import ExperimentManager

app = typer.Typer(help="Evaluation commands.")
console = Console()
exp_manager = ExperimentManager()
dataset_registry = DatasetRegistry()

@app.command(name="baseline")
def run_baseline(
    model_name: str = typer.Option("Qwen/Qwen2.5-0.5B", help="Base model to evaluate"),
    test_file: str = typer.Option("test.jsonl", help="Path to test dataset"),
    output_dir: str = typer.Option("outputs/baseline", help="Directory to save baseline reports")
):
    """Run a rigorous baseline evaluation on a base LLM without fine-tuning."""
    console.print(f"[cyan]Starting Baseline Evaluation for {model_name}[/cyan]")
    
    if not os.path.exists(test_file):
        typer.secho(f"Test dataset not found at {test_file}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    import torch
    from transformers import BitsAndBytesConfig

    from forgellm.models.loader import ModelLoader
    
    q_config = None
    if torch.cuda.is_available():
        q_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=False,
        )
    
    console.print("[yellow]Loading Base Model & Tokenizer...[/yellow]")
    loader = ModelLoader(model_name)
    tokenizer = loader.load_tokenizer()
    model = loader.load_model(quantization_config=q_config)
    
    console.print("[yellow]Running Metric Evaluation...[/yellow]")
    evaluator = ForgeEvaluator(model, tokenizer, model_version=model_name, dataset_version=test_file)
    results = evaluator.evaluate_test_set(test_file, output_dir)
    
    # Print summary
    table = Table(title="Baseline Metrics Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="green")
    
    table.add_row("Samples Evaluated", str(results["aggregate_metrics"]["total_samples"]))
    table.add_row("ROUGE-L (Avg)", f"{results['aggregate_metrics']['avg_rougeL']:.4f}")
    table.add_row("Exact Match (Avg)", f"{results['aggregate_metrics']['avg_exact_match']:.4f}")
    
    console.print(table)
    console.print(f"[bold green]Baseline report saved to {output_dir}/baseline_report.md[/bold green]")


@app.command(name="evaluate")
def run_evaluate(
    experiment_id: str,
    min_rouge_improvement: float = typer.Option(0.01, help="Minimum ROUGE-L delta required to be considered 'improved'"),
    max_rouge_degradation: float = typer.Option(0.01, help="Maximum ROUGE-L delta degradation allowed before failing the Quality Gate")
):
    """Evaluate an experiment (Base vs Fine-Tuned) with Regression Analysis."""
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
    q_config = None
    if torch.cuda.is_available():
        q_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=False,
        )
    
    from peft import PeftModel

    from forgellm.evaluation.regression import RegressionAnalyzer
    from forgellm.models.loader import ModelLoader
    
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("ForgeLLM_FineTuning_Evaluation")
    
    with mlflow.start_run(run_name=f"eval_{experiment_id}"):
        mlflow.set_tag("experiment_id", experiment_id)
        mlflow.set_tag("dataset", exp.dataset)
        
        # 1. Evaluate Base Model
        console.print("[yellow]Loading Base Model...[/yellow]")
        loader = ModelLoader(exp.model)
        tokenizer = loader.load_tokenizer()
        base_model = loader.load_model(quantization_config=q_config)
        
        console.print("[yellow]Evaluating Base Model...[/yellow]")
        base_evaluator = ForgeEvaluator(base_model, tokenizer)
        base_results = base_evaluator.evaluate_test_set(ds_info["val_path"], str(results_dir / "base_results"))
        
        # Free memory
        del base_model
        import gc
        gc.collect()
        torch.cuda.empty_cache()
        
        # 2. Evaluate Fine-Tuned Model
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
        ft_results = ft_evaluator.evaluate_test_set(ds_info["val_path"], str(results_dir / "ft_results"))
    
    # Generate Comparison
    comparison = []
    base_res_list = base_results["results"]
    ft_res_list = ft_results["results"]
    
    for base_res, ft_res in zip(base_res_list, ft_res_list):
        comparison.append({
            "prompt": base_res["prompt"],
            "base_response": base_res["generated"],
            "ft_response": ft_res["generated"]
        })
        
    with open(results_dir / "comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)
        
        # Run Regression Analysis
        console.print("[yellow]Running Regression Analysis...[/yellow]")
        analyzer = RegressionAnalyzer(base_results, ft_results)
        payload = analyzer.generate_report(str(results_dir), min_rouge_improvement, max_rouge_degradation)
        
        mlflow.log_artifact(str(results_dir / "regression_report.md"), artifact_path="regression")
        mlflow.log_artifact(str(results_dir / "regression_results.json"), artifact_path="regression")
        mlflow.log_metrics({
            "delta_rougeL": payload["metrics"]["rougeL_delta"],
            "delta_exact_match": payload["metrics"]["exact_match_delta"]
        })
    
    # Print Table
    table = Table(title=f"Regression Results (Status: {payload['status'].upper()})")
    table.add_column("Metric", style="cyan")
    table.add_column("Base Model", style="magenta")
    table.add_column("Fine-Tuned Model", style="green")
    table.add_column("Delta", style="yellow")
    
    metrics = payload["metrics"]
    r_sign = "+" if metrics["rougeL_delta"] > 0 else ""
    
    table.add_row("ROUGE-L Score", f"{metrics['base_rougeL']:.4f}", f"{metrics['ft_rougeL']:.4f}", f"{r_sign}{metrics['rougeL_delta']:.4f}")
    
    console.print(table)
    console.print(f"[bold green]Comparison saved to {results_dir}/comparison.json[/bold green]")
    console.print(f"[bold green]Regression Report saved to {results_dir}/regression_report.md[/bold green]")
    
    if not payload["passed"]:
        typer.secho(f"Model failed the Quality Gate! (Status: {payload['status']})", fg=typer.colors.RED)
        typer.secho("Model will NOT be registered.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    else:
        typer.secho(f"Model passed the Quality Gate! (Status: {payload['status']})", fg=typer.colors.GREEN)
        
        from forgellm.models.mlflow_registry import MLflowModelRegistry
        mlflow_registry = MLflowModelRegistry("http://localhost:5000")
        
        # Log the adapter artifacts to THIS evaluation run so they are bound to the metrics
        print("Logging adapter artifacts to evaluation run for registration...")
        import mlflow.pyfunc as _pyfunc
        class AdapterWrapper(_pyfunc.PythonModel):
            def predict(self, context, model_input):
                pass
                
        _pyfunc.log_model(
            artifact_path="model_adapter",
            python_model=AdapterWrapper(),
            artifacts={"adapter_weights": str(adapter_path)}
        )
        
        # Register the model
        safe_model_name = f"ForgeLLM_{exp.model.replace('/', '_')}"
        run_id = mlflow.active_run().info.run_id
        
        version = mlflow_registry.register_model(run_id, safe_model_name)
        typer.secho(f"Successfully registered {safe_model_name} version {version}!", fg=typer.colors.CYAN)
        typer.secho(f"Run `forge model promote {safe_model_name} {version}` to deploy to Production.", fg=typer.colors.CYAN)
