import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey

from app.database import Base


class UploadedPolicySnapshot(Base):
    __tablename__ = "uploaded_policy_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    source_file_name = Column(String(255), nullable=False)
    policy_name = Column(String(255), nullable=True)
    sum_assured_amount = Column(Float, nullable=True)
    premium_amount = Column(Float, nullable=True)
    benefits_json = Column(Text, nullable=True, default="[]")
    extracted_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
