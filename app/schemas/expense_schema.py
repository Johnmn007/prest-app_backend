from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

VALID_CATEGORIES = ["TRANSPORTE", "MANTENIMIENTO", "ADMINISTRATIVO", "VARIOS"]

class ExpenseCreate(BaseModel):
    description: str = Field(..., min_length=3, max_length=255)
    amount: float = Field(..., gt=0)
    category: str = Field(default="VARIOS")
    notes: Optional[str] = Field(default=None, max_length=500)
    date: Optional[date] = None  # Si no se envía, se usa la fecha de hoy

class ExpenseUpdate(BaseModel):
    description: Optional[str] = Field(default=None, min_length=3, max_length=255)
    amount: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=500)
    date: Optional[date] = None

class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float
    category: str
    notes: Optional[str]
    date: date
    created_at: datetime
    registered_by: Optional[int]

    class Config:
        from_attributes = True
