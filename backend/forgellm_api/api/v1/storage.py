from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import json
from datetime import datetime

from backend.forgellm_api.db.session import get_db
from backend.forgellm_api.db.models.storage import Artifact, ArtifactManifest
from backend.forgellm_api.schemas.storage import ArtifactResponse
from backend.forgellm_api.services.storage_service import get_storage

router = APIRouter(tags=["Artifact Storage"])

@router.post("/projects/{project_id}/artifacts/upload", response_model=ArtifactResponse)
async def upload_artifact(
    project_id: str,
    artifact_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    storage = get_storage()
    
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
        
    try:
        # Calculate checksum
        checksum = storage.checksum(tmp_path)
        size_bytes = os.path.getsize(tmp_path)
        
        # URI format
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
        uri = f"{storage.__class__.__name__.lower().replace('storage', '')}://forgellm/projects/{project_id}/{artifact_type}s/{checksum}{file_ext}"
        
        # Upload
        final_uri = storage.upload(tmp_path, uri)
        
        # Save to DB
        artifact = Artifact(
            project_id=project_id,
            artifact_type=artifact_type,
            uri=final_uri,
            size_bytes=size_bytes,
            checksum=checksum,
            storage_provider="s3" if "S3" in storage.__class__.__name__ else "local"
        )
        db.add(artifact)
        db.flush()
        
        # Create manifest
        manifest_content = {
            "artifact_id": artifact.id,
            "project_id": project_id,
            "type": artifact_type,
            "filename": file.filename,
            "checksum": checksum,
            "size": size_bytes
        }
        manifest = ArtifactManifest(
            artifact_id=artifact.id,
            content=manifest_content
        )
        db.add(manifest)
        db.commit()
        db.refresh(artifact)
        
        return artifact
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/projects/{project_id}/artifacts", response_model=List[ArtifactResponse])
def list_artifacts(project_id: str, db: Session = Depends(get_db)):
    return db.query(Artifact).filter(Artifact.project_id == project_id).all()
