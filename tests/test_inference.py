import warnings
from unittest.mock import MagicMock, patch

import pytest
import torch

from forgellm.inference.generator import ForgeGenerator
from forgellm.models.loader import ModelLoader

# ==============================================================================
# ModelLoader Tests
# ==============================================================================


@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_cpu_device_warning(mock_cuda):
    with pytest.warns(UserWarning, match="CUDA is not available"):
        loader = ModelLoader("test-model/qwen-mini")
    assert loader.device == "cpu"
    assert loader.cuda_available is False


@patch(
    "forgellm.models.loader.torch.cuda.get_device_name", return_value="NVIDIA RTX 4090"
)
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=True)
def test_model_loader_cuda_device(mock_cuda, mock_device_name):
    loader = ModelLoader("test-model/qwen-mini")
    assert loader.device == "cuda"
    assert loader.cuda_available is True


@patch("forgellm.models.loader.AutoTokenizer.from_pretrained")
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_load_tokenizer_assigns_pad_token(mock_cuda, mock_from_pretrained):
    mock_tok = MagicMock()
    mock_tok.pad_token = None
    mock_tok.eos_token = "<|endoftext|>"
    mock_from_pretrained.return_value = mock_tok

    loader = ModelLoader("test-model/qwen-mini")
    tokenizer = loader.load_tokenizer()

    assert tokenizer.pad_token == "<|endoftext|>"
    mock_from_pretrained.assert_called_once_with(
        "test-model/qwen-mini", trust_remote_code=True
    )


@patch("forgellm.models.loader.AutoTokenizer.from_pretrained")
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_load_tokenizer_keeps_existing_pad_token(
    mock_cuda, mock_from_pretrained
):
    mock_tok = MagicMock()
    mock_tok.pad_token = "<|pad|>"
    mock_tok.eos_token = "<|endoftext|>"
    mock_from_pretrained.return_value = mock_tok

    loader = ModelLoader("test-model/qwen-mini")
    tokenizer = loader.load_tokenizer()

    assert tokenizer.pad_token == "<|pad|>"


@patch(
    "forgellm.models.loader.AutoTokenizer.from_pretrained",
    side_effect=Exception("Network error"),
)
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_load_tokenizer_failure(mock_cuda, mock_from_pretrained):
    loader = ModelLoader("test-model/qwen-mini")
    with pytest.raises(
        RuntimeError, match="Failed to load tokenizer for test-model/qwen-mini"
    ):
        loader.load_tokenizer()


@patch("forgellm.models.loader.AutoModelForCausalLM.from_pretrained")
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_load_model_cpu(mock_cuda, mock_from_pretrained):
    mock_model = MagicMock()
    mock_from_pretrained.return_value = mock_model

    loader = ModelLoader("test-model/qwen-mini")
    model = loader.load_model()

    assert model == mock_model
    mock_from_pretrained.assert_called_once_with(
        "test-model/qwen-mini",
        quantization_config=None,
        trust_remote_code=True,
        device_map=None,
    )


@patch(
    "forgellm.models.loader.torch.cuda.get_device_name", return_value="NVIDIA RTX 4090"
)
@patch("forgellm.models.loader.AutoModelForCausalLM.from_pretrained")
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=True)
def test_model_loader_load_model_cuda_quantization(
    mock_cuda, mock_from_pretrained, mock_device_name
):
    mock_model = MagicMock()
    mock_from_pretrained.return_value = mock_model
    q_config = MagicMock()

    loader = ModelLoader("test-model/qwen-mini")
    model = loader.load_model(quantization_config=q_config)

    assert model == mock_model
    mock_from_pretrained.assert_called_once_with(
        "test-model/qwen-mini",
        quantization_config=q_config,
        trust_remote_code=True,
        device_map="auto",
    )


@patch(
    "forgellm.models.loader.AutoModelForCausalLM.from_pretrained",
    side_effect=Exception("Weights missing"),
)
@patch("forgellm.models.loader.torch.cuda.is_available", return_value=False)
def test_model_loader_load_model_failure(mock_cuda, mock_from_pretrained):
    loader = ModelLoader("test-model/qwen-mini")
    with pytest.raises(
        RuntimeError, match="Failed to load base model for test-model/qwen-mini"
    ):
        loader.load_model()


