import os
import tempfile

import pytest
import yaml
from pydantic import ValidationError

from forgellm.training.config import ForgeConfig, load_config


def test_load_config_valid():
    config_data = {
        "model": {"name": "TestModel", "model_version": "v2"},
        "training": {"learning_rate": 0.01, "seed": 999}
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
        yaml.dump(config_data, f)
        temp_path = f.name
        
    try:
        config = load_config(temp_path)
        assert isinstance(config, ForgeConfig)
        assert config.model.name == "TestModel"
        assert config.model.model_version == "v2"
        assert config.training.learning_rate == 0.01
        assert config.training.seed == 999
        # Default fallback assertions
        assert config.dataset.seed == 42
    finally:
        os.remove(temp_path)

def test_load_config_invalid_type():
    config_data = {
        "training": {"learning_rate": "invalid_string"} # Expecting float
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
        yaml.dump(config_data, f)
        temp_path = f.name
        
    try:
        with pytest.raises(ValidationError):
            load_config(temp_path)
    finally:
        os.remove(temp_path)

def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config.yaml")
