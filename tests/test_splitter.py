import pytest
from datasets import Dataset
from forgellm.dataset.splitter import DatasetSplitter

def test_splitter():
    # Create dummy dataset
    data = {"text": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]}
    dataset = Dataset.from_dict(data)
    
    splitter = DatasetSplitter(validation_split=0.2, seed=42)
    split = splitter.split(dataset)
    
    assert "train" in split
    assert "validation" in split
    assert len(split["train"]) == 8
    assert len(split["validation"]) == 2
