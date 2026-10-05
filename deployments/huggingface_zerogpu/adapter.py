"""ForgeLLM ZeroGPU Inference Adapter.

Provides a clean GPU-decorated execution boundary for Hugging Face Spaces (ZeroGPU)
with fallback for local workstations and CI environments.
"""

import os
import sys
import time
from collections.abc import Generator
from threading import Thread
from typing import Any

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
)

# Optional spaces decorator with graceful local fallback
try:
    import spaces

    gpu_decorator = spaces.GPU(duration=60)
except (ImportError, AttributeError):

    def gpu_decorator(func):
        """No-op fallback decorator when spaces is not installed."""
        return func


DEFAULT_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


class ZeroGPUInferenceEngine:
    """Manages model loading and streaming generation within Hugging Face ZeroGPU constraints."""

    def __init__(self, model_id: str = DEFAULT_MODEL_ID):
        self.model_id = os.environ.get("FORGELLM_MODEL_ID", model_id)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self._is_loaded = False

    def load_model(self) -> bool:
        """Load tokenizer and model weights onto appropriate device."""
        if self._is_loaded:
            return True

        try:
            print(f"[ForgeLLM-ZeroGPU] Loading tokenizer: {self.model_id}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, trust_remote_code=True
            )

            print(f"[ForgeLLM-ZeroGPU] Loading model weights: {self.model_id}")
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model.eval()
            self._is_loaded = True
            print(
                f"[ForgeLLM-ZeroGPU] Successfully loaded model on device: {self.device}"
            )
            return True
        except Exception as e:
            print(
                f"[ForgeLLM-ZeroGPU] Failed to load model {self.model_id}: {e}",
                file=sys.stderr,
            )
            self._is_loaded = False
            return False

    @gpu_decorator
    def generate_stream(
        self,
        messages: list[dict[str, str]],
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Generator[tuple[str, dict[str, Any]], None, None]:
        """Generate response tokens with live telemetry.

        Yields:
            tuple of (accumulated_text: str, metrics: dict)
        """
        if not self._is_loaded and not self.load_model():
            yield (
                "Error: Model failed to load. Please check network and logs.",
                {},
            )
            return

        # On ZeroGPU, migrate model to CUDA once inside @spaces.GPU lease
        if torch.cuda.is_available() and self.model is not None:
            current_dev = next(self.model.parameters()).device
            if current_dev.type != "cuda":
                print(
                    "[ForgeLLM-ZeroGPU] Migrating model to CUDA inside ZeroGPU slice..."
                )
                self.model.to("cuda")

        # Input sanitization and bounds enforcement
        max_new_tokens = max(1, min(int(max_new_tokens), 512))
        temperature = max(0.0, min(float(temperature), 2.0))
        top_p = max(0.1, min(float(top_p), 1.0))

        # Format ChatML prompt template
        if (
            hasattr(self.tokenizer, "apply_chat_template")
            and self.tokenizer.chat_template
        ):
            prompt_text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            prompt_text = ""
            for m in messages:
                prompt_text += f"{m.get('role', 'user')}: {m.get('content', '')}\n"
            prompt_text += "assistant:\n"

        target_device = self.model.device if self.model else "cpu"
        inputs = self.tokenizer(prompt_text, return_tensors="pt")
        input_ids = inputs["input_ids"].to(target_device)
        attention_mask = inputs.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(target_device)

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        gen_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature if temperature > 0 else None,
            "top_p": top_p if temperature > 0 else None,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.eos_token_id,
        }

        start_time = time.perf_counter()
        first_token_time = None
        generated_text = ""
        token_count = 0

        # Execute generation in separate daemon thread for streaming
        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()

        for token_count, new_text in enumerate(streamer, start=1):
            if first_token_time is None:
                first_token_time = time.perf_counter()
            generated_text += new_text
            now = time.perf_counter()
            ttft_sec = (first_token_time - start_time) if first_token_time else 0.0
            elapsed_sec = max(0.001, now - start_time)
            tokens_per_sec = token_count / elapsed_sec

            telemetry = {
                "model": self.model_id,
                "device": str(self.model.device),
                "tokens_generated": token_count,
                "latency_sec": round(elapsed_sec, 3),
                "ttft_sec": round(ttft_sec, 3),
                "tokens_per_sec": round(tokens_per_sec, 2),
            }
            yield generated_text, telemetry

        thread.join()
