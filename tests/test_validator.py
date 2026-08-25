import pytest
from forgellm.dataset.validator import DatasetValidator

def test_valid_record():
    validator = DatasetValidator()
    record = {
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"}
        ]
    }
    errors = []
    assert validator._validate_record(record, 1, errors) == True
    assert len(errors) == 0

def test_missing_user():
    validator = DatasetValidator()
    record = {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "assistant", "content": "hi"}
        ]
    }
    errors = []
    assert validator._validate_record(record, 1, errors) == False
    assert any("Missing at least one 'user' message" in e for e in errors)

def test_empty_content():
    validator = DatasetValidator()
    record = {
        "messages": [
            {"role": "user", "content": "  "},
            {"role": "assistant", "content": "hi"}
        ]
    }
    errors = []
    assert validator._validate_record(record, 1, errors) == False
    assert any("Content is empty" in e for e in errors)
