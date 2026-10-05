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


@patch("adapter.TextIteratorStreamer")
def test_zerogpu_generate_stream_mock(mock_streamer_cls):
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

    mock_streamer = MagicMock()
    mock_streamer.__iter__.return_value = iter(["Hello", " world", "!"])
    mock_streamer_cls.return_value = mock_streamer

    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_model.generate = MagicMock()

    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")
    engine.tokenizer = mock_tok
    engine.model = mock_model
    engine._is_loaded = True

    messages = [{"role": "user", "content": "Hi"}]
    chunks = []
    telemetries = []

    for text, telem in engine.generate_stream(
        messages=messages,
        max_new_tokens=10,
        temperature=0.0,
    ):
        chunks.append(text)
        telemetries.append(telem)

    assert len(chunks) == 3
    assert chunks[-1] == "Hello world!"
    assert "tokens_per_sec" in telemetries[-1]
    assert "latency_sec" in telemetries[-1]
    assert "ttft_sec" in telemetries[-1]


def test_zerogpu_generate_stream_unloaded_failure():
    engine = ZeroGPUInferenceEngine(model_id="invalid/non-existent-model")
    with patch.object(engine, "load_model", return_value=False):
        results = list(engine.generate_stream([{"role": "user", "content": "Hello"}]))
        assert len(results) == 1
        assert "Error: Model failed to load" in results[0][0]
