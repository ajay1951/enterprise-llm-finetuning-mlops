import datetime
import json
import os
import subprocess

import mlflow
from datasets import Dataset
from transformers import set_seed
from trl import SFTConfig, SFTTrainer

from forgellm.models.loader import ModelLoader
from forgellm.training.config import load_config
from forgellm.training.lora import get_lora_config
from forgellm.training.quantization import get_quantization_config


class ForgeTrainer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = load_config(config_path)

        # Enforce exact reproducibility across PyTorch and Transformers
        set_seed(self.config.training.seed)

        self.train_dataset = None
        self.eval_dataset = None
        self.trainer = None

    def _get_git_commit(self) -> str:
        try:
            return (
                subprocess.check_output(["git", "rev-parse", "HEAD"])
                .decode("ascii")
                .strip()
            )
        except Exception:
            return "unknown"

    def _save_run_metadata(self):
        os.makedirs(self.config.training.output_dir, exist_ok=True)
        metadata = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "git_commit": self._get_git_commit(),
            "config": self.config.model_dump(),
        }
        metadata_path = os.path.join(
            self.config.training.output_dir, "run_metadata.json"
        )
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Run metadata saved to {metadata_path}")

    def prepare_dataset(self, train_path: str, val_path: str):
        self.train_dataset = Dataset.from_json(train_path)
        if os.path.exists(val_path):
            self.eval_dataset = Dataset.from_json(val_path)

    def _apply_oom_guardrails(self):
        """Inspect CUDA VRAM and dynamically adjust batch size & quantization if memory is constrained."""
        import torch

        if torch.cuda.is_available():
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"[OOM Guardrail] Detected GPU VRAM: {total_vram_gb:.2f} GB")
            if total_vram_gb < 6.0:
                print(
                    "[OOM Guardrail] VRAM < 6GB. Enabling micro-batch size = 1 and 4-bit QLoRA to prevent CUDA OOM."
                )
                self.config.training.per_device_train_batch_size = 1
                self.config.training.gradient_accumulation_steps = max(
                    4, self.config.training.gradient_accumulation_steps
                )
                self.config.quantization.load_in_4bit = True

    def train(self):
        # 0. Save Metadata & Apply Guardrails
        self._save_run_metadata()
        self._apply_oom_guardrails()

        # 1. Load tokenizer and model
        loader = ModelLoader(
            model_name=self.config.model.name,
            trust_remote_code=self.config.model.trust_remote_code,
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
            report_to="mlflow",
            max_length=self.config.dataset.max_seq_length,
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
        mlflow.set_tracking_uri(self.config.training.mlflow_tracking_uri)
        mlflow.set_experiment(self.config.training.experiment_name)

        # Determine run name
        commit_sha = self._get_git_commit()
        run_name = (
            f"run_{commit_sha[:7]}"
            if commit_sha != "unknown"
            else f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        with mlflow.start_run(run_name=run_name) as run:
            self.active_run_id = run.info.run_id

            # Flatten config for MLflow
            def flatten_dict(d, parent_key="", sep="."):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            mlflow.log_params(flatten_dict(self.config.model_dump()))
            mlflow.set_tag("git_commit", commit_sha)
            mlflow.set_tag("model_version", self.config.model.model_version)
            mlflow.set_tag("dataset_version", self.config.dataset.version)

            self.trainer.train()

    def _prune_old_checkpoints(self, max_to_keep: int = 3):
        """Clean up older checkpoint folders in output_dir, retaining top max_to_keep checkpoints."""
        import shutil

        out_dir = self.config.training.output_dir
        if not os.path.exists(out_dir):
            return

        checkpoints = [
            os.path.join(out_dir, d)
            for d in os.listdir(out_dir)
            if d.startswith("checkpoint-") and os.path.isdir(os.path.join(out_dir, d))
        ]

        if len(checkpoints) > max_to_keep:
            # Sort by checkpoint step number
            checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
            to_remove = checkpoints[:-max_to_keep]
            for ckpt in to_remove:
                print(f"[Checkpoint Pruner] Removing old checkpoint: {ckpt}")
                shutil.rmtree(ckpt, ignore_errors=True)

    def save_model(self, adapter_path: str):
        print(f"\nSaving final LoRA adapter to {adapter_path}")
        self.trainer.model.save_pretrained(adapter_path)
        tokenizer_path = os.path.join(os.path.dirname(adapter_path), "tokenizer")
        self.trainer.processing_class.save_pretrained(tokenizer_path)
        self._prune_old_checkpoints(max_to_keep=3)

        # Log artifacts to MLflow if active
        if hasattr(self, "active_run_id") and self.active_run_id:
            mlflow.set_tracking_uri(self.config.training.mlflow_tracking_uri)
            with mlflow.start_run(run_id=self.active_run_id):
                print(f"Logging artifacts to MLflow run {self.active_run_id}...")
                mlflow.log_artifacts(adapter_path, artifact_path="model_adapter")
                mlflow.log_artifacts(tokenizer_path, artifact_path="tokenizer")

                # Also log metadata json
                metadata_path = os.path.join(
                    self.config.training.output_dir, "run_metadata.json"
                )
                if os.path.exists(metadata_path):
                    mlflow.log_artifact(metadata_path, artifact_path="metadata")
