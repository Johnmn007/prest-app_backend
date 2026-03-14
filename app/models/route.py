from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.base import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    zone = Column(String(150))
    collector_id = Column(Integer, ForeignKey("users.id"), nullable=False)
