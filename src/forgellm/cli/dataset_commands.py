import os

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forgellm.dataset.cleaner import DatasetCleaner
from forgellm.dataset.registry import DatasetRegistry
from forgellm.dataset.validator import DatasetValidator

app = typer.Typer(help="Dataset management and preparation commands.")
console = Console()
registry = DatasetRegistry()


@app.command()
def validate(file: str):
    """Validate a dataset file."""
    if not os.path.exists(file):
        typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    validator = DatasetValidator()
    result = validator.validate_file(file)

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("File", file)
    table.add_row("Examples", str(result.total))
    table.add_row("Valid", str(result.valid))
    table.add_row("Invalid", str(result.invalid))
    table.add_row("Duplicates", str(result.duplicates))

    console.print(Panel(table, title="ForgeLLM Dataset Validation"))

    if result.status == "PASSED":
        typer.secho("Status: PASSED", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("Status: FAILED", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)


@app.command()
def prepare(
    file: str,
    name: str = typer.Option(..., help="Name of the dataset"),
    validation_split: float = typer.Option(0.1, help="Fraction of data for validation"),
    seed: int = typer.Option(42, help="Random seed for splitting"),
):
    """Clean, format, split and register a dataset."""
    if not os.path.exists(file):
        typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    console.print("[yellow]Validating...[/yellow]")
    validator = DatasetValidator()
    result = validator.validate_file(file)
    if result.status != "PASSED":
        typer.secho("Validation failed. Fix the dataset first.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    console.print("[yellow]Cleaning...[/yellow]")
    cleaner = DatasetCleaner()
    cleaned_file = file.replace(".jsonl", "_cleaned.jsonl")
    if cleaned_file == file:
        cleaned_file = file + "_cleaned.jsonl"
    cleaner.clean(file, cleaned_file)

    from forgellm.dataset.formatter import DatasetFormatter

    console.print("[yellow]Formatting...[/yellow]")
    formatter = DatasetFormatter()
    dataset = formatter.format_dataset(cleaned_file)

    console.print("[yellow]Splitting...[/yellow]")
    from forgellm.dataset.splitter import DatasetSplitter

    splitter = DatasetSplitter(validation_split=validation_split, seed=seed)
    split_dataset = splitter.split(dataset)

    # Save the splits to temporary files
    import tempfile

    temp_dir = tempfile.mkdtemp()
    train_file = os.path.join(temp_dir, "train.jsonl")
    val_file = os.path.join(temp_dir, "val.jsonl")

    split_dataset["train"].to_json(train_file)
    split_dataset["validation"].to_json(val_file)

    total_examples = result.total

    # We need to count lines in train and val
    def count_lines(filepath):
        with open(filepath, "r") as f:
            return sum(1 for _ in f)

    train_count = count_lines(train_file)
    val_count = count_lines(val_file) if val_file else 0

    console.print("[yellow]Registering dataset...[/yellow]")
    metadata = registry.register(
        dataset_name=name,
        source_path=file,
        train_path=train_file,
        val_path=val_file if val_file else "",
        total_examples=total_examples,
        training_examples=train_count,
        validation_examples=val_count,
        seed=seed,
    )

    output = [
        "[bold green]Dataset preparation complete.[/bold green]\n",
        f"[bold]Dataset ID:[/bold] {metadata['dataset_name']}",
        f"[bold]Version:[/bold] {metadata['version']}\n",
        f"[bold]Training examples:[/bold] {metadata['training_examples']}",
        f"[bold]Validation examples:[/bold] {metadata['validation_examples']}\n",
        f"[bold]Location:[/bold] {registry.base_dir / name / metadata['version']}",
    ]

    console.print("\n".join(output))


@app.command()
def list():
    """List all registered datasets."""
    datasets = registry.list_datasets()
    if not datasets:
        console.print("No datasets registered yet.")
        return

    table = Table(title="Registered Datasets")
    table.add_column("Dataset ID", style="cyan")
    table.add_column("Versions", style="magenta")

    for name in datasets:
        versions = registry.list_versions(name)
        v_list = ", ".join(v["version"] for v in versions)
        table.add_row(name, v_list)

    console.print(table)


@app.command()
def info(name: str):
    """Show info for a dataset."""
    versions = registry.list_versions(name)
    if not versions:
        typer.secho(f"Dataset '{name}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    latest = versions[-1]

    table = Table(show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for k, v in latest.items():
        table.add_row(str(k), str(v))

    console.print(Panel(table, title=f"Dataset: {name} (Latest: {latest['version']})"))


@app.command()
def versions(name: str):
    """List all versions of a dataset."""
    versions_list = registry.list_versions(name)
    if not versions_list:
        typer.secho(f"Dataset '{name}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    table = Table(title=f"Dataset: {name}")
    table.add_column("Version", style="cyan")
    table.add_column("Examples", style="magenta")
    table.add_column("Created", style="green")

    for v in versions_list:
        table.add_row(v["version"], str(v["total_examples"]), v["created_at"][:10])

    console.print(table)
