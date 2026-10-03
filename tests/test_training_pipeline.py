import json
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import torch

from forgellm.training.config import QuantizationConfig, TrainingConfig
from forgellm.training.dpo_trainer import ForgeDPOTrainer
from forgellm.training.quantization import get_quantization_config
from forgellm.training.trainer import ForgeTrainer

# ==============================================================================
# Quantization Tests
# ==============================================================================


def test_quantization_disabled():
    cfg = QuantizationConfig(enabled=False)
    assert get_quantization_config(cfg) is None


@patch("forgellm.training.quantization.torch.cuda.is_available", return_value=False)
def test_quantization_cuda_unavailable_error(mock_cuda):
    cfg = QuantizationConfig(enabled=True, bits=4)
    with pytest.raises(
        RuntimeError, match="QLoRA requires a compatible CUDA/bitsandbytes environment"
    ):
        get_quantization_config(cfg)


@patch("forgellm.training.quantization.torch.cuda.is_available", return_value=True)
def test_quantization_bitsandbytes_missing_error(mock_cuda):
    cfg = QuantizationConfig(enabled=True, bits=4)
    with patch.dict("sys.modules", {"bitsandbytes": None}), pytest.raises(RuntimeError):
        get_quantization_config(cfg)


@patch("forgellm.training.quantization.torch.cuda.is_available", return_value=True)
def test_quantization_4bit_success(mock_cuda):
    cfg = QuantizationConfig(enabled=True, bits=4)
    mock_bnb = MagicMock()
    with patch.dict("sys.modules", {"bitsandbytes": mock_bnb}):
        q_config = get_quantization_config(cfg)
        assert q_config is not None
        assert q_config.load_in_4bit is True
        assert q_config.bnb_4bit_quant_type == "nf4"
        assert q_config.bnb_4bit_use_double_quant is True


@patch("forgellm.training.quantization.torch.cuda.is_available", return_value=True)
def test_quantization_8bit_success(mock_cuda):
    cfg = QuantizationConfig(enabled=True, bits=8)
    mock_bnb = MagicMock()
    with patch.dict("sys.modules", {"bitsandbytes": mock_bnb}):
        q_config = get_quantization_config(cfg)
        assert q_config is not None
        assert q_config.load_in_8bit is True


@patch("forgellm.training.quantization.torch.cuda.is_available", return_value=True)
def test_quantization_invalid_bits(mock_cuda):
    cfg = QuantizationConfig(enabled=True, bits=16)
    mock_bnb = MagicMock()
    with (
        patch.dict("sys.modules", {"bitsandbytes": mock_bnb}),
        pytest.raises(ValueError, match="Unsupported quantization bits: 16"),
    ):
        get_quantization_config(cfg)


# ==============================================================================
# LoRA Config Tests
# ==============================================================================


