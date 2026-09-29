from datasets import Dataset


class DatasetFormatter:
    def __init__(self, format_type: str = "messages"):
        self.format_type = format_type

    def format_dataset(self, jsonl_path: str) -> Dataset:
        """
        Loads a validated and cleaned JSONL file into a Hugging Face Dataset.
        For phase 1, we expect the conversational 'messages' format.
        """
        if self.format_type != "messages":
            raise ValueError(
                f"Format type '{self.format_type}' is not supported yet. Use 'messages'."
            )

        dataset = Dataset.from_json(jsonl_path)
        return dataset
