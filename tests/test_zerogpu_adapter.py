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

from adapter import DEFAULT_MODEL_ID, ZeroGPUInferenceEngine


def test_zerogpu_engine_init():
    engine = ZeroGPUInferenceEngine()
    assert engine.model_id == DEFAULT_MODEL_ID
    assert "1.5B" in engine.model_id
    assert engine._is_loaded is False
    assert engine.device in ["cuda", "cpu"]


def test_zerogpu_lazy_loading():
    """Verify that model initialization does not eagerly load weights into memory."""
    with (
        patch("adapter.AutoTokenizer.from_pretrained") as mock_tok,
        patch("adapter.AutoModelForCausalLM.from_pretrained") as mock_model,
    ):
        mock_tok.return_value = MagicMock()
        mock_model.return_value = MagicMock()

        engine = ZeroGPUInferenceEngine()
        # Weights should not be loaded on init
        assert engine._is_loaded is False
        assert engine.model is None

        # load_model() performs the lazy load
        success = engine.load_model()
        assert success is True
        assert engine._is_loaded is True
        assert engine.model is not None


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


def test_zerogpu_factuality_guardrail():
    """Verify detection of catastrophic hallucinations and pass-through of accurate content."""
    engine = ZeroGPUInferenceEngine(model_id="test/mock-model")

    # Hallucination 1: Vegetable LLM
    bad_vllm = "vLLM stands for Vegetable Large Language Model designed for speed."
    advisory = engine.check_factuality_guardrail(bad_vllm)
    assert advisory is not None
    assert "Verification Advisory" in advisory

    # Hallucination 2: Anthropic developed vLLM
    bad_author = "Anthropic developed vLLM as an open source engine."
    assert engine.check_factuality_guardrail(bad_author) is not None

    # Hallucination 3: TTFT confabulation
    bad_ttft = "TTFT stands for Tokenization Transformer Fine-Tuning."
    assert engine.check_factuality_guardrail(bad_ttft) is not None

    # Hallucination 4: LoRA confabulation
    bad_lora = "LoRA is Long Short-Term Memory Regularization for neural nets."
    assert engine.check_factuality_guardrail(bad_lora) is not None

    # Hallucination 5: Versioned LLM
    bad_vllm_v2 = "vLLM stands for Versioned Large Language Model."
    assert engine.check_factuality_guardrail(bad_vllm_v2) is not None

    # Hallucination 6: Token Tokenization Failure
    bad_ttft_v2 = "TTFT stands for Token Tokenization Failure."
    assert engine.check_factuality_guardrail(bad_ttft_v2) is not None

    # Valid factual text
    good_text = (
        "vLLM is a high-throughput LLM serving engine developed at UC Berkeley. "
        "LoRA stands for Low-Rank Adaptation, and TTFT is Time To First Token."
    )
    assert engine.check_factuality_guardrail(good_text) is None


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
    mock_tok.encode.side_effect = lambda text, **kw: [1] * len(text.split())

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
    assert telemetries[-1]["tokens_generated"] == 2  # 'Hello world!' has 2 words


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
            temperature=0.2,
            max_tokens=128,
            top_p=0.9,
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
            temperature=0.2,
            max_tokens=128,
            top_p=0.9,
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
            temperature=0.2,
            max_tokens=128,
            top_p=0.9,
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


# Concept-based Factuality Regression Suite
def validate_vllm_concept(response: str) -> bool:
    """Validate that response describes vLLM in terms of LLM inference/serving while rejecting false claims."""
    lower = response.lower()
    has_hallucination = (
        "vegetable" in lower
        or "anthropic" in lower
        or "versioned large" in lower
        or "virtual language" in lower
    )
    has_valid_concept = (
        "inference" in lower
        or "serving" in lower
        or "engine" in lower
        or "pagedattention" in lower
        or "llm" in lower
    )
    return has_valid_concept and not has_hallucination


