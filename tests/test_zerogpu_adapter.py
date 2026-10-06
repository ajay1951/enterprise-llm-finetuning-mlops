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
    mock_model.to.return_value = mock_model
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


def test_ui_clear_chat():
    from app import clear_chat

    history, status, ttft, latency, tokens, throughput = clear_chat()
    assert history == []
    assert status == "🟢 Ready"
    assert ttft == "—"
    assert latency == "—"
    assert tokens == "—"
    assert throughput == "—"


def test_ui_chat_and_telemetry_empty():
    from app import chat_and_telemetry

    results = list(
        chat_and_telemetry(
            message="   ",
            history=[],
            system_prompt="",
            temperature=0.7,
            max_tokens=128,
            top_p=0.8,
        )
    )
    assert len(results) == 1
    hist, status, ttft, _lat, _tok, _spd = results[0]
    assert hist == []
    assert "Ready" in status
    assert ttft == "—"


@patch("app.engine.generate_stream")
def test_ui_chat_and_telemetry_success(mock_gen_stream):
    from app import chat_and_telemetry

    mock_gen_stream.return_value = iter(
        [
            (
                "Hello",
                {
                    "ttft_sec": 0.35,
                    "latency_sec": 0.35,
                    "tokens_generated": 1,
                    "tokens_per_sec": 2.86,
                },
            ),
            (
                "Hello world",
                {
                    "ttft_sec": 0.35,
                    "latency_sec": 0.85,
                    "tokens_generated": 2,
                    "tokens_per_sec": 2.35,
                },
            ),
        ]
    )

    results = list(
        chat_and_telemetry(
            message="Hi",
            history=[],
            system_prompt="You are helpful.",
            temperature=0.7,
            max_tokens=128,
            top_p=0.8,
        )
    )

    # 2 streaming steps + 1 final complete step = 3 steps
    assert len(results) == 3

    # Step 1: Streaming
    hist_1, status_1, ttft_1, lat_1, tok_1, spd_1 = results[0]
    assert hist_1[-1]["content"] == "Hello"
    assert status_1 == "⚡ Generating..."
    assert ttft_1 == "0.35 s"
    assert lat_1 == "0.35 s"
    assert tok_1 == "1"
    assert spd_1 == "2.9 tok/s"

    # Step 3: Complete
    hist_3, status_3, ttft_3, lat_3, tok_3, spd_3 = results[2]
    assert hist_3[-1]["content"] == "Hello world"
    assert status_3 == "✓ Complete"
    assert ttft_3 == "0.35 s"
    assert lat_3 == "0.85 s"
    assert tok_3 == "2"
    assert spd_3 == "2.4 tok/s"


@patch("app.engine.generate_stream", side_effect=RuntimeError("CUDA OOM"))
def test_ui_chat_and_telemetry_error(mock_gen_stream):
    from app import chat_and_telemetry

    results = list(
        chat_and_telemetry(
            message="Trigger crash",
            history=[],
            system_prompt="",
            temperature=0.7,
            max_tokens=128,
            top_p=0.8,
        )
    )

    assert len(results) == 1
    _hist, status, ttft, lat, tok, spd = results[0]
    assert "❌ Error" in status
    assert "CUDA OOM" in status
    assert ttft == "—"
    assert lat == "—"
    assert tok == "—"
    assert spd == "—"
