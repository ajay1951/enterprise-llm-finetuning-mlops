import json
import os
from forgellm.dataset.validator import DatasetValidator

class DatasetCleaner:
    def __init__(self, max_length: int = 10000):
        self.validator = DatasetValidator(max_length=max_length)
        
    def clean(self, input_path: str, output_path: str) -> dict:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        report = {
            "total_processed": 0,
            "saved": 0,
            "removed_invalid": 0,
            "removed_duplicates": 0
        }
        
        seen_contents = set()
        
        with open(input_path, "r", encoding="utf-8") as fin, \
             open(output_path, "w", encoding="utf-8") as fout:
            
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
                
                # Normalize whitespace in content
                for msg in record["messages"]:
                    msg["content"] = msg["content"].strip()
                
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                report["saved"] += 1
                
        return report
