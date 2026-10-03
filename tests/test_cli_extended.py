import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from forgellm.cli.main import app

runner = CliRunner()


# ==============================================================================
# Dataset CLI Commands
# ==============================================================================


def test_cli_dataset_validate_missing_file():
    result = runner.invoke(app, ["dataset", "validate", "non_existent.jsonl"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_cli_dataset_validate_valid_file(tmp_path):
    data_file = tmp_path / "valid.jsonl"
    data_file.write_text(
        json.dumps(
            {
                "messages": [
                    {"role": "user", "content": "hi"},
                    {"role": "assistant", "content": "hello"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["dataset", "validate", str(data_file)])
    assert result.exit_code == 0
    assert "PASSED" in result.output


def test_cli_dataset_validate_invalid_file(tmp_path):
    data_file = tmp_path / "invalid.jsonl"
    data_file.write_text(json.dumps({"wrong": "data"}) + "\n", encoding="utf-8")
    result = runner.invoke(app, ["dataset", "validate", str(data_file)])
    assert result.exit_code == 1
    assert "FAILED" in result.output


def test_cli_dataset_prepare_missing_file():
    result = runner.invoke(
        app, ["dataset", "prepare", "missing.jsonl", "--name", "test-ds"]
    )
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("forgellm.cli.dataset_commands.DatasetValidator")
@patch("forgellm.cli.dataset_commands.DatasetCleaner")
@patch("forgellm.dataset.formatter.DatasetFormatter")
@patch("forgellm.dataset.splitter.DatasetSplitter")
@patch("forgellm.cli.dataset_commands.registry")
def test_cli_dataset_prepare_success(
    mock_reg,
    mock_splitter_cls,
    mock_formatter_cls,
    mock_cleaner_cls,
    mock_val_cls,
    tmp_path,
):
    data_file = tmp_path / "raw.jsonl"
    data_file.write_text('{"messages": []}\n', encoding="utf-8")

    mock_val = MagicMock()
    mock_val.validate_file.return_value = MagicMock(status="PASSED", total=10)
    mock_val_cls.return_value = mock_val

    mock_formatter = MagicMock()
    mock_formatter_cls.return_value = mock_formatter

    mock_train_ds = MagicMock()
    mock_val_ds = MagicMock()

    def write_train(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"text":"a"}\n' * 8)

    def write_val(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write('{"text":"b"}\n' * 2)

    mock_train_ds.to_json.side_effect = write_train
    mock_val_ds.to_json.side_effect = write_val
    mock_splitter = MagicMock()
    mock_splitter.split.return_value = {
        "train": mock_train_ds,
        "validation": mock_val_ds,
    }
    mock_splitter_cls.return_value = mock_splitter

    mock_reg.register.return_value = {
        "dataset_name": "support-tickets",
        "version": "1.0",
        "training_examples": 8,
        "validation_examples": 2,
    }
    mock_reg.base_dir = tmp_path / "datasets"

    result = runner.invoke(
        app, ["dataset", "prepare", str(data_file), "--name", "support-tickets"]
    )
    assert result.exit_code == 0
    assert "Dataset preparation complete" in result.output


# ==============================================================================
# Experiment CLI Commands
# ==============================================================================


def test_cli_experiment_show_not_found():
    result = runner.invoke(app, ["experiment", "show", "non-existent-exp-999"])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("forgellm.cli.experiment_commands.manager")
def test_cli_experiment_show_success(mock_mgr):
    mock_exp = MagicMock()
    mock_exp.experiment_id = "EXP-000001"
    mock_exp.model = "Qwen/Qwen2.5-0.5B"
    mock_exp.dataset = "demo-dataset"
    mock_exp.dataset_version = "v1"
    mock_exp.method = "qlora"
    mock_exp.status = "completed"
    mock_exp.duration_seconds = 125.0
    mock_mgr.storage.get_experiment.return_value = mock_exp

    result = runner.invoke(app, ["experiment", "show", "EXP-000001"])
    assert result.exit_code == 0
    assert "EXP-000001" in result.output
    assert "COMPLETED" in result.output


# ==============================================================================
# Model CLI Commands
# ==============================================================================


@patch("forgellm.models.mlflow_registry.MLflowModelRegistry")
def test_cli_model_promote_success(mock_registry_cls):
    mock_reg = MagicMock()
    mock_registry_cls.return_value = mock_reg

    result = runner.invoke(app, ["model", "promote", "customer-support-llm", "2"])
    assert result.exit_code == 0
    assert (
        "Successfully promoted customer-support-llm version 2 to Production"
        in result.output
    )
    mock_reg.promote_model.assert_called_once_with("customer-support-llm", 2)


@patch("forgellm.models.mlflow_registry.MLflowModelRegistry")
def test_cli_model_promote_failure(mock_registry_cls):
    mock_reg = MagicMock()
    mock_reg.promote_model.side_effect = Exception("Model not registered")
    mock_registry_cls.return_value = mock_reg

    result = runner.invoke(app, ["model", "promote", "unregistered-llm", "1"])
    assert result.exit_code == 1
    assert "Failed to promote model" in result.output


@patch("forgellm.models.mlflow_registry.MLflowModelRegistry")
def test_cli_model_rollback_success(mock_registry_cls):
    mock_reg = MagicMock()
    mock_registry_cls.return_value = mock_reg

    result = runner.invoke(app, ["model", "rollback", "customer-support-llm", "1"])
    assert result.exit_code == 0
    assert "Successfully rolled back customer-support-llm to version 1" in result.output
    mock_reg.rollback_model.assert_called_once_with("customer-support-llm", 1)


@patch("forgellm.models.mlflow_registry.MLflowModelRegistry")
def test_cli_model_status_production_found(mock_registry_cls):
    mock_reg = MagicMock()
    mock_prod = MagicMock(name="customer-support-llm", version="3", run_id="run-789")
    mock_prod.name = "customer-support-llm"
    mock_prod.version = "3"
    mock_prod.run_id = "run-789"
    mock_reg.get_production_version.return_value = mock_prod
    mock_registry_cls.return_value = mock_reg

    result = runner.invoke(app, ["model", "status", "customer-support-llm"])
    assert result.exit_code == 0
    assert "customer-support-llm" in result.output
    assert "run-789" in result.output


@patch("forgellm.models.mlflow_registry.MLflowModelRegistry")
def test_cli_model_status_production_none(mock_registry_cls):
    mock_reg = MagicMock()
    mock_reg.get_production_version.return_value = None
    mock_registry_cls.return_value = mock_reg

    result = runner.invoke(app, ["model", "status", "customer-support-llm"])
    assert result.exit_code == 0
    assert "No Production version found" in result.output


def test_cli_model_export_missing_model():
    result = runner.invoke(app, ["model", "export", "non_existent_model:v99"])
    assert result.exit_code == 1
    assert "Export failed" in result.output


# ==============================================================================
# Chat CLI Commands
# ==============================================================================


def test_cli_chat_model_not_found():
    result = runner.invoke(app, ["chat", "ghost-model:v1"])
    assert result.exit_code == 1
    assert "not found" in result.output


@patch("forgellm.cli.chat_commands.registry")
def test_cli_chat_model_not_ready(mock_reg):
    mock_reg.get_model.return_value = {
        "status": "training",
        "base_model": "Qwen/Qwen2.5-0.5B",
    }
    result = runner.invoke(app, ["chat", "in-progress-model:v1"])
    assert result.exit_code == 1
    assert "is not ready" in result.output


# ==============================================================================
# Training CLI Commands
# ==============================================================================


@patch("forgellm.cli.training_commands.dataset_registry")
def test_cli_train_dataset_version_not_found(mock_ds_reg):
    mock_ds_reg.get_version_info.return_value = None
    result = runner.invoke(app, ["train", "--dataset", "missing-ds:v1"])
    assert result.exit_code == 1
    assert "not found" in result.output
