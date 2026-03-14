from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.base import Base

class Refinancing(Base):
    __tablename__ = "refinancings"

    id = Column(Integer, primary_key=True, index=True)
    original_loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    new_loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    reason = Column(String(50), nullable=False) # MORA, RENOVACION, REESTRUCTURACION
    remaining_balance = Column(Float, nullable=False)
    new_interest_rate = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
