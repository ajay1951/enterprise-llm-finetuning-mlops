from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.forgellm_api.db.session import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "ForgeLLM API"}

@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    try:
        # Check database
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
        
    return {"status": "ready", "database": "connected"}
