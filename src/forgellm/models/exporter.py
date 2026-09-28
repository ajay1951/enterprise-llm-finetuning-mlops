import os
import logging
import torch
from peft import PeftModel
from forgellm.models.loader import ModelLoader
from forgellm.models.registry import ModelRegistry

logger = logging.getLogger(__name__)

class ModelExporter:
    """Handles merging PEFT LoRA adapters into base weights and exporting standalone formats."""

    def __init__(self, registry: ModelRegistry = None):
        self.registry = registry or ModelRegistry()

    def export_merged_model(
        self,
        model_ref: str,
        output_dir: str,
        save_tokenizer: bool = True
    ) -> str:
        """Merge PEFT adapter with base model and save full standalone weights."""
        if ":" not in model_ref:
            model_name, version = model_ref, "v1"
        else:
            model_name, version = model_ref.split(":")

        info = self.registry.get_model(model_name, version)
        if not info:
            raise ValueError(f"Model reference '{model_ref}' not found in registry.")

        base_model_name = info.get("base_model", "Qwen/Qwen2.5-0.5B")
        adapter_path = os.path.join(info["location"], "adapter")

        logger.info(f"Loading base model: {base_model_name}")
        loader = ModelLoader(base_model_name)
        tokenizer = loader.load_tokenizer()
        
        # Load base model in float16 for merging
        base_model = loader.load_model(torch_dtype=torch.float16, device_map="cpu")

        logger.info(f"Loading LoRA adapter from: {adapter_path}")
        peft_model = PeftModel.from_pretrained(base_model, adapter_path)

        logger.info("Merging LoRA weights with base model...")
        merged_model = peft_model.merge_and_unload()

        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Saving merged standalone model to: {output_dir}")
        merged_model.save_pretrained(output_dir, safe_serialization=True)

        if save_tokenizer and tokenizer:
            tokenizer.save_pretrained(output_dir)

        logger.info(f"Successfully exported merged model to {output_dir}")
        return output_dir
