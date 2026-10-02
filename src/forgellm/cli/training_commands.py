import json
import os
import time
from pathlib import Path

import typer
import yaml
from rich.console import Console

from forgellm.dataset.registry import DatasetRegistry
from forgellm.experiments.manager import ExperimentManager
from forgellm.models.registry import ModelRegistry

app = typer.Typer(help="Model training commands.")

console = Console()
exp_manager = ExperimentManager()
model_registry = ModelRegistry()
dataset_registry = DatasetRegistry()

import collections.abc


def deep_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def resolve_config(
    config_path: str | None, preset: str | None, overrides: dict
) -> dict:
    config = {}

    # 1. Defaults
    config = {
        "model": {"name": "Qwen/Qwen2.5-0.5B"},
        "quantization": {"enabled": False},
        "lora": {
            "r": 8,
            "alpha": 16,
            "dropout": 0.05,
            "target_modules": ["q_proj", "v_proj"],
        },
        "dataset": {"max_seq_length": 256},
        "training": {
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 1,
            "num_train_epochs": 1,
            "learning_rate": 2e-4,
        },
    }

    # 2. User YAML config
    if config_path and os.path.exists(config_path):
        with open(config_path, "r") as f:
            user_config = yaml.safe_load(f)
            deep_update(config, user_config)

    # 3. Preset
    if preset:
        preset_path = f"configs/presets/{preset}.yaml"
        if os.path.exists(preset_path):
            with open(preset_path, "r") as f:
                preset_config = yaml.safe_load(f)
                deep_update(config, preset_config)

    # 4. CLI overrides
    for k, v in overrides.items():
        if v is not None:
            if k == "epochs":
                config["training"]["num_train_epochs"] = v
            elif k == "learning_rate":
                config["training"]["learning_rate"] = v
            elif k == "batch_size":
                config["training"]["per_device_train_batch_size"] = v
            elif k == "model":
                config["model"]["name"] = v

    return config


@app.command(name="train")  # renamed function to avoid collision with app.command()
def run_train(
    model: str | None = typer.Option(None, help="Base model ID"),
    dataset: str = typer.Option(
        ..., help="Dataset reference (e.g., customer-support:v1)"
    ),
    method: str = typer.Option("qlora", help="Training method"),
    config: str | None = typer.Option(None, help="Path to config YAML"),
    preset: str | None = typer.Option(None, help="Configuration preset"),
    epochs: int | None = typer.Option(None, help="Override epochs"),
    learning_rate: float | None = typer.Option(None, help="Override learning rate"),
    batch_size: int | None = typer.Option(None, help="Override batch size"),
):
    """Run model fine-tuning."""
    # Resolve dataset
    if ":" not in dataset:
        dataset_name, dataset_version = dataset, "v1"
    else:
        dataset_name, dataset_version = dataset.split(":")

    ds_info = dataset_registry.get_version_info(dataset_name, dataset_version)
    if not ds_info:
        typer.secho(f"Dataset {dataset} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Resolve configuration precedence
    overrides = {
        "model": model,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
    }
    final_config = resolve_config(config, preset, overrides)

    # Create Experiment
    exp = exp_manager.create_experiment(
        model=final_config["model"]["name"],
        dataset=dataset_name,
        dataset_version=dataset_version,
        method=method,
    )

    console.print(f"[bold green]Created Experiment: {exp.experiment_id}[/bold green]")
    exp_manager.start_experiment(exp.experiment_id)

    # Register model in "training" status
    model_meta = model_registry.register(
        model_name=dataset_name,  # Usually model inherits dataset name for domain-specific FT
        base_model=final_config["model"]["name"],
        method=method,
        dataset_ref=f"{dataset_name}:{dataset_version}",
        experiment_id=exp.experiment_id,
        status="training",
    )

    start_time = time.time()

    try:
        # Create temp config for phase 1 trainer
        exp_dir = Path(".forgellm/experiments") / exp.experiment_id
        temp_config = exp_dir / "config.yaml"
        with open(temp_config, "w") as f:
            yaml.dump(final_config, f)

        console.print("[yellow]Starting training engine...[/yellow]")
        from forgellm.training.trainer import ForgeTrainer

        trainer = ForgeTrainer(str(temp_config))
        trainer.prepare_dataset(ds_info["train_path"], ds_info["val_path"])
        trainer.train()

        adapter_path = Path(model_meta["location"]) / "adapter"
        trainer.save_model(str(adapter_path))

        # Save metrics
        if hasattr(trainer, "trainer") and trainer.trainer.state.log_history:
            with open(exp_dir / "metrics.json", "w") as f:
                json.dump(trainer.trainer.state.log_history, f)

        duration = time.time() - start_time
        exp_manager.mark_completed(exp.experiment_id, duration)
        model_registry.update_status(
            model_meta["model_name"], model_meta["version"], "ready"
        )

        console.print(
            f"[bold green]Training completed in {duration:.1f}s![/bold green]"
        )

    except Exception as e:
        exp_manager.mark_failed(exp.experiment_id)
        model_registry.update_status(
            model_meta["model_name"], model_meta["version"], "failed"
        )
        console.print(f"[bold red]Training failed: {e!s}[/bold red]")
        raise typer.Exit(code=1)
