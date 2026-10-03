from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datasets import Dataset, DatasetDict


class DatasetSplitter:
    def __init__(self, validation_split: float = 0.1, seed: int = 42):
        if not (0.0 < validation_split < 1.0):
            raise ValueError("validation_split must be between 0.0 and 1.0")
        self.validation_split = validation_split
        self.seed = seed

    def split(self, dataset: Any) -> Any:
        """Splits a dataset into train and validation sets."""
        try:
            from datasets import DatasetDict
        except ImportError:
            DatasetDict = dict

        split_dataset = dataset.train_test_split(
            test_size=self.validation_split, seed=self.seed
        )
        # Rename 'test' to 'validation' to match typical naming
        return DatasetDict(
            {"train": split_dataset["train"], "validation": split_dataset["test"]}
        )
