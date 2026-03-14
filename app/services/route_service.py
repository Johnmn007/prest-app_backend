from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.route import Route
from app.models.route_client import RouteClient
from app.models.client import Client
from app.schemas.route_schema import RouteCreate, RouteClientCreate
from typing import List, Optional

def create_route(db: Session, route: RouteCreate):
    db_route = Route(**route.model_dump())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route

def get_routes(db: Session, skip: int = 0, limit: int = 100, collector_id: Optional[int] = None):
    query = db.query(Route)
    if collector_id:
        query = query.filter(Route.collector_id == collector_id)
    return query.offset(skip).limit(limit).all()

def get_route(db: Session, route_id: int):
    return db.query(Route).filter(Route.id == route_id).first()

def assign_client_to_route(db: Session, mapping: RouteClientCreate):
    # Check if route exists
    route = db.query(Route).filter(Route.id == mapping.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Check if client exists
    client = db.query(Client).filter(Client.id == mapping.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # Check if this mapping already exists
    existing = db.query(RouteClient).filter(RouteClient.route_id == mapping.route_id, RouteClient.client_id == mapping.client_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client already assigned to this route")
        
    new_mapping = RouteClient(**mapping.model_dump())
    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)
    return new_mapping

def get_route_clients(db: Session, route_id: int):
    # Return mapping instances joined with clients, ordered by order_index
    route_clients = db.query(RouteClient).filter(RouteClient.route_id == route_id).order_by(RouteClient.order_index).all()
    
    # We populate the client relationship so pydantic schema `RouteClientResponse` can process it
    # For a perfect integration, we could use SQLAlchemy relationship() in the model, but manual population works too
    for rc in route_clients:
        client = db.query(Client).filter(Client.id == rc.client_id).first()
        setattr(rc, "client", client)
        
    return route_clients

def update_route_client_order(db: Session, mapping_id: int, new_order: int):
    mapping = db.query(RouteClient).filter(RouteClient.id == mapping_id).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="Route-Client mapping not found")
    
    mapping.order_index = new_order
    db.commit()
    db.refresh(mapping)
    return mapping
