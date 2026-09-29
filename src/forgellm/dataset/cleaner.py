import json
import os
import re

from forgellm.dataset.validator import DatasetValidator


class DatasetCleaner:
    def __init__(self, max_length: int = 10000, sanitize_pii: bool = True):
        self.validator = DatasetValidator(max_length=max_length)
        self.sanitize_pii = sanitize_pii

        # PII Regex patterns for automated scrubbing
        self.pii_patterns = [
            (
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
                "[EMAIL_REDACTED]",
            ),
            (
                re.compile(
                    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
                ),
                "[PHONE_REDACTED]",
            ),
            (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
            (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CREDIT_CARD_REDACTED]"),
            (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), "[IP_REDACTED]"),
        ]

    def scrub_pii(self, text: str) -> str:
        """Replace sensitive PII strings with redacted placeholders."""
        for pattern, replacement in self.pii_patterns:
            text = pattern.sub(replacement, text)
        return text

    def clean(self, input_path: str, output_path: str) -> dict:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        report = {
            "total_processed": 0,
            "saved": 0,
            "removed_invalid": 0,
            "removed_duplicates": 0,
            "pii_sanitized": 0,
        }

        seen_contents = set()

        with (
            open(input_path, "r", encoding="utf-8") as fin,
            open(output_path, "w", encoding="utf-8") as fout,
        ):
            for line_idx, line in enumerate(fin, start=1):
                line = line.strip()
                if not line:
                    continue

                report["total_processed"] += 1

                # Check duplicates
                if line in seen_contents:
                    report["removed_duplicates"] += 1
                    continue

                seen_contents.add(line)

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    report["removed_invalid"] += 1
                    continue

                errors = []
                if not self.validator._validate_record(record, line_idx, errors):
                    report["removed_invalid"] += 1
                    continue

                # Normalize whitespace & sanitize PII in content
                for msg in record["messages"]:
                    original = msg["content"].strip()
                    if self.sanitize_pii:
                        sanitized = self.scrub_pii(original)
                        if sanitized != original:
                            report["pii_sanitized"] += 1
                        msg["content"] = sanitized
                    else:
                        msg["content"] = original

                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                report["saved"] += 1

        return report