# ==============================================================================
# ForgeGenerator Tests
# ==============================================================================


def test_forge_generator_init():
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_tok = MagicMock()

    generator = ForgeGenerator(mock_model, mock_tok)
    assert generator.model == mock_model
    assert generator.tokenizer == mock_tok
    assert generator.device == torch.device("cpu")


@patch("builtins.input", side_effect=["exit"])
def test_forge_generator_chat_loop_exit(mock_input):
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_tok = MagicMock()

    generator = ForgeGenerator(mock_model, mock_tok)
    generator.chat_loop()

    mock_model.generate.assert_not_called()


@patch("transformers.TextStreamer")
@patch("builtins.input", side_effect=["Hello assistant", "quit"])
def test_forge_generator_chat_loop_generation_with_stop_tokens(
    mock_input, mock_streamer_cls
):
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

    mock_tok = MagicMock()
    mock_tok.eos_token_id = 151643
    mock_tok.pad_token_id = 151643
    mock_tok.vocab = {"<|im_end|>": 151645}
    mock_tok.convert_tokens_to_ids.return_value = 151645
    mock_tok.apply_chat_template.return_value = (
        "<|im_start|>user\nHello assistant<|im_end|>\n<|im_start|>assistant\n"
    )

    encoded_inputs = MagicMock()
    encoded_inputs.to.return_value = {"input_ids": torch.tensor([[10, 20]])}
    mock_tok.return_value = encoded_inputs

    generator = ForgeGenerator(mock_model, mock_tok)
    generator.chat_loop()

    assert mock_model.generate.called
    gen_kwargs = mock_model.generate.call_args[1]
    assert gen_kwargs["max_new_tokens"] == 150
    assert gen_kwargs["temperature"] == 0.7
    assert gen_kwargs["top_p"] == 0.9
    assert gen_kwargs["repetition_penalty"] == 1.2
    assert 151645 in gen_kwargs["eos_token_id"]


@patch("transformers.TextStreamer")
@patch("builtins.input", side_effect=["Hello assistant", "exit"])
def test_forge_generator_chat_loop_template_fallback(mock_input, mock_streamer_cls):
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])

    mock_tok = MagicMock()
    mock_tok.eos_token_id = 2
    mock_tok.pad_token_id = None
    mock_tok.vocab = {}
    mock_tok.apply_chat_template.side_effect = Exception("No template available")

    encoded_inputs = MagicMock()
    encoded_inputs.to.return_value = {"input_ids": torch.tensor([[10, 20]])}
    mock_tok.return_value = encoded_inputs

    generator = ForgeGenerator(mock_model, mock_tok)
    generator.chat_loop()

    assert mock_model.generate.called
    # Verified that call to tokenizer passed fallback prompt
    prompt_arg = mock_tok.call_args[0][0]
    assert prompt_arg == "User: Hello assistant\nAssistant:"


@patch("builtins.input", side_effect=KeyboardInterrupt)
def test_forge_generator_chat_loop_keyboard_interrupt(mock_input):
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_tok = MagicMock()

    generator = ForgeGenerator(mock_model, mock_tok)
    # Should catch KeyboardInterrupt and break cleanly
    generator.chat_loop()
    mock_model.generate.assert_not_called()


@patch("transformers.TextStreamer")
@patch("builtins.input", side_effect=["Generate text", "exit"])
def test_forge_generator_chat_loop_handles_runtime_exception(
    mock_input, mock_streamer_cls
):
    mock_model = MagicMock()
    mock_model.device = torch.device("cpu")
    mock_model.generate.side_effect = Exception("CUDA device out of memory")

    mock_tok = MagicMock()
    mock_tok.eos_token_id = 2
    mock_tok.pad_token_id = 2
    mock_tok.vocab = {}
    mock_tok.apply_chat_template.return_value = "Prompt"

    encoded_inputs = MagicMock()
    encoded_inputs.to.return_value = {"input_ids": torch.tensor([[10]])}
    mock_tok.return_value = encoded_inputs

    generator = ForgeGenerator(mock_model, mock_tok)
    # Should catch exception and gracefully handle error
    generator.chat_loop()
    assert mock_model.generate.called
