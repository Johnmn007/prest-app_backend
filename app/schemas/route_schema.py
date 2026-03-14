from pydantic import BaseModel
from typing import Optional, List
from app.schemas.client_schema import ClientResponse

class RouteBase(BaseModel):
    name: str
    zone: Optional[str] = None

class RouteCreate(RouteBase):
    collector_id: int

class RouteResponse(RouteBase):
    id: int
    collector_id: int

    class Config:
        from_attributes = True

class RouteClientBase(BaseModel):
    client_id: int
    order_index: int = 0

class RouteClientCreate(RouteClientBase):
    route_id: int

class RouteClientResponse(RouteClientBase):
    id: int
    route_id: int
    client: ClientResponse

    class Config:
        from_attributes = True
