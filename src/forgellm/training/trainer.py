import os
import json
import yaml
import torch
from typing import Dict, Any
from datasets import Dataset, DatasetDict
from transformers import TrainingArguments 
from trl import SFTTrainer, SFTConfig
from forgellm.training.config import ForgeConfig
from forgellm.models.loader import ModelLoader
from forgellm.training.quantization import get_quantization_config
from forgellm.training.lora import get_lora_config

class ForgeTrainer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.raw_config = yaml.safe_load(f)
            
        class DummyConfig:
            def __init__(self, d):
                for k, v in d.items():
                    if isinstance(v, dict):
                        setattr(self, k, DummyConfig(v))
                    else:
                        setattr(self, k, v)
        
        self.config = DummyConfig({})
        
        self.config.model = DummyConfig({"name": self.raw_config.get("model", "Qwen/Qwen2.5-0.5B"), "trust_remote_code": False})
        
        q_dict = self.raw_config.get("quantization", {"enabled": False})
        self.config.quantization = DummyConfig(q_dict)
        
        lora_dict = self.raw_config.get("lora", {})
        self.config.lora = DummyConfig({
            "r": lora_dict.get("r", 8),
            "alpha": lora_dict.get("lora_alpha", 16),
            "dropout": lora_dict.get("lora_dropout", 0.05),
            "target_modules": lora_dict.get("target_modules", ["q_proj", "v_proj"])
        })
        
        self.config.training = DummyConfig({})
        tc = self.raw_config.get("training", {})
        self.config.training.output_dir = ".forgellm/training_output"
        self.config.training.num_train_epochs = int(tc.get("epochs", 1))
        self.config.training.per_device_train_batch_size = int(tc.get("batch_size", 1))
        self.config.training.per_device_eval_batch_size = int(tc.get("batch_size", 1))
        self.config.training.gradient_accumulation_steps = int(tc.get("gradient_accumulation_steps", 1))
        self.config.training.learning_rate = float(tc.get("learning_rate", 2e-4))
        self.config.training.logging_steps = 10
        self.config.training.save_steps = 0
        self.config.training.eval_steps = 0
        self.config.training.seed = 42
        
        self.config.dataset = DummyConfig({})
        self.config.dataset.max_seq_length = tc.get("max_length", 256)
        
        self.train_dataset = None
        self.eval_dataset = None
        self.trainer = None

    def prepare_dataset(self, train_path: str, val_path: str):
        self.train_dataset = Dataset.from_json(train_path)
        if os.path.exists(val_path):
            self.eval_dataset = Dataset.from_json(val_path)

    def train(self):
        # 1. Load tokenizer and model
        loader = ModelLoader(
            model_name=self.config.model.name,
            trust_remote_code=self.config.model.trust_remote_code
        )
        tokenizer = loader.load_tokenizer()
        
        # 2. Quantization
        q_config = get_quantization_config(self.config.quantization)
        
        # 3. Base model
        print("Loading base model...")
        model = loader.load_model(quantization_config=q_config)
        
        # 4. LoRA
        peft_config = get_lora_config(self.config.lora)
        
        # 5. Training Arguments
        training_args = SFTConfig(
            output_dir=self.config.training.output_dir,
            num_train_epochs=self.config.training.num_train_epochs,
            per_device_train_batch_size=self.config.training.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.training.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.training.gradient_accumulation_steps,
            learning_rate=self.config.training.learning_rate,
            logging_steps=self.config.training.logging_steps,
            save_steps=self.config.training.save_steps,
            eval_steps=self.config.training.eval_steps,
            eval_strategy="steps" if self.config.training.eval_steps > 0 else "no",
            save_strategy="steps" if self.config.training.save_steps > 0 else "no",
            seed=self.config.training.seed,
            report_to="none",
            max_length=self.config.dataset.max_seq_length
        )

        print("Initializing SFTTrainer...")
        self.trainer = SFTTrainer(
            model=model,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            peft_config=peft_config,
            processing_class=tokenizer,
            args=training_args,
        )
        
        print("\nStarting Training...")
        self.trainer.train()
        
    def save_model(self, adapter_path: str):
        print(f"\nSaving final LoRA adapter to {adapter_path}")
        self.trainer.model.save_pretrained(adapter_path)
        tokenizer_path = os.path.join(os.path.dirname(adapter_path), "tokenizer")
        self.trainer.processing_class.save_pretrained(tokenizer_path)
