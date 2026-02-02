"""Audit logging model."""


from sqlalchemy import JSON, Column, String, Text
from app.models.base import BaseModel

class AuditLog(BaseModel):

    __tablename__ = "audit_logs"

    user_id = Column(String(36), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)