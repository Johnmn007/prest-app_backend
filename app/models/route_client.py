from sqlalchemy import Column, Integer, ForeignKey
from app.database.base import Base

class RouteClient(Base):
    __tablename__ = "route_clients"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)
