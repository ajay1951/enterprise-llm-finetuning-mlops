import os

import pytest

from forgellm.dataset.validator import DatasetValidator
from forgellm.training.trainer import ForgeTrainer


def test_multi_turn_dataset_validator():
    validator = DatasetValidator()
    errors = []

    # Valid multi-turn dialogue record
    multi_turn_record = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful customer support assistant.",
            },
            {"role": "user", "content": "Hello, my app keeps closing on startup."},
            {
                "role": "assistant",
                "content": "I can help with that. What version of the app are you running?",
            },
            {"role": "user", "content": "I am using version 2.4.1."},
            {
                "role": "assistant",
                "content": "Thank you! Please try clearing app cache in settings.",
            },
        ]
    }

    assert validator._validate_record(multi_turn_record, 1, errors) is True
    assert len(errors) == 0


def test_checkpoint_pruner_utility(tmp_path):
    output_dir = tmp_path / "checkpoints"
    os.makedirs(output_dir, exist_ok=True)

    # Create 5 fake step checkpoint directories
    for step in [10, 20, 30, 40, 50]:
        ckpt_dir = output_dir / f"checkpoint-{step}"
        os.makedirs(ckpt_dir, exist_ok=True)

    target_dir = str(output_dir)

    class DummyTraining:
        output_dir = target_dir

    class DummyConfig:
        training = DummyTraining()

    trainer = ForgeTrainer.__new__(ForgeTrainer)
    trainer.config = DummyConfig()

    trainer._prune_old_checkpoints(max_to_keep=3)

    remaining = os.listdir(output_dir)
    assert len(remaining) == 3
    assert "checkpoint-30" in remaining
    assert "checkpoint-40" in remaining
    assert "checkpoint-50" in remaining
    assert "checkpoint-10" not in remaining
    assert "checkpoint-20" not in remaining
