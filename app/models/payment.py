from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    installment_id = Column(Integer, ForeignKey("installments.id"), nullable=False)
    collector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_type = Column(String(50), default="NORMAL")

    # Relaciones
    loan = relationship("Loan", back_populates="payments")
    collector = relationship("User", back_populates="payments") # <-- FALTABA ESTA PARA EL SCRIPT