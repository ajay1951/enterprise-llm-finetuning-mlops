from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.core.security import get_current_user
from backend.forgellm_api.db.models.experiment import (
    GatewayExperiment,
    ExperimentVariant,
)

router = APIRouter(tags=["A/B Experiments"])


@router.post("/api/v1/experiments")
def create_experiment(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    exp = GatewayExperiment(
        project_id=payload["project_id"],
        model_id=payload["model_id"],
        name=payload["name"],
        status="DRAFT",
    )
    db.add(exp)
    db.flush()

    v_a = ExperimentVariant(
        experiment_id=exp.id,
        model_version_id=payload["model_a_version_id"],
        name=payload.get("name_a", "Variant A"),
        weight=payload.get("weight_a", 50),
    )
    v_b = ExperimentVariant(
        experiment_id=exp.id,
        model_version_id=payload["model_b_version_id"],
        name=payload.get("name_b", "Variant B"),
        weight=payload.get("weight_b", 50),
    )
    db.add_all([v_a, v_b])
    db.commit()

    return {"id": exp.id, "status": exp.status}


@router.get("/api/v1/experiments")
def list_experiments(
    project_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    experiments = (
        db.query(GatewayExperiment)
        .filter(GatewayExperiment.project_id == project_id)
        .all()
    )
    # Serialize for response...
    return [{"id": e.id, "name": e.name, "status": e.status} for e in experiments]


@router.get("/api/v1/experiments/{id}")
def get_experiment(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    exp = db.query(GatewayExperiment).filter(GatewayExperiment.id == id).first()
    if not exp:
        raise HTTPException(404, "Experiment not found")

    variants = (
        db.query(ExperimentVariant).filter(ExperimentVariant.experiment_id == id).all()
    )

    return {
        "id": exp.id,
        "name": exp.name,
        "status": exp.status,
        "variants": [
            {
                "id": v.id,
                "name": v.name,
                "weight": v.weight,
                "requests": v.requests,
                "successful_requests": v.successful_requests,
                "avg_latency_ms": v.avg_latency_ms,
            }
            for v in variants
        ],
    }


@router.post("/api/v1/experiments/{id}/start")
def start_experiment(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    exp = db.query(GatewayExperiment).filter(GatewayExperiment.id == id).first()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    exp.status = "RUNNING"
    db.commit()
    return {"status": "RUNNING"}


@router.post("/api/v1/experiments/{id}/pause")
def pause_experiment(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    exp = db.query(GatewayExperiment).filter(GatewayExperiment.id == id).first()
    if not exp:
        raise HTTPException(404, "Experiment not found")
    exp.status = "PAUSED"
    db.commit()
    return {"status": "PAUSED"}


@router.delete("/api/v1/experiments/{id}")
def delete_experiment(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    exp = db.query(GatewayExperiment).filter(GatewayExperiment.id == id).first()
    if not exp:
        raise HTTPException(404, "Experiment not found")

    # Also delete variants to maintain referential integrity
    db.query(ExperimentVariant).filter(ExperimentVariant.experiment_id == id).delete()
    db.delete(exp)
    db.commit()
    return {"status": "success", "message": "Experiment deleted"}
