from pydantic import BaseModel
from typing import Optional
from datetime import date

class InstallmentBase(BaseModel):
    installment_number: int
    due_date: date
    amount: float
    paid_amount: float = 0.0
    status: str = "PENDING"

class InstallmentCreate(InstallmentBase):
    loan_id: int

class InstallmentResponse(InstallmentBase):
    id: int
    loan_id: int

    class Config:
        from_attributes = True
