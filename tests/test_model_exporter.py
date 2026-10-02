from unittest.mock import MagicMock, patch

import pytest

from forgellm.models.exporter import ModelExporter


def test_model_exporter_not_found():
    mock_registry = MagicMock()
    mock_registry.get_model.return_value = None

    exporter = ModelExporter(registry=mock_registry)
    with pytest.raises(ValueError, match="not found in registry"):
        exporter.export_merged_model("non_existent:v1", "/tmp/out")


def test_model_exporter_success(tmp_path):
    mock_registry = MagicMock()
    mock_registry.get_model.return_value = {
        "base_model": "Qwen/Qwen2.5-0.5B",
        "location": str(tmp_path / "model_loc"),
    }

    mock_loader = MagicMock()
    mock_base_model = MagicMock()
    mock_loader.load_model.return_value = mock_base_model
    mock_tokenizer = MagicMock()
    mock_loader.load_tokenizer.return_value = mock_tokenizer

    mock_peft_model = MagicMock()
    mock_peft_module = MagicMock()
    mock_peft_module.PeftModel.from_pretrained.return_value = mock_peft_model

    mock_merged = MagicMock()
    mock_peft_model.merge_and_unload.return_value = mock_merged

    out_dir = str(tmp_path / "merged_out")

    with (
        patch("forgellm.models.exporter.ModelLoader", return_value=mock_loader),
        patch.dict("sys.modules", {"peft": mock_peft_module}),
    ):
        exporter = ModelExporter(registry=mock_registry)
        res = exporter.export_merged_model(
            "test_model:v1", out_dir, save_tokenizer=True
        )

    assert res == out_dir
    mock_peft_model.merge_and_unload.assert_called_once()
    mock_merged.save_pretrained.assert_called_once_with(
        out_dir, safe_serialization=True
    )
    mock_tokenizer.save_pretrained.assert_called_once_with(out_dir)
