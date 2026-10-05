import json
import logging
import os

import torch

try:
    from datasets import Dataset
except ImportError:  # pragma: no cover
    Dataset = None

try:
    from trl import DPOConfig, DPOTrainer
except (ImportError, RuntimeError, Exception):  # pragma: no cover
    DPOConfig = None
    DPOTrainer = None

from forgellm.models.loader import ModelLoader
from forgellm.training.lora import get_lora_config

logger = logging.getLogger(__name__)


class ForgeDPOTrainer:
    """Handles Direct Preference Optimization (DPO) training for human alignment."""

    def __init__(
        self, model_name: str = "Qwen/Qwen2.5-0.5B", output_dir: str = "outputs/dpo_run"
    ):
        self.model_name = model_name
        self.output_dir = output_dir

    def train_dpo(
        self,
        dataset_path: str,
        num_epochs: int = 1,
        learning_rate: float = 5e-6,
        beta: float = 0.1,
    ) -> str:
        """Execute DPO training on a dataset containing (prompt, chosen, rejected) pairs."""
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"DPO dataset not found: {dataset_path}")

        logger.info(f"Loading preference dataset from: {dataset_path}")
        dpo_dataset = Dataset.from_json(dataset_path)

        loader = ModelLoader(self.model_name)
        tokenizer = loader.load_tokenizer()

        logger.info("Loading model for DPO alignment...")
        model = loader.load_model(
            torch_dtype=torch.float16,
            device_map="auto" if torch.cuda.is_available() else "cpu",
        )

        dpo_config = DPOConfig(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            beta=beta,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            logging_steps=5,
            save_strategy="no",
            remove_unused_columns=False,
        )

        trainer = DPOTrainer(
            model=model,
            args=dpo_config,
            train_dataset=dpo_dataset,
            processing_class=tokenizer,
        )

        logger.info("Starting DPO Preference Optimization training...")
        trainer.train()

        os.makedirs(self.output_dir, exist_ok=True)
        trainer.save_model(self.output_dir)
        tokenizer.save_pretrained(self.output_dir)

        logger.info(f"DPO alignment complete! Model saved to {self.output_dir}")
        return self.output_dir
