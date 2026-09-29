import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ModelRegistry:
    def __init__(self, base_dir: str = ".forgellm/models"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_next_version(self, model_name: str) -> str:
        model_dir = self.base_dir / model_name
        if not model_dir.exists():
            return "v1"

        versions = [
            d.name for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("v")
        ]
        if not versions:
            return "v1"

        v_nums = [int(v[1:]) for v in versions if v[1:].isdigit()]
        if not v_nums:
            return "v1"

        return f"v{max(v_nums) + 1}"

    def register(
        self,
        model_name: str,
        base_model: str,
        method: str,
        dataset_ref: str,
        experiment_id: str,
        status: str = "training",
    ) -> dict[str, Any]:

        version = self._get_next_version(model_name)
        version_dir = self.base_dir / model_name / version
        version_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "model_name": model_name,
            "version": version,
            "base_model": base_model,
            "method": method,
            "dataset": dataset_ref,
            "experiment": experiment_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "location": str(version_dir),
        }

        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    def update_status(self, model_name: str, version: str, status: str):
        meta_path = self.base_dir / model_name / version / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r") as f:
                metadata = json.load(f)
            metadata["status"] = status
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=2)

    def get_model(self, model_name: str, version: str) -> dict[str, Any] | None:
        meta_path = self.base_dir / model_name / version / "metadata.json"
        if not meta_path.exists():
            return None
        with open(meta_path, "r") as f:
            return json.load(f)

    def list_models(self) -> list[str]:
        if not self.base_dir.exists():
            return []
        return [d.name for d in self.base_dir.iterdir() if d.is_dir()]

    def list_versions(self, model_name: str) -> list[dict[str, Any]]:
        model_dir = self.base_dir / model_name
        if not model_dir.exists():
            return []

        versions = []
        for d in model_dir.iterdir():
            if d.is_dir() and d.name.startswith("v"):
                info = self.get_model(model_name, d.name)
                if info:
                    versions.append(info)

        versions.sort(key=lambda x: int(x["version"][1:]))
        return versions
