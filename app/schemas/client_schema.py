from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    full_name: str
    dni: str
    phone: Optional[str] = None
    address: Optional[str] = None
    reference_address: Optional[str] = None
    gps_location: Optional[str] = None
    risk_score: str = "NORMAL"
    active: bool = True

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    full_name: Optional[str] = None
    dni: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    reference_address: Optional[str] = None
    gps_location: Optional[str] = None
    risk_score: Optional[str] = None
    active: Optional[bool] = None

class ClientResponse(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
