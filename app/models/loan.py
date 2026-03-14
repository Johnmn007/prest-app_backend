from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    collector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    principal_amount = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    daily_payment = Column(Float, nullable=False)
    installments = Column(Integer, nullable=False)
    paid_installments = Column(Integer, default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    client = relationship("Client", back_populates="loans")
    collector = relationship("User", back_populates="loans") # <-- COINCIDE CON USER
    installment_details = relationship("Installment", back_populates="loan", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="loan")

class Installment(Base):
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    status = Column(String(50), default="PENDING")

    loan = relationship("Loan", back_populates="installment_details")