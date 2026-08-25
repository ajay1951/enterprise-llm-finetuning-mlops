import typer
from forgellm.hardware.detector import HardwareDetector
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Hardware detection and profiling commands.")
console = Console()

@app.command()
def info():
    """Display system hardware and environment information."""
    profile = HardwareDetector.detect()
    
    output = [
        "[bold cyan]ForgeLLM Hardware[/bold cyan]\n",
        f"[bold]OS:[/bold] {profile.os_name} ({profile.cpu_arch})",
        f"[bold]RAM:[/bold] {profile.ram_gb} GB\n",
        f"[bold]PyTorch:[/bold] {profile.pytorch_version}",
        f"[bold]CUDA Available:[/bold] {'[green]YES[/green]' if profile.cuda_available else '[red]NO[/red]'}",
        f"[bold]CUDA Version:[/bold] {profile.cuda_version}",
        f"[bold]bitsandbytes:[/bold] {profile.bitsandbytes_version}\n"
    ]
    
    output.append(f"[bold]GPU Count:[/bold] {profile.gpu_count}")
    for i in range(profile.gpu_count):
        output.append(f"[bold]GPU {i}:[/bold] {profile.gpu_names[i]} ({profile.vram_gb[i]} GB VRAM)")
        
    console.print(Panel("\n".join(output), title="System Info"))

@app.command()
def profile():
    """Profile the system to see if it supports QLoRA."""
    profile = HardwareDetector.detect()
    
    qlora_supported = profile.cuda_available and profile.bitsandbytes_version != "Not installed"
    
    output = [
        "[bold cyan]ForgeLLM Hardware Profile[/bold cyan]\n",
        f"[bold]Detected GPU:[/bold] {profile.gpu_names[0] if profile.gpu_count > 0 else 'None'}",
        f"[bold]VRAM:[/bold] {profile.vram_gb[0] if profile.gpu_count > 0 else 0} GB\n",
        f"[bold]CUDA:[/bold] {'Available' if profile.cuda_available else 'Unavailable'}",
        f"[bold]bitsandbytes:[/bold] {'Available' if profile.bitsandbytes_version != 'Not installed' else 'Unavailable'}\n",
        f"[bold]QLoRA:[/bold] {'[green]Supported[/green]' if qlora_supported else '[red]Unsupported[/red]'}"
    ]
    
    console.print(Panel("\n".join(output), title="Hardware Profiler"))
