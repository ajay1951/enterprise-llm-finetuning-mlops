import warnings

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
)


class ModelLoader:
    def __init__(self, model_name: str, trust_remote_code: bool = True):
        self.model_name = model_name
        self.trust_remote_code = trust_remote_code
        self._check_device()

    def _check_device(self):
        print("Model Loader")
        print("-" * 24)
        print(f"Model: {self.model_name}")

        self.device = "cpu"
        self.cuda_available = torch.cuda.is_available()

        print(f"CUDA available: {'YES' if self.cuda_available else 'NO'}")

        if self.cuda_available:
            self.device = "cuda"
            print("Device: CUDA")
            print(f"GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("Device: CPU")
            warnings.warn("CUDA is not available. Training will be extremely slow.")

    def load_tokenizer(self) -> PreTrainedTokenizer:
        try:
            tokenizer = AutoTokenizer.from_pretrained(  # nosec B615
                self.model_name, trust_remote_code=self.trust_remote_code
            )
            # Add pad token if missing
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            return tokenizer
        except Exception as e:
            raise RuntimeError(f"Failed to load tokenizer for {self.model_name}: {e}")

    def load_model(self, quantization_config=None, **kwargs) -> PreTrainedModel:
        try:
            device_map = kwargs.pop(
                "device_map",
                "auto" if (self.cuda_available and quantization_config) else None,
            )
            model = AutoModelForCausalLM.from_pretrained(  # nosec B615
                self.model_name,
                quantization_config=quantization_config,
                trust_remote_code=self.trust_remote_code,
                device_map=device_map,
                **kwargs,
            )
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load base model for {self.model_name}: {e}")
