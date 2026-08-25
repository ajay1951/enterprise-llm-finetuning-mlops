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
        table.add_row(
            v["version"], 
            v["status"].upper(), 
            v["created_at"][:10]
        )
        
    console.print(table)
