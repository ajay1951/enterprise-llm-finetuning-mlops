import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, List
import torch
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from peft import PeftModel
from threading import Thread
from .base import ModelServingBackend

logger = logging.getLogger(__name__)


class TransformersBackend(ModelServingBackend):
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cpu"

    async def load_model(
        self,
        base_model: str,
        adapter_path: str = None,
        device: str = "cuda",
        config: dict = None,
    ) -> bool:
        try:
            logger.info(f"Loading base model {base_model} onto {device}")
            self.device = device

            # Use torch.float16 or bfloat16 for efficiency if on CUDA
            dtype = torch.float16 if device == "cuda" else torch.float32

            self.tokenizer = AutoTokenizer.from_pretrained(
                base_model, trust_remote_code=True
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=dtype,
                device_map=device,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

            if adapter_path:
                logger.info(f"Applying PEFT adapter from {adapter_path}")
                self.model = PeftModel.from_pretrained(self.model, adapter_path)

            self.model.eval()

            # Simple Warmup
            logger.info("Running warmup inference...")
            warmup_ids = self.tokenizer.encode("Hello", return_tensors="pt").to(
                self.device
            )
            with torch.no_grad():
                self.model.generate(warmup_ids, max_new_tokens=2)
            logger.info("Warmup complete.")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    async def unload_model(self):
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer
            self.tokenizer = None

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("Model unloaded and memory freed.")

    def _prepare_inputs(self, messages: List[Dict[str, str]]):
        if (
            hasattr(self.tokenizer, "apply_chat_template")
            and self.tokenizer.chat_template
        ):
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        else:
            # Fallback for models without chat templates
            prompt = ""
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role.capitalize()}: {content}\n"
            prompt += "Assistant:"
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        return inputs

    async def generate_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        inputs = self._prepare_inputs(messages)

        # Prevent context overflow
        max_context = kwargs.get("max_model_len", 4096)
        if inputs["input_ids"].shape[1] >= max_context:
            raise ValueError(
                f"Context length exceeded: Input has {inputs['input_ids'].shape[1]} tokens, max is {max_context}"
            )

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        generation_kwargs = dict(
            **inputs,
            streamer=streamer,
            max_new_tokens=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 1.0),
            do_sample=kwargs.get("temperature", 0.7) > 0,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        # Iterate over the streamer
        for new_text in streamer:
            # Yield control back to event loop briefly so streaming is non-blocking
            await asyncio.sleep(0.001)
            yield new_text

        thread.join()

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        inputs = self._prepare_inputs(messages)

        max_context = kwargs.get("max_model_len", 4096)
        if inputs["input_ids"].shape[1] >= max_context:
            raise ValueError(
                f"Context length exceeded: Input has {inputs['input_ids'].shape[1]} tokens, max is {max_context}"
            )

        generation_kwargs = dict(
            **inputs,
            max_new_tokens=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 1.0),
            do_sample=kwargs.get("temperature", 0.7) > 0,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        with torch.no_grad():
            outputs = self.model.generate(**generation_kwargs)

        # Decode only the newly generated tokens
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return response
