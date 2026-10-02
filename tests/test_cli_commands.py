from typer.testing import CliRunner

from forgellm.cli.main import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "ForgeLLM version" in result.output


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ForgeLLM CLI" in result.output


def test_cli_system_profile():
    result = runner.invoke(app, ["system", "profile"])
    assert result.exit_code == 0


def test_cli_experiment_list():
    result = runner.invoke(app, ["experiment", "list"])
    assert result.exit_code == 0


def test_cli_dataset_list():
    result = runner.invoke(app, ["dataset", "list"])
    assert result.exit_code == 0


def test_cli_model_list():
    result = runner.invoke(app, ["model", "list"])
    assert result.exit_code == 0
