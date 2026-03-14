from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PaymentBase(BaseModel):
    payment_amount: float
    payment_type: str = "NORMAL" # NORMAL, PARTIAL, EARLY, FULL_SETTLEMENT

class PaymentCreate(PaymentBase):
    loan_id: int
    installment_id: Optional[int] = None

class PaymentResponse(PaymentBase):
    id: int
    loan_id: int
    installment_id: int
    collector_id: int
    payment_date: datetime

    class Config:
        from_attributes = True
