import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class DatasetRegistry:
    def __init__(self, base_dir: str = ".forgellm/datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_sha256(self, filepath: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_next_version(self, dataset_name: str) -> str:
        dataset_dir = self.base_dir / dataset_name
        if not dataset_dir.exists():
            return "v1"

        versions = [
            d.name
            for d in dataset_dir.iterdir()
            if d.is_dir() and d.name.startswith("v")
        ]
        if not versions:
            return "v1"

        # Parse version numbers
        v_nums = [int(v[1:]) for v in versions if v[1:].isdigit()]
        if not v_nums:
            return "v1"

        return f"v{max(v_nums) + 1}"

    def get_version_info(
        self, dataset_name: str, version: str
    ) -> dict[str, Any] | None:
        metadata_path = self.base_dir / dataset_name / version / "metadata.json"
        if not metadata_path.exists():
            return None
        with open(metadata_path, "r") as f:
            return json.load(f)

    def list_datasets(self) -> list[str]:
        if not self.base_dir.exists():
            return []
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def list_versions(self, dataset_name: str) -> list[dict[str, Any]]:
        dataset_dir = self.base_dir / dataset_name
        if not dataset_dir.exists():
            return []

        versions = []
        for d in dataset_dir.iterdir():
            if d.is_dir() and d.name.startswith("v"):
                info = self.get_version_info(dataset_name, d.name)
                if info:
                    versions.append(info)

        # Sort by version number
        versions.sort(key=lambda x: int(x["version"][1:]))
        return versions

    def register(
        self,
        dataset_name: str,
        source_path: str,
        train_path: str,
        val_path: str,
        total_examples: int,
        training_examples: int,
        validation_examples: int,
        seed: int,
    ) -> dict[str, Any]:

        sha256 = self._calculate_sha256(source_path)

        # Check if this exact file was already registered as the latest version
        dataset_dir = self.base_dir / dataset_name
        if dataset_dir.exists():
            versions = self.list_versions(dataset_name)
            if versions:
                latest = versions[-1]
                if latest["sha256"] == sha256:
                    return latest  # Skip registration if hash matches exactly

        version = self._get_next_version(dataset_name)
        version_dir = self.base_dir / dataset_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy data files into the registry
        registry_train_path = version_dir / "train.jsonl"
        registry_val_path = version_dir / "val.jsonl"

        shutil.copy2(train_path, registry_train_path)
        if os.path.exists(val_path):
            shutil.copy2(val_path, registry_val_path)

        metadata = {
            "dataset_name": dataset_name,
            "version": version,
            "source": source_path,
            "total_examples": total_examples,
            "training_examples": training_examples,
            "validation_examples": validation_examples,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "sha256": sha256,
            "seed": seed,
            "train_path": str(registry_train_path),
            "val_path": str(registry_val_path),
        }

        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata
