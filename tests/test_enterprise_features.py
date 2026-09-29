import json
import os

import pytest

from forgellm.dataset.cleaner import DatasetCleaner


def test_pii_sanitization():
    cleaner = DatasetCleaner(sanitize_pii=True)
    raw_text = "Contact support at testuser@example.com or call +1-555-123-4567. SSN: 123-45-6789."
    scrubbed = cleaner.scrub_pii(raw_text)

    assert "[EMAIL_REDACTED]" in scrubbed
    assert "testuser@example.com" not in scrubbed
    assert "[PHONE_REDACTED]" in scrubbed
    assert "[SSN_REDACTED]" in scrubbed


def test_dataset_cleaner_pii_integration(tmp_path):
    input_file = tmp_path / "raw.jsonl"
    output_file = tmp_path / "cleaned.jsonl"

    sample_record = {
        "messages": [
            {
                "role": "user",
                "content": "My email is user@domain.org and IP is 192.168.1.1.",
            },
            {"role": "assistant", "content": "Thanks! We received your request."},
        ]
    }

    with open(input_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(sample_record) + "\n")

    cleaner = DatasetCleaner(sanitize_pii=True)
    report = cleaner.clean(str(input_file), str(output_file))

    assert report["saved"] == 1
    assert report["pii_sanitized"] >= 1

    with open(output_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        user_msg = data["messages"][0]["content"]
        assert "[EMAIL_REDACTED]" in user_msg
        assert "[IP_REDACTED]" in user_msg
