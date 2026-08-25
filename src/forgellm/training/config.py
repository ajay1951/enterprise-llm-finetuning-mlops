import yaml
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ModelConfig:
    name: str = "Qwen/Qwen2.5-0.5B"
    trust_remote_code: bool = True

@dataclass
class DatasetConfig:
    train_file: str = "data/raw/train.jsonl"
    validation_split: float = 0.1
    seed: int = 42
    max_seq_length: int = 2048

@dataclass
class TrainingConfig:
    output_dir: str = "outputs"
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 0.0002
    warmup_ratio: float = 0.03
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    seed: int = 42

@dataclass
class LoraConfig:
    r: int = 16
    alpha: int = 32
    dropout: float = 0.05

@dataclass
class QuantizationConfig:
    enabled: bool = True
    bits: int = 4

@dataclass
class ForgeConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    lora: LoraConfig = field(default_factory=LoraConfig)
    quantization: QuantizationConfig = field(default_factory=QuantizationConfig)

def load_config(path: str) -> ForgeConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    return ForgeConfig(
        model=ModelConfig(**data.get("model", {})),
        dataset=DatasetConfig(**data.get("dataset", {})),
        training=TrainingConfig(**data.get("training", {})),
        lora=LoraConfig(**data.get("lora", {})),
        quantization=QuantizationConfig(**data.get("quantization", {}))
    )
