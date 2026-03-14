from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RefinancingCreate(BaseModel):
    original_loan_id: int
    reason: str # MORA, RENOVACION, REESTRUCTURACION
    new_principal_amount: float # Monto principal para el nuevo prestamo
    new_interest_rate: float
    new_installments: int

class RefinancingResponse(BaseModel):
    id: int
    original_loan_id: int
    new_loan_id: int
    reason: str
    remaining_balance: float
    new_interest_rate: float
    created_at: datetime

    class Config:
        from_attributes = True
