import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse, ChatSessionOut, UpdateSessionTitleRequest
from app.agents.graph import run_agent_workflow
from app.services.profile_service import get_user_profile, get_latest_profile_snapshot, get_profile_snapshot_by_id
from app.services.policy_service import get_all_policies, serialize_policy_catalog
from app.services.uploaded_policy_service import get_latest_uploaded_policy_snapshot, build_uploaded_policy_context

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Chat & Multi-Agent Assistant"])


@router.post("/query", response_model=ChatQueryResponse)
def handle_chat_query(
    req: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process user query through LangGraph Multi-Agent Assistant pipeline (Router, Coverage RAG, Sales, Comparison, Profile, Chat).
    """
    # 1. Get or Create Session
    session_id = req.session_id
    if not session_id:
        chat_session = ChatSession(user_id=current_user.id, session_title=f"Query: {req.message[:30]}...")
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        session_id = chat_session.id
    else:
        chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
        if not chat_session:
            raise HTTPException(status_code=404, detail="Chat session not found")

    # 2. Get User Profile dict
    profile_obj = get_user_profile(db, current_user.id)
    if req.profile_session_id is not None:
        profile_snapshot = get_profile_snapshot_by_id(db, current_user.id, req.profile_session_id)
        if not profile_snapshot:
            raise HTTPException(status_code=404, detail="Profile session not found")
    else:
        profile_snapshot = get_latest_profile_snapshot(db, current_user.id)

    if profile_snapshot:
        try:
            user_profile_dict = json.loads(profile_snapshot.profile_data)
        except Exception:
            user_profile_dict = {}
    else:
        peds = profile_obj.pre_existing_diseases
        if isinstance(peds, str):
            try:
                peds = json.loads(peds)
            except Exception:
                peds = [peds] if peds else []

        user_profile_dict = {
            "age": profile_obj.age,
            "gender": profile_obj.gender,
            "city": profile_obj.city,
            "city_tier": profile_obj.city_tier,
            "pre_existing_diseases": peds,
            "tobacco_user": profile_obj.tobacco_user,
            "coverage_type": profile_obj.coverage_type,
            "family_members_count": profile_obj.family_members_count,
            "sum_insured_preference": profile_obj.sum_insured_preference,
            "budget_annual_max": profile_obj.budget_annual_max,
            "preferred_room_type": profile_obj.preferred_room_type,
        }
    policy_catalog = serialize_policy_catalog(get_all_policies(db))
    latest_snapshot = get_latest_uploaded_policy_snapshot(db, current_user.id, session_id)
    uploaded_policy_baseline = build_uploaded_policy_context(latest_snapshot, user_profile_dict) if latest_snapshot else None

    # 3. Save User Message to DB
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        content=req.message,
        agent_name="User"
    )
    db.add(user_msg)
    db.commit()

    # Build conversational context for short follow-up intents (e.g., "yes").
    recent_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    conversation_messages = [
        {
            "role": "assistant" if m.sender == "assistant" else "user",
            "content": m.content,
            "agent_name": m.agent_name,
        }
        for m in recent_messages
    ]

    # 4. Invoke LangGraph Multi-Agent Workflow
    agent_output = run_agent_workflow(
        query=req.message,
        messages=conversation_messages,
        user_profile=user_profile_dict,
        policy_catalog=policy_catalog,
        uploaded_policy_baseline=uploaded_policy_baseline,
        filter_company=req.filter_company,
        filter_policy=req.filter_policy,
        claim_amount=req.claim_amount,
        compare_policy_ids=req.compare_policy_ids,
    )

    response_text = agent_output.get("final_response", "Thank you for your question.")
    sources = agent_output.get("sources", [])
    agent_used = agent_output.get("agent_used", "ChatAgent")
    intent = agent_output.get("intent", "FAQ")
    recommended = agent_output.get("recommended_policies")
    comparison = agent_output.get("comparison_table")

    # 5. Save Assistant Message to DB
    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        content=response_text,
        sources=json.dumps(sources),
        agent_name=agent_used
    )
    db.add(assistant_msg)
    db.commit()

    return ChatQueryResponse(
        session_id=session_id,
        message=response_text,
        agent_used=agent_used,
        intent=intent,
        sources=sources,
        recommended_policies=recommended,
        comparison_table=comparison
    )


@router.get("/sessions", response_model=List[ChatSessionOut])
def get_chat_sessions(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Fetch all past chat sessions for current user."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    
    out = []
    for s in sessions:
        msgs_out = []
        for m in s.messages:
            s_list = []
            if m.sources:
                try:
                    s_list = json.loads(m.sources)
                except Exception:
                    s_list = []
            msgs_out.append({
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "sources": s_list,
                "agent_name": m.agent_name,
                "created_at": m.created_at
            })
        out.append({
            "id": s.id,
            "session_title": s.session_title,
            "created_at": s.created_at,
            "messages": msgs_out
        })
    return out


@router.put("/sessions/{session_id}")
def update_chat_session_title(
    session_id: int,
    req: UpdateSessionTitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the title of a specific chat session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session.session_title = req.session_title.strip() or f"Chat Session #{session_id}"
    db.commit()
    db.refresh(session)
    return {"message": "Session title updated", "session_id": session_id, "session_title": session.session_title}


@router.delete("/sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific chat session and all its messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(session)
    db.commit()
    return {"message": f"Session #{session_id} deleted successfully."}


@router.delete("/sessions")
def clear_all_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete all past chat sessions for current user."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()
    session_ids = [s.id for s in sessions]
    if session_ids:
        db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(ChatSession).filter(ChatSession.user_id == current_user.id).delete(synchronize_session=False)
        db.commit()
    return {"message": "All chat history cleared successfully."}


