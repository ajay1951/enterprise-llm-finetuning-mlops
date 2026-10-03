from typing import Any

try:
    import mlflow
    from mlflow.tracking import MlflowClient
except ImportError:  # pragma: no cover
    mlflow = None
    MlflowClient = None


class MLflowModelRegistry:
    def __init__(self, tracking_uri: str = "http://localhost:5000"):
        if mlflow is None or MlflowClient is None:
            raise RuntimeError(
                "MLflow is not installed. Please install mlflow to use MLflowModelRegistry."
            )
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri)

    def register_model(self, run_id: str, model_name: str) -> str:
        """Register a model from a specific run to the Model Registry."""
        model_uri = f"runs:/{run_id}/model_adapter"
        print(f"Registering model {model_name} from {model_uri}...")

        try:
            self.client.create_registered_model(model_name)
        except Exception:  # nosec B110
            pass  # Already exists

        mv = mlflow.register_model(model_uri, model_name)
        print(f"Registered version {mv.version} of {model_name}")
        return mv.version

    def promote_model(self, model_name: str, version: int):
        """Promote a registered model version to Production."""
        print(f"Promoting version {version} of {model_name} to Production alias...")
        self.client.set_registered_model_alias(
            name=model_name, alias="Production", version=str(version)
        )
        print("Promotion successful.")

    def rollback_model(self, model_name: str, target_version: int):
        """Rollback Production to a specific older version."""
        print(
            f"Rolling back to version {target_version} of {model_name} as Production..."
        )
        self.client.set_registered_model_alias(
            name=model_name, alias="Production", version=str(target_version)
        )
        print("Rollback successful.")

    def get_production_version(self, model_name: str) -> Any | None:
        """Fetch the current Production version of a model."""
        try:
            return self.client.get_model_version_by_alias(model_name, "Production")
        except Exception:
            return None

    def list_all_versions(self, model_name: str) -> list[Any]:
        """List all registered versions of a model."""
        try:
            return self.client.search_model_versions(f"name='{model_name}'")
        except Exception:
            return []
