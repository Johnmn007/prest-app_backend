from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from app.schemas.installment_schema import InstallmentResponse

class LoanBase(BaseModel):
    client_id: int
    principal_amount: float
    interest_rate: float
    installments: int
    start_date: date

class LoanCreate(LoanBase):
    """Esquema para la creación de un nuevo préstamo."""
    pass

class LoanResponse(LoanBase):
    """Esquema de respuesta base para listados y creación."""
    id: int
    collector_id: int
    total_amount: float
    daily_payment: float
    paid_installments: int
    end_date: date
    status: str
    created_at: datetime
    
    # Atributos extendidos para evitar tablas vacías y títulos genéricos
    client_name: Optional[str] = None
    installment_details: List[InstallmentResponse] = []

    class Config:
        from_attributes = True

class LoanDetailResponse(LoanResponse):
    """Esquema detallado para la vista del 'ojito' (hereda todo de LoanResponse)."""
    pass