import json
import os
from typing import Any


class ValidationResult:
    def __init__(self, total: int, valid: int, invalid: int, duplicates: int, errors: list[str]):
        self.total = total
        self.valid = valid
        self.invalid = invalid
        self.duplicates = duplicates
        self.errors = errors
        self.status = "PASSED" if self.valid > 0 else "FAILED"
    
    def __str__(self) -> str:
        res = "Dataset Validation\n"
        res += "-" * 28 + "\n"
        res += f"Total examples:       {self.total}\n"
        res += f"Valid examples:       {self.valid}\n"
        res += f"Invalid examples:     {self.invalid}\n"
        res += f"Duplicates:           {self.duplicates}\n\n"
        if self.errors:
            res += "Errors (first 5):\n"
            for err in self.errors[:5]:
                res += f"  - {err}\n"
            res += "\n"
        res += f"Status: {self.status}"
        return res

class DatasetValidator:
    def __init__(self, max_length: int = 10000):
        self.max_length = max_length
        self.valid_roles = {"system", "user", "assistant"}

    def validate_file(self, filepath: str) -> ValidationResult:
        if not os.path.exists(filepath):
            return ValidationResult(0, 0, 0, 0, [f"File not found: {filepath}"])

        total = 0
        valid = 0
        invalid = 0
        duplicates = 0
        errors = []
        seen_contents = set()

        with open(filepath, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                total += 1
                
                if line in seen_contents:
                    duplicates += 1
                    invalid += 1
                    errors.append(f"Line {line_idx}: Duplicate record")
                    continue
                
                seen_contents.add(line)

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    invalid += 1
                    errors.append(f"Line {line_idx}: Invalid JSON")
                    continue

                if not self._validate_record(record, line_idx, errors):
                    invalid += 1
                else:
                    valid += 1

        return ValidationResult(total, valid, invalid, duplicates, errors)

    def _validate_record(self, record: Any, line_idx: int, errors: list[str]) -> bool:
        if not isinstance(record, dict):
            errors.append(f"Line {line_idx}: Record is not a JSON object")
            return False
            
        if "messages" not in record:
            errors.append(f"Line {line_idx}: Missing 'messages' field")
            return False
            
        messages = record["messages"]
        if not isinstance(messages, list):
            errors.append(f"Line {line_idx}: 'messages' must be a list")
            return False

        has_user = False
        has_assistant = False

        for i, msg in enumerate(messages):
            if not isinstance(msg, dict):
                errors.append(f"Line {line_idx}, Msg {i}: Message is not an object")
                return False
                
            if "role" not in msg or "content" not in msg:
                errors.append(f"Line {line_idx}, Msg {i}: Missing 'role' or 'content'")
                return False
                
            role = msg["role"]
            content = msg["content"]

            if role not in self.valid_roles:
                errors.append(f"Line {line_idx}, Msg {i}: Invalid role '{role}'")
                return False
                
            if not isinstance(content, str) or not content.strip():
                errors.append(f"Line {line_idx}, Msg {i}: Content is empty or not a string")
                return False
                
            if len(content) > self.max_length:
                errors.append(f"Line {line_idx}, Msg {i}: Content exceeds max length")
                return False

            if role == "user":
                has_user = True
            elif role == "assistant":
                has_assistant = True

        if not has_user:
            errors.append(f"Line {line_idx}: Missing at least one 'user' message")
            return False
            
        if not has_assistant:
            errors.append(f"Line {line_idx}: Missing at least one 'assistant' message")
            return False

        return True
