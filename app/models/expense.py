from sqlalchemy import Column, Integer, Float, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    description  = Column(String(255), nullable=False)
    amount       = Column(Float, nullable=False)
    category     = Column(String(50), nullable=False, default="VARIOS")
    # TRANSPORTE | MANTENIMIENTO | ADMINISTRATIVO | VARIOS
    notes        = Column(String(500), nullable=True)
    date         = Column(Date, nullable=False, server_default=func.current_date())
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relación para saber quién la registró
    user = relationship("User", foreign_keys=[registered_by])