def test_get_lora_config_success():
    from forgellm.training.config import LoraConfig
    from forgellm.training.lora import get_lora_config

    mock_peft_lora = MagicMock()
    with patch("forgellm.training.lora.PeftLoraConfig", mock_peft_lora):
        cfg = LoraConfig(r=16, alpha=32, dropout=0.05)
        res = get_lora_config(cfg)
        mock_peft_lora.assert_called_once_with(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules=[
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            bias="none",
            task_type="CAUSAL_LM",
        )


def test_get_lora_config_peft_missing():
    from forgellm.training.config import LoraConfig
    from forgellm.training.lora import get_lora_config

    with patch("forgellm.training.lora.PeftLoraConfig", None):
        cfg = LoraConfig(r=8, alpha=16)
        with pytest.raises(RuntimeError, match="peft is not installed"):
            get_lora_config(cfg)


# ==============================================================================
# ForgeDPOTrainer Tests
# ==============================================================================


def test_dpo_trainer_init():
    trainer = ForgeDPOTrainer(
        model_name="Qwen/Qwen2.5-0.5B", output_dir="outputs/dpo_test"
    )
    assert trainer.model_name == "Qwen/Qwen2.5-0.5B"
    assert trainer.output_dir == "outputs/dpo_test"


def test_dpo_trainer_missing_dataset_error():
    trainer = ForgeDPOTrainer(output_dir="outputs/dpo_test")
    with pytest.raises(FileNotFoundError, match="DPO dataset not found"):
        trainer.train_dpo("non_existent_dataset.jsonl")


@patch("forgellm.training.dpo_trainer.DPOConfig")
@patch("forgellm.training.dpo_trainer.Dataset")
@patch("forgellm.training.dpo_trainer.ModelLoader")
@patch("forgellm.training.dpo_trainer.DPOTrainer")
def test_dpo_trainer_success(
    mock_dpo_trainer_cls,
    mock_loader_cls,
    mock_dataset_cls,
    mock_dpo_config_cls,
    tmp_path,
):

    dataset_file = tmp_path / "dpo_pairs.jsonl"
    dataset_file.write_text(
        '{"prompt": "hi", "chosen": "hello", "rejected": "bye"}\n', encoding="utf-8"
    )

    mock_loader = MagicMock()
    mock_model = MagicMock()
    mock_tok = MagicMock()
    mock_loader.load_model.return_value = mock_model
    mock_loader.load_tokenizer.return_value = mock_tok
    mock_loader_cls.return_value = mock_loader

    mock_trainer = MagicMock()
    mock_dpo_trainer_cls.return_value = mock_trainer

    out_dir = str(tmp_path / "dpo_output")
    trainer = ForgeDPOTrainer(model_name="Qwen/Qwen2.5-0.5B", output_dir=out_dir)

    result_path = trainer.train_dpo(
        dataset_path=str(dataset_file),
        num_epochs=2,
        learning_rate=1e-5,
        beta=0.05,
    )

    assert result_path == out_dir
    mock_trainer.train.assert_called_once()
    mock_trainer.save_model.assert_called_once_with(out_dir)
    mock_tok.save_pretrained.assert_called_once_with(out_dir)


# ==============================================================================
# ForgeTrainer Unit Tests
# ==============================================================================


@pytest.fixture
def sample_config_yaml(tmp_path):
    config_dict = {
        "model": {"name": "Qwen/Qwen2.5-0.5B", "model_version": "v1.0"},
        "dataset": {"name": "sample-ds", "version": "1.0", "max_seq_length": 512},
        "training": {
            "output_dir": str(tmp_path / "trainer_out"),
            "num_train_epochs": 1,
            "per_device_train_batch_size": 2,
            "per_device_eval_batch_size": 2,
            "gradient_accumulation_steps": 2,
            "learning_rate": 0.0002,
            "seed": 42,
            "mlflow_tracking_uri": "http://localhost:5000",
            "experiment_name": "Test_Experiment",
        },
        "quantization": {"enabled": False, "bits": 4},
        "lora": {"r": 8, "lora_alpha": 16, "target_modules": ["q_proj", "v_proj"]},
    }
    import yaml

    cfg_file = tmp_path / "config.yaml"
    with open(cfg_file, "w", encoding="utf-8") as f:
        yaml.dump(config_dict, f)
    return str(cfg_file)


def test_forge_trainer_init(sample_config_yaml):
    trainer = ForgeTrainer(sample_config_yaml)
    assert trainer.config.model.name == "Qwen/Qwen2.5-0.5B"
    assert trainer.config.training.seed == 42
    assert trainer.train_dataset is None
    assert trainer.eval_dataset is None


def test_forge_trainer_save_run_metadata(sample_config_yaml, tmp_path):
    trainer = ForgeTrainer(sample_config_yaml)
    trainer._save_run_metadata()

    metadata_path = tmp_path / "trainer_out" / "run_metadata.json"
    assert metadata_path.exists()

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "timestamp" in data
    assert "git_commit" in data
    assert data["config"]["model"]["name"] == "Qwen/Qwen2.5-0.5B"


@patch("torch.cuda.is_available", return_value=True)
@patch("torch.cuda.get_device_properties")
def test_forge_trainer_oom_guardrails_low_vram(
    mock_props, mock_cuda, sample_config_yaml
):
    # Mock VRAM = 4GB (constrained)
    mock_dev_props = MagicMock()
    mock_dev_props.total_memory = 4 * 1024 * 1024 * 1024
    mock_props.return_value = mock_dev_props

    trainer = ForgeTrainer(sample_config_yaml)
    trainer._apply_oom_guardrails()

    # Should automatically reduce batch size to 1 and enable 4-bit QLoRA
    assert trainer.config.training.per_device_train_batch_size == 1
    assert trainer.config.training.gradient_accumulation_steps >= 4
    assert trainer.config.quantization.enabled is True
    assert trainer.config.quantization.bits == 4


@patch("torch.cuda.is_available", return_value=True)
@patch("torch.cuda.get_device_properties")
def test_forge_trainer_oom_guardrails_high_vram(
    mock_props, mock_cuda, sample_config_yaml
):
    # Mock VRAM = 24GB (unconstrained RTX 4090)
    mock_dev_props = MagicMock()
    mock_dev_props.total_memory = 24 * 1024 * 1024 * 1024
    mock_props.return_value = mock_dev_props

    trainer = ForgeTrainer(sample_config_yaml)
    trainer._apply_oom_guardrails()

    # Settings should remain unchanged
    assert trainer.config.training.per_device_train_batch_size == 2
    assert trainer.config.quantization.enabled is False


def test_forge_trainer_prune_old_checkpoints(sample_config_yaml, tmp_path):
    trainer = ForgeTrainer(sample_config_yaml)
    out_dir = tmp_path / "trainer_out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Create 5 checkpoint directories
    for step in [100, 200, 300, 400, 500]:
        (out_dir / f"checkpoint-{step}").mkdir()

    trainer._prune_old_checkpoints(max_to_keep=3)

    remaining = sorted(os.listdir(out_dir))
    assert remaining == ["checkpoint-300", "checkpoint-400", "checkpoint-500"]


@patch("forgellm.training.trainer.mlflow")
def test_forge_trainer_save_model(mock_mlflow, sample_config_yaml, tmp_path):
    trainer = ForgeTrainer(sample_config_yaml)
    trainer.active_run_id = "test-run-123"

    mock_trainer_obj = MagicMock()
    trainer.trainer = mock_trainer_obj

    adapter_path = str(tmp_path / "trainer_out" / "adapter")
    trainer.save_model(adapter_path)

    mock_trainer_obj.model.save_pretrained.assert_called_once_with(adapter_path)
    mock_trainer_obj.processing_class.save_pretrained.assert_called_once()
    mock_mlflow.set_tracking_uri.assert_called_once_with("http://localhost:5000")