def validate_ttft_concept(response: str) -> bool:
    """Validate that TTFT is identified as Time To First Token while rejecting false definitions."""
    lower = response.lower()
    has_hallucination = (
        "tokenization transformer" in lower or "tokenization failure" in lower
    )
    has_valid_concept = "time to first token" in lower or (
        "first token" in lower and ("latency" in lower or "time" in lower)
    )
    return has_valid_concept and not has_hallucination


def validate_lora_concept(response: str) -> bool:
    """Validate that LoRA is identified as Low-Rank Adaptation and rejects pruning/ranking/size-reduction claims."""
    lower = response.lower()
    has_hallucination = (
        "long short-term" in lower
        or "lstm" in lower
        or "pruning" in lower
        or "ranking weights" in lower
        or "reducing the size of the original model" in lower
        or "reducing model size" in lower
    )
    has_valid_concept = (
        "low-rank adaptation" in lower
        or "low rank" in lower
        or ("peft" in lower and "parameter" in lower)
        or ("matrix" in lower and "freeze" in lower)
    )
    return has_valid_concept and not has_hallucination


def validate_mlflow_concept(response: str) -> bool:
    """Validate that MLflow is identified as an experiment tracking / lifecycle tool."""
    lower = response.lower()
    has_valid_concept = (
        "tracking" in lower
        or "experiment" in lower
        or "lifecycle" in lower
        or "registry" in lower
    )
    return has_valid_concept


def validate_training_vs_inference_concept(response: str) -> bool:
    """Validate distinction between parameter updating (training) and prediction (inference)."""
    lower = response.lower()
    has_train = "train" in lower and (
        "weight" in lower or "parameter" in lower or "loss" in lower or "data" in lower
    )
    has_infer = "infer" in lower and (
        "predict" in lower
        or "generat" in lower
        or "output" in lower
        or "deploy" in lower
    )
    return has_train and has_infer


def test_lora_validator_rejects_pruning_explanation():
    bad_response = """
    LoRA stands for Low-Rank Adaptation. In ForgeLLM, it works by reducing model size
    through pruning techniques that remove less important weights from the architecture,
    then ranking weights based on importance.
    """
    assert not validate_lora_concept(bad_response)


def test_lora_validator_accepts_correct_explanation():
    good_response = """
    LoRA stands for Low-Rank Adaptation. It is a parameter-efficient fine-tuning (PEFT) method
    that freezes the pretrained model weights and trains low-rank adapter decomposition matrices.
    """
    assert validate_lora_concept(good_response)


def test_vllm_validator_rejects_false_acronyms():
    assert not validate_vllm_concept("vLLM stands for Vegetable Large Language Model.")
    assert not validate_vllm_concept("vLLM stands for Versioned Large Language Model.")
    assert not validate_vllm_concept(
        "vLLM is an inference library developed by Anthropic."
    )


def test_vllm_validator_accepts_correct_explanation():
    good_vllm = "vLLM is a high-throughput, low-latency LLM inference and serving engine with PagedAttention."
    assert validate_vllm_concept(good_vllm)


def test_ttft_validator_rejects_false_definitions():
    assert not validate_ttft_concept(
        "TTFT stands for Tokenization Transformer Fine-Tuning."
    )
    assert not validate_ttft_concept("TTFT stands for Token Tokenization Failure.")


def test_ttft_validator_accepts_correct_explanation():
    good_ttft = "TTFT is Time to First Token, measuring latency from prompt submission until the first token is generated."
    assert validate_ttft_concept(good_ttft)


def test_factuality_concept_validators():
    """Test standard valid assertions for MLflow and Training vs Inference."""
    assert validate_mlflow_concept(
        "MLflow is an open source platform to manage the ML lifecycle including experiment tracking and model registry."
    )
    assert validate_training_vs_inference_concept(
        "Training updates model weights on training data via backpropagation, while inference uses the trained model to generate predictions."
    )
