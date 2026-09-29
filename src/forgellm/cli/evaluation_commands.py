import json
import os
from pathlib import Path
from typing import Optional

import mlflow
import torch
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from transformers import BitsAndBytesConfig

from forgellm.dataset.registry import DatasetRegistry
from forgellm.evaluation.evaluator import ForgeEvaluator
from forgellm.evaluation.judge import LLMJudge
from forgellm.experiments.manager import ExperimentManager

app = typer.Typer(help="Model evaluation and regression testing commands.")
console = Console()
exp_manager = ExperimentManager()
dataset_registry = DatasetRegistry()


@app.command(name="baseline")
def run_baseline(
    model_name: str = typer.Option("Qwen/Qwen2.5-0.5B", help="Base model to evaluate"),
    test_file: str = typer.Option("test.jsonl", help="Path to test dataset"),
    output_dir: str = typer.Option(
        "outputs/baseline", help="Directory to save baseline reports"
    ),
    judge: bool = typer.Option(
        False, "--judge", help="Enable LLM-as-a-Judge evaluation"
    ),
):
    """Run a deterministic baseline evaluation on a base LLM without fine-tuning."""
    console.print(
        Panel(
            f"[bold cyan]ForgeLLM Baseline Evaluation[/bold cyan]\nModel: {model_name}\nDataset: {test_file}"
        )
    )

    if not os.path.exists(test_file):
        typer.secho(f"Test dataset not found at {test_file}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

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

    llm_judge = LLMJudge() if judge else LLMJudge(provider="none")
    if judge and not llm_judge.is_enabled():
        console.print(
            "[yellow]Warning: --judge requested but FORGELLM_JUDGE_API_KEY/provider not configured. Running objective only.[/yellow]"
        )

    console.print("[yellow]Running Evaluation...[/yellow]")
    evaluator = ForgeEvaluator(
        model,
        tokenizer,
        model_version=model_name,
        dataset_version=test_file,
        judge=llm_judge,
    )
    results = evaluator.evaluate_test_set(test_file, output_dir)

    # Print Objective Metrics Table
    obj = results["aggregate_metrics"]
    table = Table(title="Objective Metrics Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Score", style="green")

    table.add_row("Total Samples", str(obj["total_samples"]))
    table.add_row("Exact Match", f"{obj['avg_exact_match'] * 100:.1f}%")
    table.add_row("ROUGE-L", f"{obj['avg_rougeL']:.4f}")
    table.add_row("Semantic Similarity", f"{obj['avg_semantic_similarity']:.4f}")
    table.add_row("Composite Quality", f"{obj['avg_composite_quality_score']:.4f}")

    console.print(table)

    # Print Judge Table if available
    judge_res = results.get("aggregate_judge_metrics")
    if judge_res:
        j_table = Table(title="LLM-as-a-Judge Metrics")
        j_table.add_column("Dimension", style="cyan")
        j_table.add_column("Score (1-5)", style="magenta")
        j_table.add_row("Relevance", f"{judge_res['avg_relevance']} / 5.0")
        j_table.add_row("Helpfulness", f"{judge_res['avg_helpfulness']} / 5.0")
        j_table.add_row(
            "Instruction Following", f"{judge_res['avg_instruction_following']} / 5.0"
        )
        j_table.add_row("Factuality", f"{judge_res['avg_factuality']} / 5.0")
        j_table.add_row("Safety", f"{judge_res['avg_safety']} / 5.0")
        j_table.add_row("Overall Quality", f"{judge_res['avg_overall']} / 5.0")
        console.print(j_table)

    console.print(
        f"[bold green]Reports and artifacts saved to {output_dir}/[/bold green]"
    )


@app.command(name="evaluate")
def run_evaluate(
    experiment_id: str,
    min_rouge_improvement: float = typer.Option(
        0.01, help="Minimum ROUGE-L delta required to be considered 'improved'"
    ),
    max_rouge_degradation: float = typer.Option(
        0.01,
        help="Maximum ROUGE-L delta degradation allowed before failing Quality Gate",
    ),
    min_exact_match_improvement: float = typer.Option(
        0.0, help="Minimum Exact Match delta for improvement"
    ),
    max_exact_match_degradation: float = typer.Option(
        0.02, help="Maximum Exact Match degradation allowed"
    ),
    min_semantic_similarity_improvement: float = typer.Option(
        0.0, help="Minimum Semantic Similarity delta for improvement"
    ),
    max_semantic_similarity_degradation: float = typer.Option(
        0.02, help="Maximum Semantic Similarity degradation allowed"
    ),
    min_composite_improvement: float = typer.Option(
        0.0, help="Minimum composite quality score delta for improvement"
    ),
    max_composite_degradation: float = typer.Option(
        0.02, help="Maximum composite quality degradation allowed"
    ),
    min_judge_overall_improvement: float = typer.Option(
        0.0, help="Minimum LLM Judge overall score delta for improvement"
    ),
    max_judge_overall_degradation: float = typer.Option(
        0.25, help="Maximum LLM Judge overall score degradation allowed"
    ),
    max_safety_degradation: float = typer.Option(
        0.0, help="Maximum safety score degradation allowed (zero tolerance)"
    ),
    judge: bool = typer.Option(
        False, "--judge", help="Enable LLM-as-a-Judge evaluation"
    ),
):
    """Evaluate an experiment (Base vs Fine-Tuned) with multi-metric Regression Analysis."""
    exp = exp_manager.storage.get_experiment(experiment_id)
    if not exp:
        typer.secho(f"Experiment {experiment_id} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    ds_info = dataset_registry.get_version_info(exp.dataset, exp.dataset_version)
    if not ds_info or not ds_info.get("val_path"):
        typer.secho(
            f"Validation dataset not found for {exp.dataset}:{exp.dataset_version}.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    exp_dir = Path(".forgellm/experiments") / experiment_id
    results_dir = exp_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel(
            f"[bold cyan]ForgeLLM Experiment Evaluation & Quality Gate[/bold cyan]\nExperiment ID: {experiment_id}\nModel: {exp.model}\nDataset: {exp.dataset}:{exp.dataset_version}"
        )
    )

    # Quantization setup
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

    llm_judge = LLMJudge() if judge else LLMJudge(provider="none")
    if judge and not llm_judge.is_enabled():
        console.print(
            "[yellow]Warning: --judge requested but judge provider is not configured. Running objective metrics only.[/yellow]"
        )

    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("ForgeLLM_FineTuning_Evaluation")

    with mlflow.start_run(run_name=f"eval_{experiment_id}"):
        mlflow.set_tag("experiment_id", experiment_id)
        mlflow.set_tag("dataset", exp.dataset)

        # 1. Evaluate Base Model
        console.print("[yellow]1/2 Loading Base Model...[/yellow]")
        loader = ModelLoader(exp.model)
        tokenizer = loader.load_tokenizer()
        base_model = loader.load_model(quantization_config=q_config)

        console.print("[yellow]Evaluating Base Model...[/yellow]")
        base_evaluator = ForgeEvaluator(
            base_model,
            tokenizer,
            model_version=f"{exp.model}-base",
            dataset_version=exp.dataset_version,
            judge=llm_judge,
        )
        base_results = base_evaluator.evaluate_test_set(
            ds_info["val_path"], str(results_dir / "base_results")
        )

        # Free memory
        del base_model
        import gc

        gc.collect()
        if torch.cuda.is_available():
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
            typer.secho(
                f"Trained adapter for experiment {experiment_id} not found in model registry.",
                fg=typer.colors.RED,
            )
            raise typer.Exit(code=1)

        adapter_path = os.path.join(model_info["location"], "adapter")

        console.print("[yellow]2/2 Loading Fine-Tuned Model Adapter...[/yellow]")
        base_model = loader.load_model(quantization_config=q_config)
        ft_model = PeftModel.from_pretrained(base_model, adapter_path)

        console.print("[yellow]Evaluating Fine-Tuned Model...[/yellow]")
        ft_evaluator = ForgeEvaluator(
            ft_model,
            tokenizer,
            model_version=f"{exp.model}-finetuned",
            dataset_version=exp.dataset_version,
            judge=llm_judge,
        )
        ft_results = ft_evaluator.evaluate_test_set(
            ds_info["val_path"], str(results_dir / "ft_results")
        )

    # Generate Comparison JSON
    comparison = []
    base_res_list = base_results["results"]
    ft_res_list = ft_results["results"]

    for base_res, ft_res in zip(base_res_list, ft_res_list):
        comp_item = {
            "prompt": base_res["prompt"],
            "expected": base_res["expected"],
            "base_response": base_res["generated"],
            "ft_response": ft_res["generated"],
            "base_objective": base_res["objective_metrics"],
            "ft_objective": ft_res["objective_metrics"],
        }
        if "judge_metrics" in base_res and "judge_metrics" in ft_res:
            comp_item["base_judge"] = base_res["judge_metrics"]
            comp_item["ft_judge"] = ft_res["judge_metrics"]
        comparison.append(comp_item)

    with open(results_dir / "comparison.json", "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)

    # Run Multi-Metric Regression Analysis
    console.print("[yellow]Running Regression Analysis...[/yellow]")
    analyzer = RegressionAnalyzer(base_results, ft_results)
    payload = analyzer.generate_report(
        str(results_dir),
        min_rouge_improvement=min_rouge_improvement,
        max_rouge_degradation=max_rouge_degradation,
        min_exact_match_improvement=min_exact_match_improvement,
        max_exact_match_degradation=max_exact_match_degradation,
        min_semantic_similarity_improvement=min_semantic_similarity_improvement,
        max_semantic_similarity_degradation=max_semantic_similarity_degradation,
        min_composite_improvement=min_composite_improvement,
        max_composite_degradation=max_composite_degradation,
        min_judge_overall_improvement=min_judge_overall_improvement,
        max_judge_overall_degradation=max_judge_overall_degradation,
        max_safety_degradation=max_safety_degradation,
    )

    if mlflow.active_run():
        mlflow.log_artifact(
            str(results_dir / "regression_report.md"), artifact_path="regression"
        )
        mlflow.log_artifact(
            str(results_dir / "regression_results.json"), artifact_path="regression"
        )
        mlflow.log_metrics(
            {
                "delta_rougeL": payload["metrics"]["rougeL_delta"],
                "delta_exact_match": payload["metrics"]["exact_match_delta"],
                "delta_composite_quality": payload["metrics"][
                    "composite_quality_delta"
                ],
            }
        )

    # Print Results Table
    metrics = payload["metrics"]
    table = Table(
        title=f"Quality Gate Evaluation (Status: {payload['status'].upper()})"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Base Model", style="magenta")
    table.add_column("Fine-Tuned", style="green")
    table.add_column("Delta", style="yellow")

    def fmt_d(val: float) -> str:
        s = "+" if val > 0 else ""
        return f"{s}{val:.4f}"

    table.add_row(
        "Exact Match",
        f"{metrics['base_exact_match'] * 100:.1f}%",
        f"{metrics['ft_exact_match'] * 100:.1f}%",
        fmt_d(metrics["exact_match_delta"]),
    )
    table.add_row(
        "ROUGE-L",
        f"{metrics['base_rougeL']:.4f}",
        f"{metrics['ft_rougeL']:.4f}",
        fmt_d(metrics["rougeL_delta"]),
    )
    table.add_row(
        "Semantic Similarity",
        f"{metrics['base_semantic_similarity']:.4f}",
        f"{metrics['ft_semantic_similarity']:.4f}",
        fmt_d(metrics["semantic_similarity_delta"]),
    )
    table.add_row(
        "Composite Quality",
        f"{metrics['base_composite_quality']:.4f}",
        f"{metrics['ft_composite_quality']:.4f}",
        fmt_d(metrics["composite_quality_delta"]),
    )

    if metrics.get("judge_available", False):
        table.add_row(
            "Judge Overall (1-5)",
            f"{metrics['base_judge_overall']:.2f}",
            f"{metrics['ft_judge_overall']:.2f}",
            f"{metrics['judge_overall_delta']:+.2f}",
        )
        table.add_row(
            "Judge Safety (1-5)",
            f"{metrics['base_judge_safety']:.2f}",
            f"{metrics['ft_judge_safety']:.2f}",
            f"{metrics['judge_safety_delta']:+.2f}",
        )

    console.print(table)
    console.print(
        f"[bold green]Comparison saved to {results_dir}/comparison.json[/bold green]"
    )
    console.print(
        f"[bold green]Regression Report saved to {results_dir}/regression_report.md[/bold green]"
    )

    if not payload["passed"]:
        typer.secho(
            f"\n❌ Quality Gate Failed: Model categorized as '{payload['status']}'.",
            fg=typer.colors.RED,
            bold=True,
        )
        if payload.get("failure_reasons"):
            for reason in payload["failure_reasons"]:
                typer.secho(f"  - {reason}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    else:
        typer.secho(
            f"\n✅ Quality Gate Passed: Model categorized as '{payload['status']}'.",
            fg=typer.colors.GREEN,
            bold=True,
        )

        from forgellm.models.mlflow_registry import MLflowModelRegistry

        mlflow_registry = MLflowModelRegistry("http://localhost:5000")

        # Log adapter artifacts to MLflow
        try:
            import mlflow.pyfunc as _pyfunc

            class AdapterWrapper(_pyfunc.PythonModel):
                def predict(self, context, model_input):
                    pass

            _pyfunc.log_model(
                artifact_path="model_adapter",
                python_model=AdapterWrapper(),
                artifacts={"adapter_weights": str(adapter_path)},
            )
            safe_model_name = f"ForgeLLM_{exp.model.replace('/', '_')}"
            run_id = mlflow.active_run().info.run_id
            version = mlflow_registry.register_model(run_id, safe_model_name)
            typer.secho(
                f"Registered {safe_model_name} version {version} in MLflow Model Registry.",
                fg=typer.colors.CYAN,
            )
        except Exception as e:
            console.print(f"[yellow]MLflow Model Registration notice: {e}[/yellow]")
