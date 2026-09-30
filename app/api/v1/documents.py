from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatSession
from app.models.user import User
from app.schemas.uploaded_policy import UploadedPolicyContext, UploadedPolicyUploadResponse
from app.services.uploaded_policy_service import (
    build_uploaded_policy_context,
    extract_uploaded_policy_metadata,
    save_uploaded_policy_snapshot,
)

router = APIRouter(prefix="/documents", tags=["Uploaded Policy Documents"])


@router.post("/upload-policy", response_model=UploadedPolicyUploadResponse)
async def upload_policy_document(
    file: UploadFile = File(...),
    session_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a user's existing policy document and extract structured comparison data."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Please upload a valid PDF or text document.")

    lower_name = file.filename.lower()
    if not (lower_name.endswith(".pdf") or lower_name.endswith(".txt") or (file.content_type or "").lower() in {"application/pdf", "text/plain"}):
        raise HTTPException(status_code=400, detail="Only PDF or TXT policy documents are supported.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded document appears to be empty.")

    chat_session_id = session_id
    if chat_session_id is not None:
        chat_session = db.query(ChatSession).filter(ChatSession.id == chat_session_id, ChatSession.user_id == current_user.id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        chat_session = ChatSession(user_id=current_user.id, session_title=f"Upload: {file.filename[:30]}...")
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        chat_session_id = chat_session.id

    extracted = extract_uploaded_policy_metadata(file.filename, file_bytes, file.content_type)
    snapshot = save_uploaded_policy_snapshot(db, current_user.id, chat_session_id, file.filename, extracted)
    context = build_uploaded_policy_context(snapshot, {})

    return UploadedPolicyUploadResponse(
        message="Policy document analyzed successfully.",
        session_id=chat_session_id,
        snapshot=UploadedPolicyContext(
            id=snapshot.id,
            source_file_name=snapshot.source_file_name,
            policy_name=snapshot.policy_name,
            sum_assured_amount=snapshot.sum_assured_amount,
            premium_amount=snapshot.premium_amount,
            benefits=context["benefits"],
            recommendation_window={
                "premium_floor": context.get("premium_floor"),
                "premium_ceiling": context.get("premium_ceiling"),
                "target_sum_insured": context.get("target_sum_insured"),
            },
            extracted_summary=context["extracted_summary"],
            created_at=snapshot.created_at,
        ),
    )
