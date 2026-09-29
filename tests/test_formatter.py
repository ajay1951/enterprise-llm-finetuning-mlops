import json

import pytest

from forgellm.dataset.formatter import DatasetFormatter


def test_format_dataset_messages(tmp_path):
    sample_file = tmp_path / "train.jsonl"
    record = {
        "messages": [
            {"role": "user", "content": "How do I reset my password?"},
            {
                "role": "assistant",
                "content": "Click 'Forgot Password' on the login screen.",
            },
        ]
    }
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    formatter = DatasetFormatter(format_type="messages")
    dataset = formatter.format_dataset(str(sample_file))

    assert len(dataset) == 1
    assert "messages" in dataset.column_names


def test_format_dataset_unsupported():
    formatter = DatasetFormatter(format_type="unknown")
    with pytest.raises(ValueError):
        formatter.format_dataset("dummy.jsonl")
