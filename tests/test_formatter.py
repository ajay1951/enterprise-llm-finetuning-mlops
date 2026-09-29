import pytest

from forgellm.dataset.formatter import DatasetFormatter


def test_format_dataset_unsupported():
    formatter = DatasetFormatter(format_type="unknown")
    with pytest.raises(ValueError):
        formatter.format_dataset("dummy.jsonl")
