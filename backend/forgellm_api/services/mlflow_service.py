import mlflow
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MLflowService:
    def __init__(self):
        self.tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
        mlflow.set_tracking_uri(self.tracking_uri)

    def _get_or_create_experiment(self, experiment_name: str) -> str:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
        return experiment_id

    def start_training_run(
        self,
        experiment_name: str,
        run_name: str,
        params: Dict[str, Any],
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Start a training run in MLflow, log params, and return the Run ID.
        """
        try:
            experiment_id = self._get_or_create_experiment(experiment_name)

            run = mlflow.start_run(experiment_id=experiment_id, run_name=run_name)
            if tags:
                mlflow.set_tags(tags)

            mlflow.log_params(params)
            mlflow.end_run()  # End context so we can log to it later incrementally

            return run.info.run_id
        except Exception as e:
            logger.error(f"Failed to start run in MLflow: {e}")
            raise

    def log_metric_step(self, run_id: str, metrics: Dict[str, float], step: int):
        """
        Log metrics at a specific step.
        """
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            logger.error(f"Failed to log metric step to MLflow: {e}")
            raise

    def log_evaluation_metrics(self, run_id: str, metrics: Dict[str, float]):
        """
        Log evaluation metrics to an existing run.
        """
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_metrics(metrics)
        except Exception as e:
            logger.error(f"Failed to log evaluation metrics to MLflow: {e}")
            raise


mlflow_service = MLflowService()
