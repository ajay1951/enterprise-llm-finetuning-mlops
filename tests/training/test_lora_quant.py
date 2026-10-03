from unittest.mock import MagicMock, patch

import pytest

from forgellm.training.config import LoraConfig, QuantizationConfig
from forgellm.training.lora import get_lora_config
from forgellm.training.quantization import get_quantization_config


def test_lora_config_generation():
    lora_cfg = LoraConfig(r=8, alpha=16, dropout=0.1)
    with patch(
        "forgellm.training.lora.PeftLoraConfig",
        MagicMock(side_effect=lambda **kwargs: MagicMock(**kwargs)),
    ):
        peft_cfg = get_lora_config(lora_cfg)

        assert peft_cfg.r == 8
        assert peft_cfg.lora_alpha == 16
        assert peft_cfg.lora_dropout == 0.1
        assert "q_proj" in peft_cfg.target_modules


def test_quantization_disabled():
    q_cfg = QuantizationConfig(enabled=False, bits=4)
    res = get_quantization_config(q_cfg)
    assert res is None


def test_quantization_cuda_unavailable():
    q_cfg = QuantizationConfig(enabled=True, bits=4)
    with patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(RuntimeError) as exc:
            get_quantization_config(q_cfg)
        assert "QLoRA requires a compatible CUDA" in str(exc.value)
