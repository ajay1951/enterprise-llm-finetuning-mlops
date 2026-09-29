import json
import os
import tempfile

from forgellm.dataset.validator import DatasetValidator


def test_dataset_validator_valid():
    validator = DatasetValidator()

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(
            json.dumps(
                {
                    "messages": [
                        {"role": "user", "content": "hi"},
                        {"role": "assistant", "content": "hello"},
                    ]
                }
            )
            + "\n"
        )

    result = validator.validate_file(f.name)
    os.remove(f.name)

    assert result.status == "PASSED"
    assert result.valid == 1
    assert result.invalid == 0
    assert result.total == 1


def test_dataset_validator_invalid():
    validator = DatasetValidator()

    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(json.dumps({"wrong": "format"}) + "\n")

    result = validator.validate_file(f.name)
    os.remove(f.name)

    assert result.status == "FAILED"
    assert result.valid == 0
    assert result.invalid == 1
