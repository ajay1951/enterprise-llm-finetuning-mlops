"""Unit and Integration Tests for ForgeLLM Hugging Face ZeroGPU Adapter."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import torch

# Add deployments path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__), "..", "deployments", "huggingface_zerogpu"
        )
    ),
)

from adapter import ZeroGPUInferenceEngine


def test_zerogpu_engine_init():
    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")
    assert engine.model_id == "test/mock-model"
    assert engine._is_loaded is False
    assert engine.device in ["cuda", "cpu"]


@patch("adapter.AutoTokenizer.from_pretrained")
@patch("adapter.AutoModelForCausalLM.from_pretrained")
def test_zerogpu_load_model_success(
    mock_model_from_pretrained, mock_tok_from_pretrained
):
    mock_tok = MagicMock()
    mock_tok_from_pretrained.return_value = mock_tok

    mock_model = MagicMock()
    mock_model_from_pretrained.return_value = mock_model

    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")
    success = engine.load_model()

    assert success is True
    assert engine._is_loaded is True
    assert engine.tokenizer == mock_tok
    assert engine.model == mock_model
    assert mock_model.eval.called


@patch("adapter.AutoTokenizer.from_pretrained", side_effect=Exception("Hub timeout"))
def test_zerogpu_load_model_failure(mock_tok_from_pretrained):
    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")
    success = engine.load_model()

    assert success is False
    assert engine._is_loaded is False


def test_zerogpu_generate_stream_mock():
    mock_tok = MagicMock()
    mock_tok.chat_template = True
    mock_tok.apply_chat_template.return_value = (
        "<|im_start|>user\nHi<|im_end|>\n<|im_start|>assistant\n"
    )
    mock_tok.return_value = {
        "input_ids": torch.tensor([[1, 2]]),
        "attention_mask": torch.tensor([[1, 1]]),
    }
    mock_tok.eos_token_id = 999
    mock_tok.decode.side_effect = lambda ids, **kw: f"Token-{ids[-1]}"

    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")

    # Mock forward output
    mock_output_1 = MagicMock()
    mock_output_1.logits = torch.tensor([[[0.1, 0.9]]])  # argmax is 1
    mock_output_1.past_key_values = MagicMock()

    mock_output_2 = MagicMock()
    mock_output_2.logits = torch.tensor([[[0.1, 0.0]]])  # token 999 (EOS)
    mock_output_2.past_key_values = MagicMock()

    mock_model.side_effect = [mock_output_1, mock_output_2]

    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")
    engine.tokenizer = mock_tok
    engine.model = mock_model
    engine._is_loaded = True

    messages = [{"role": "user", "content": "Hi"}]
    chunks = []
    telemetries = []

    for text, telem in engine.generate_stream(
        messages=messages,
        max_new_tokens=2,
        temperature=0.0,
    ):
        chunks.append(text)
        telemetries.append(telem)

    assert len(chunks) >= 1
    assert "tokens_per_sec" in telemetries[-1]
    assert "latency_sec" in telemetries[-1]
    assert "ttft_sec" in telemetries[-1]


def test_zerogpu_generate_stream_unloaded_failure():
    engine = ZeroGPUInferenceEngine(model_id="invalid/non-existent-model")
    with patch.object(engine, "load_model", return_value=False):
        results = list(engine.generate_stream([{"role": "user", "content": "Hello"}]))
        assert len(results) == 1
        assert "Error: Model failed to load" in results[0][0]
