from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class AuditLog(Base):
    """
    Immutable records of every write operation performed by a user.
    
    """

    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action     = Column(String(50), nullable=False)   
    entity     = Column(String(50), nullable=False)   
    entity_id  = Column(Integer, nullable=True)
    detail     = Column(Text, nullable=True)         
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", foreign_keys=[user_id])