import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forgellm.experiments.manager import ExperimentManager

app = typer.Typer(help="Experiment tracking and comparison commands.")
console = Console()
manager = ExperimentManager()

@app.command()
def list():
    """List all experiments."""
    experiments = manager.storage.list_experiments()
    if not experiments:
        console.print("No experiments found.")
        return
        
    table = Table(title="ForgeLLM Experiments")
    table.add_column("ID", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Dataset", style="blue")
    table.add_column("Status", style="green")
    table.add_column("Created", style="white")
    
    for exp in experiments:
        table.add_row(
            exp.experiment_id,
            exp.model,
            f"{exp.dataset}:{exp.dataset_version}",
            exp.status.upper(),
            exp.created_at[:10]
        )
        
    console.print(table)

@app.command()
def show(experiment_id: str):
    """Show details for an experiment."""
    exp = manager.storage.get_experiment(experiment_id)
    if not exp:
        typer.secho(f"Experiment {experiment_id} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    output = [
        "[bold cyan]ForgeLLM Experiment[/bold cyan]\n",
        f"[bold]{exp.experiment_id}[/bold]",
        "────────────────────────────\n",
        f"[bold]Model:[/bold]          {exp.model}",
        f"[bold]Dataset:[/bold]        {exp.dataset}:{exp.dataset_version}",
        f"[bold]Method:[/bold]         {exp.method}\n",
        f"[bold]Status:[/bold]         {exp.status.upper()}\n"
    ]
    
    if exp.duration_seconds:
        mins = int(exp.duration_seconds // 60)
        secs = int(exp.duration_seconds % 60)
        output.append(f"[bold]Training time:[/bold]  {mins}m {secs}s\n")
        
    output.append(f"[bold]Git Commit:[/bold]     {exp.git_commit}")
    output.append(f"[bold]GPU:[/bold]            {exp.gpu}")
    
    console.print(Panel("\n".join(output)))

@app.command()
def compare(exp1: str, exp2: str):
    """Compare two experiments."""
    e1 = manager.storage.get_experiment(exp1)
    e2 = manager.storage.get_experiment(exp2)
    
    if not e1:
        typer.secho(f"Experiment {exp1} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    if not e2:
        typer.secho(f"Experiment {exp2} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    table = Table(title="Experiment Comparison")
    table.add_column("Metric", style="cyan")
    table.add_column(e1.experiment_id, style="magenta")
    table.add_column(e2.experiment_id, style="green")
    
    table.add_row("Model", e1.model, e2.model)
    table.add_row("Dataset", f"{e1.dataset}:{e1.dataset_version}", f"{e2.dataset}:{e2.dataset_version}")
    table.add_row("Method", e1.method, e2.method)
    table.add_row("Status", e1.status.upper(), e2.status.upper())
    
    if e1.duration_seconds and e2.duration_seconds:
        t1 = f"{int(e1.duration_seconds // 60)}m {int(e1.duration_seconds % 60)}s"
        t2 = f"{int(e2.duration_seconds // 60)}m {int(e2.duration_seconds % 60)}s"
        table.add_row("Training Time", t1, t2)
        
    console.print(table)
