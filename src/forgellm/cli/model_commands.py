import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forgellm.models.registry import ModelRegistry

app = typer.Typer(help="Model registry commands.")
console = Console()
registry = ModelRegistry()


@app.command()
def list():
    """List all registered models."""
    models = registry.list_models()
    if not models:
        console.print("No models registered yet.")
        return

    table = Table(title="Registered Models")
    table.add_column("Model Name", style="cyan")
    table.add_column("Versions", style="magenta")

    for name in models:
        versions = registry.list_versions(name)
        v_list = ", ".join(v["version"] for v in versions)
        table.add_row(name, v_list)

    console.print(table)


@app.command()
def show(model_ref: str):
    """Show details for a model."""
    if ":" not in model_ref:
        model_name, version = model_ref, "v1"
    else:
        model_name, version = model_ref.split(":")

    info = registry.get_model(model_name, version)
    if not info:
        typer.secho(f"Model '{model_ref}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    table = Table(show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for k, v in info.items():
        table.add_row(str(k), str(v))

    console.print(Panel(table, title=f"Model: {model_ref}"))


@app.command()
def versions(name: str):
    """List all versions of a model."""
    versions_list = registry.list_versions(name)
    if not versions_list:
        typer.secho(f"Model '{name}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    table = Table(title=f"Model: {name}")
    table.add_column("Version", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Created", style="white")

    for v in versions_list:
        table.add_row(v["version"], v["status"].upper(), v["created_at"][:10])

    console.print(table)


# ==========================================
# MLflow Lifecycle Commands
# ==========================================

from forgellm.models.mlflow_registry import MLflowModelRegistry


@app.command(name="promote")
def promote_model(model_name: str, version: int):
    """Promote a registered model version to Production in MLflow."""
    mlflow_registry = MLflowModelRegistry("http://localhost:5000")
    try:
        mlflow_registry.promote_model(model_name, version)
        typer.secho(
            f"Successfully promoted {model_name} version {version} to Production!",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Failed to promote model: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="rollback")
def rollback_model(model_name: str, target_version: int):
    """Rollback Production to a specific older version in MLflow."""
    mlflow_registry = MLflowModelRegistry("http://localhost:5000")
    try:
        mlflow_registry.rollback_model(model_name, target_version)
        typer.secho(
            f"Successfully rolled back {model_name} to version {target_version}!",
            fg=typer.colors.YELLOW,
        )
    except Exception as e:
        typer.secho(f"Failed to rollback model: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="status")
def model_status(model_name: str):
    """Check the current Production version of a model in MLflow."""
    mlflow_registry = MLflowModelRegistry("http://localhost:5000")
    try:
        prod = mlflow_registry.get_production_version(model_name)
        if prod:
            console.print(
                Panel.fit(
                    f"[bold cyan]Model:[/bold cyan] {prod.name}\n"
                    f"[bold green]Production Version:[/bold green] v{prod.version}\n"
                    f"[bold magenta]Run ID:[/bold magenta] {prod.run_id}",
                    title="Current Production Deployment",
                )
            )
        else:
            typer.secho(
                f"No Production version found for {model_name}.", fg=typer.colors.YELLOW
            )
    except Exception as e:
        typer.secho(f"Failed to fetch status: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="export")
def export_model(
    model_ref: str = typer.Argument(
        ..., help="Model reference (e.g., customer-support:v7)"
    ),
    output_dir: str = typer.Option(
        "outputs/exported_model", help="Directory to save exported model"
    ),
):
    """Export and merge a fine-tuned LoRA adapter into a standalone model binary."""
    from forgellm.models.exporter import ModelExporter

    exporter = ModelExporter()
    console.print(f"[yellow]Merging LoRA adapter for '{model_ref}'...[/yellow]")
    try:
        path = exporter.export_merged_model(model_ref, output_dir)
        typer.secho(
            f"Successfully exported merged model to: {path}",
            fg=typer.colors.GREEN,
            bold=True,
        )
    except Exception as e:
        typer.secho(f"Export failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command(name="download")
def download_model(
    repo_id: str = typer.Argument(
        ..., help="HuggingFace Repository ID (e.g., Qwen/Qwen2.5-0.5B)"
    ),
):
    """Download open-weight base model snapshot from HuggingFace Hub directly to local cache."""
    from huggingface_hub import snapshot_download

    console.print(
        f"[yellow]Downloading model '{repo_id}' from HuggingFace Hub...[/yellow]"
    )
    try:
        local_path = snapshot_download(repo_id=repo_id)
        typer.secho(
            f"Successfully downloaded '{repo_id}' to cache: {local_path}",
            fg=typer.colors.GREEN,
            bold=True,
        )
    except Exception as e:
        typer.secho(f"Download failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
