import sys

import typer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Will import command groups as they are built
# from forgellm.cli import dataset_commands
# from forgellm.cli import training_commands
# from forgellm.cli import evaluation_commands
# from forgellm.cli import model_commands
# from forgellm.cli import system_commands
# from forgellm.cli import chat_commands
from forgellm.cli import (
    chat_commands,
    dataset_commands,
    evaluation_commands,
    experiment_commands,
    model_commands,
    system_commands,
    training_commands,
)

app = typer.Typer(
    name="forge",
    help="ForgeLLM CLI - Local LLM Fine-Tuning Platform",
    no_args_is_help=True,
)

app.add_typer(system_commands.app, name="system")
app.add_typer(dataset_commands.app, name="dataset")
app.add_typer(experiment_commands.app, name="experiment")
app.add_typer(model_commands.app, name="model")

app.command(name="train")(training_commands.run_train)
app.command(name="chat")(chat_commands.run_chat)
app.command(name="evaluate")(evaluation_commands.run_evaluate)


@app.command()
def version():
    """Show the ForgeLLM version."""
    from importlib.metadata import version as get_version

    try:
        ver = get_version("forgellm")
    except Exception:
        ver = "unknown (not installed as package)"
    typer.echo(f"ForgeLLM version: {ver}")


# We will add other commands here later

if __name__ == "__main__":
    app()
