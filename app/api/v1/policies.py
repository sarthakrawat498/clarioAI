from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.policy import PolicyOut
from app.services.policy_service import get_all_policies, get_policy_by_id
from app.rag.vector_store import vector_store_manager

router = APIRouter(prefix="/policies", tags=["Policy Catalogue & Documents"])


@router.get("", response_model=List[PolicyOut])
def list_policies(db: Session = Depends(get_db)):
    """Retrieve catalog of available health insurance plans."""
    return get_all_policies(db)


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """Get single policy details by ID."""
    p = get_policy_by_id(db, policy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    return p


@router.post("/ingest-sample-docs")
def trigger_document_ingestion():
    """Trigger sample PDF/TXT policy document ingestion into ChromaDB."""
    vector_store_manager.ingest_all_sample_policies()
    return {"status": "success", "message": "Successfully indexed all policy documents into ChromaDB."}
