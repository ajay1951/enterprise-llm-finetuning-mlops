import typer
import os
from typing import Optional
from rich.console import Console

from forgellm.models.registry import ModelRegistry
from forgellm.models.loader import ModelLoader
from forgellm.inference.generator import ForgeGenerator
from forgellm.training.quantization import get_quantization_config
from peft import PeftModel

console = Console()
registry = ModelRegistry()

def run_chat(
    model_ref: str = typer.Argument(..., help="Model reference (e.g., customer-support:v1)"),
    temperature: float = typer.Option(0.7, help="Generation temperature"),
    max_new_tokens: int = typer.Option(256, help="Maximum new tokens")
):
    """Start an interactive chat session with a registered model."""
    if ":" not in model_ref:
        model_name, version = model_ref, "v1"
    else:
        model_name, version = model_ref.split(":")
        
    info = registry.get_model(model_name, version)
    if not info:
        typer.secho(f"Model '{model_ref}' not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    if info.get("status") != "ready":
        typer.secho(f"Model '{model_ref}' is not ready (Status: {info.get('status')}).", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    adapter_path = os.path.join(info["location"], "adapter")
    
    console.print(f"[bold cyan]ForgeLLM Chat[/bold cyan]")
    console.print(f"Model: {model_ref}\n")
    console.print("[yellow]Loading model... (this may take a few seconds)[/yellow]")
    
    loader = ModelLoader(info["base_model"])
    tokenizer = loader.load_tokenizer()
    
    # Force 4-bit config to avoid OOM by default
    import torch
    from transformers import BitsAndBytesConfig
    q_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=False,
    )
    
    base_model = loader.load_model(quantization_config=q_config)
    model = PeftModel.from_pretrained(base_model, adapter_path)
    
    generator = ForgeGenerator(model, tokenizer)
    generator.chat_loop()
