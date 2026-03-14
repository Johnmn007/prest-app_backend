from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.client_schema import ClientCreate, ClientUpdate, ClientResponse
from app.services import client_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client: ClientCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = client_service.get_client_by_dni(db, dni=client.dni)
    if db_client:
        raise HTTPException(status_code=400, detail="Client with this DNI already exists")
    return client_service.create_client(db=db, client=client)

@router.get("/", response_model=List[ClientResponse])
def read_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by full name"),
    dni: Optional[str] = Query(None, description="Exact match DNI"),
    phone: Optional[str] = Query(None, description="Search by phone number"),
    risk_score: Optional[str] = Query(None, description="Filter by risk score (VERDE, NORMAL, AMARILLO, ROJO, NEGRO)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clients = client_service.get_clients(
        db, skip=skip, limit=limit, search=search, dni=dni, phone=phone, risk_score=risk_score
    )
    return clients

@router.get("/{client_id}", response_model=ClientResponse)
def read_client(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = client_service.get_client(db, client_id=client_id)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int, 
    client: ClientUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = client_service.update_client(db, client_id=client_id, client=client)
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        success = client_service.delete_client(db, client_id=client_id)
        if not success:
            raise HTTPException(status_code=404, detail="Client not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
