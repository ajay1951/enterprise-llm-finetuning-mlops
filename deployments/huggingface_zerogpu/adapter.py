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


DEFAULT_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


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
            dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
                trust_remote_code=True,
            ).to(self.device)
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
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.8,
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
        raw_inputs = self.tokenizer(prompt_text, return_tensors="pt")
        if hasattr(raw_inputs, "to"):
            inputs = raw_inputs.to(target_device)
        else:
            inputs = {
                k: v.to(target_device) if hasattr(v, "to") else v
                for k, v in raw_inputs.items()
            }

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        do_sample = temperature > 0.0
        gen_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.eos_token_id or self.tokenizer.pad_token_id,
        }
        if do_sample:
            gen_kwargs["temperature"] = max(temperature, 1e-4)
            gen_kwargs["top_p"] = top_p

        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()

        start_time = time.perf_counter()
        first_token_time = None
        accumulated_text = ""
        token_count = 0

        for new_text in streamer:
            if not new_text:
                continue
            accumulated_text += new_text
            token_count += 1
            if first_token_time is None:
                first_token_time = time.perf_counter()

            now = time.perf_counter()
            elapsed_sec = max(0.001, now - start_time)
            tokens_per_sec = token_count / elapsed_sec
            ttft_sec = (first_token_time - start_time) if first_token_time else 0.0

            telemetry = {
                "model": self.model_id,
                "device": str(self.model.device),
                "tokens_generated": token_count,
                "latency_sec": round(elapsed_sec, 3),
                "ttft_sec": round(ttft_sec, 3),
                "tokens_per_sec": round(tokens_per_sec, 2),
            }
            yield accumulated_text, telemetry

        thread.join()
