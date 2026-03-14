from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.route_schema import RouteCreate, RouteResponse, RouteClientCreate, RouteClientResponse
from app.services import route_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(
    route: RouteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return route_service.create_route(db=db, route=route)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/", response_model=List[RouteResponse])
def read_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    collector_id: Optional[int] = Query(None, description="Filter by Collector ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return route_service.get_routes(db, skip=skip, limit=limit, collector_id=collector_id)

@router.post("/assign-client", response_model=RouteClientResponse, status_code=status.HTTP_201_CREATED)
def assign_client(
    mapping: RouteClientCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        mapping_created = route_service.assign_client_to_route(db=db, mapping=mapping)
        
        # Hydrate client relationship manually on creation
        from app.models.client import Client
        client = db.query(Client).filter(Client.id == mapping_created.client_id).first()
        setattr(mapping_created, "client", client)
        
        return mapping_created
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/{route_id}/clients", response_model=List[RouteClientResponse])
def read_route_clients(
    route_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return route_service.get_route_clients(db, route_id=route_id)
