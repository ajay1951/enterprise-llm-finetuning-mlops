from unittest.mock import MagicMock, patch

import pytest

from forgellm.models.mlflow_registry import MLflowModelRegistry


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_mlflow_registry_init(mock_mlflow, mock_client_cls):
    registry = MLflowModelRegistry("http://custom-mlflow:5000")
    mock_mlflow.set_tracking_uri.assert_called_once_with("http://custom-mlflow:5000")
    mock_client_cls.assert_called_once_with("http://custom-mlflow:5000")
    assert registry.client is not None


@patch("forgellm.models.mlflow_registry.mlflow", None)
def test_mlflow_registry_init_not_installed():
    with pytest.raises(RuntimeError, match="MLflow is not installed"):
        MLflowModelRegistry("http://custom-mlflow:5000")


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_register_model_new(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_mv = MagicMock()
    mock_mv.version = "1"
    mock_mlflow.register_model.return_value = mock_mv

    registry = MLflowModelRegistry()
    version = registry.register_model("run-abc-123", "customer-support-llm")

    mock_client.create_registered_model.assert_called_once_with("customer-support-llm")
    mock_mlflow.register_model.assert_called_once_with(
        "runs:/run-abc-123/model_adapter", "customer-support-llm"
    )
    assert version == "1"


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_register_model_existing_duplicate(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client.create_registered_model.side_effect = Exception("Model already exists")
    mock_client_cls.return_value = mock_client

    mock_mv = MagicMock()
    mock_mv.version = "2"
    mock_mlflow.register_model.return_value = mock_mv

    registry = MLflowModelRegistry()
    version = registry.register_model("run-xyz-456", "existing-model")

    # Should gracefully catch the create exception and still register the model version
    mock_mlflow.register_model.assert_called_once_with(
        "runs:/run-xyz-456/model_adapter", "existing-model"
    )
    assert version == "2"


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_promote_model(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    registry.promote_model("customer-support-llm", 3)

    mock_client.set_registered_model_alias.assert_called_once_with(
        name="customer-support-llm", alias="Production", version="3"
    )


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_rollback_model(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    registry.rollback_model("customer-support-llm", 1)

    mock_client.set_registered_model_alias.assert_called_once_with(
        name="customer-support-llm", alias="Production", version="1"
    )


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_get_production_version_success(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_version = MagicMock(name="v2", version="2")
    mock_client.get_model_version_by_alias.return_value = mock_version
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    prod_version = registry.get_production_version("customer-support-llm")

    mock_client.get_model_version_by_alias.assert_called_once_with(
        "customer-support-llm", "Production"
    )
    assert prod_version == mock_version


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_get_production_version_not_found(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client.get_model_version_by_alias.side_effect = Exception("Alias not found")
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    prod_version = registry.get_production_version("unregistered-model")

    assert prod_version is None


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_list_all_versions_success(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_versions = [MagicMock(version="1"), MagicMock(version="2")]
    mock_client.search_model_versions.return_value = mock_versions
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    versions = registry.list_all_versions("customer-support-llm")

    mock_client.search_model_versions.assert_called_once_with(
        "name='customer-support-llm'"
    )
    assert len(versions) == 2


@patch("forgellm.models.mlflow_registry.MlflowClient")
@patch("forgellm.models.mlflow_registry.mlflow")
def test_list_all_versions_failure(mock_mlflow, mock_client_cls):
    mock_client = MagicMock()
    mock_client.search_model_versions.side_effect = Exception("Search error")
    mock_client_cls.return_value = mock_client

    registry = MLflowModelRegistry()
    versions = registry.list_all_versions("customer-support-llm")

    assert versions == []
