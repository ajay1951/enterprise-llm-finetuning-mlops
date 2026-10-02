import json
from pathlib import Path

import pytest

from forgellm.dataset.registry import DatasetRegistry


def test_dataset_registry_initialization(tmp_path):
    registry = DatasetRegistry(base_dir=str(tmp_path / "datasets"))
    assert registry.list_datasets() == []


def test_dataset_registry_register_and_list(tmp_path):
    registry_dir = tmp_path / "datasets"
    registry = DatasetRegistry(base_dir=str(registry_dir))

    # Create dummy source, train, val files
    source_file = tmp_path / "raw.jsonl"
    source_file.write_text('{"messages": [{"role": "user", "content": "hi"}]}\n')

    train_file = tmp_path / "train.jsonl"
    train_file.write_text('{"messages": [{"role": "user", "content": "hi"}]}\n')

    val_file = tmp_path / "val.jsonl"
    val_file.write_text('{"messages": [{"role": "user", "content": "hi"}]}\n')

    meta = registry.register(
        dataset_name="support_chat",
        source_path=str(source_file),
        train_path=str(train_file),
        val_path=str(val_file),
        total_examples=1,
        training_examples=1,
        validation_examples=1,
        seed=42,
    )

    assert meta["dataset_name"] == "support_chat"
    assert meta["version"] == "v1"
    assert meta["total_examples"] == 1
    assert "sha256" in meta

    # List datasets
    assert "support_chat" in registry.list_datasets()

    # List versions
    versions = registry.list_versions("support_chat")
    assert len(versions) == 1
    assert versions[0]["version"] == "v1"

    # Get version info
    v1_info = registry.get_version_info("support_chat", "v1")
    assert v1_info is not None
    assert v1_info["version"] == "v1"

    # Non-existent version
    assert registry.get_version_info("support_chat", "v999") is None
    assert registry.list_versions("non_existent") == []


def test_dataset_registry_duplicate_registration_skipped(tmp_path):
    registry = DatasetRegistry(base_dir=str(tmp_path / "datasets"))

    source_file = tmp_path / "raw.jsonl"
    source_file.write_text('{"sample": 1}\n')

    train_file = tmp_path / "train.jsonl"
    train_file.write_text('{"sample": 1}\n')

    val_file = tmp_path / "val.jsonl"
    val_file.write_text('{"sample": 1}\n')

    meta1 = registry.register(
        "my_ds", str(source_file), str(train_file), str(val_file), 1, 1, 1, 42
    )
    # Registering exact same file with identical hash
    meta2 = registry.register(
        "my_ds", str(source_file), str(train_file), str(val_file), 1, 1, 1, 42
    )

    assert meta1["version"] == meta2["version"] == "v1"
    assert len(registry.list_versions("my_ds")) == 1


def test_dataset_registry_new_version_increment(tmp_path):
    registry = DatasetRegistry(base_dir=str(tmp_path / "datasets"))

    f1 = tmp_path / "raw1.jsonl"
    f1.write_text('{"v": 1}\n')
    meta1 = registry.register("ds_inc", str(f1), str(f1), str(f1), 1, 1, 1, 42)
    assert meta1["version"] == "v1"

    f2 = tmp_path / "raw2.jsonl"
    f2.write_text('{"v": 2, "different": true}\n')
    meta2 = registry.register("ds_inc", str(f2), str(f2), str(f2), 2, 1, 1, 42)
    assert meta2["version"] == "v2"

    versions = registry.list_versions("ds_inc")
    assert len(versions) == 2
    assert [v["version"] for v in versions] == ["v1", "v2"]
