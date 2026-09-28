import os

import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    name: str = Field(default="Qwen/Qwen2.5-0.5B", description="The HuggingFace model ID or local path")
    model_version: str = Field(default="latest", description="Version string for reproducibility tracking")
    tokenizer_name: str | None = Field(default=None, description="Optional override for tokenizer")
    trust_remote_code: bool = Field(default=True, description="Trust remote code for HF models")

class DatasetConfig(BaseModel):
    train_file: str = Field(default="data/raw/train.jsonl")
    val_file: str | None = Field(default=None)
    version: str = Field(default="v1.0", description="Dataset version identifier")
    validation_split: float = Field(default=0.1, description="Ratio of train data to use for validation if val_file is None")
    test_split: float = Field(default=0.0, description="Optional holdout test set ratio")
    seed: int = Field(default=42, description="Random seed for splitting")
    max_seq_length: int = Field(default=2048, description="Maximum token sequence length")

class TrainingConfig(BaseModel):
    experiment_name: str = Field(default="ForgeLLM_FineTuning", description="MLflow Experiment Name")
    mlflow_tracking_uri: str = Field(default="http://localhost:5000", description="MLflow tracking URI")
    output_dir: str = Field(default="outputs")
    num_train_epochs: int = Field(default=1)
    per_device_train_batch_size: int = Field(default=1)
    per_device_eval_batch_size: int = Field(default=1)
    gradient_accumulation_steps: int = Field(default=8)
    learning_rate: float = Field(default=0.0002)
    weight_decay: float = Field(default=0.01)
    warmup_ratio: float = Field(default=0.03)
    lr_scheduler_type: str = Field(default="cosine")
    logging_steps: int = Field(default=10)
    save_steps: int = Field(default=100)
    eval_steps: int = Field(default=100)
    seed: int = Field(default=42, description="Global random seed for PyTorch/CUDA/Numpy")

class LoraConfig(BaseModel):
    r: int = Field(default=16)
    alpha: int = Field(default=32)
    dropout: float = Field(default=0.05)
    target_modules: list[str] = Field(default_factory=lambda: ["q_proj", "v_proj"])

class QuantizationConfig(BaseModel):
    enabled: bool = Field(default=True)
    bits: int = Field(default=4)

class ForgeConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    lora: LoraConfig = Field(default_factory=LoraConfig)
    quantization: QuantizationConfig = Field(default_factory=QuantizationConfig)

def load_config(path: str) -> ForgeConfig:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        
    return ForgeConfig.model_validate(data)
