from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    dni = Column(String(20), unique=True, index=True, nullable=False)
    phone = Column(String(50))
    address = Column(String(255))
    reference_address = Column(String(255))
    gps_location = Column(String(100))
    risk_score = Column(String(50), default="NORMAL")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIÓN FALTANTE: Permite que SQLAlchemy vea los préstamos desde el cliente
    loans = relationship("Loan", back_populates="client")