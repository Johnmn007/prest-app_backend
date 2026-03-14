from sqlalchemy.orm import Session
from app.models.client import Client
from app.schemas.client_schema import ClientCreate, ClientUpdate
from typing import Optional
from app.models.loan import Loan, Installment

def get_client_by_dni(db: Session, dni: str):
    return db.query(Client).filter(Client.dni == dni).first()

def get_client(db: Session, client_id: int):
    return db.query(Client).filter(Client.id == client_id).first()

def get_clients(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    dni: Optional[str] = None,
    phone: Optional[str] = None,
    risk_score: Optional[str] = None
):
    query = db.query(Client).filter(Client.active == True)
    
    if search:
        query = query.filter(Client.full_name.ilike(f"%{search}%"))
    if dni:
        query = query.filter(Client.dni == dni)
    if phone:
        query = query.filter(Client.phone.ilike(f"%{phone}%"))
    if risk_score:
        query = query.filter(Client.risk_score == risk_score)
        
    return query.offset(skip).limit(limit).all()

def create_client(db: Session, client: ClientCreate):
    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, client: ClientUpdate):
    db_client = get_client(db, client_id)
    if not db_client:
        return None
    
    update_data = client.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)
        
    db.commit()
    db.refresh(db_client)
    return db_client


def delete_client(db: Session, client_id: int):
    db_client = get_client(db, client_id)
    if not db_client:
        return False
    
    # Verificar si tiene préstamos activos
    active_loans = db.query(Loan).filter(
        Loan.client_id == client_id,
        Loan.status == "ACTIVE"
    ).count()
    
    if active_loans > 0:
        raise ValueError("No se puede eliminar un cliente con préstamos vigentes")
    
    # Soft delete: lo marcamos como inactivo
    db_client.active = False
    db.commit()
    return True


def update_client_risk_level(db: Session, client_id: int):
    """
    Actualiza el nivel de riesgo del cliente basado en su historial.
    """
    # Contar cuotas vencidas (LATE) de todos sus préstamos
    cuotas_mora = db.query(Installment).join(Loan).filter(
        Loan.client_id == client_id,
        Installment.status == "LATE"
    ).count()
    
    if cuotas_mora == 0:
        nuevo_riesgo = "VERDE"
    elif cuotas_mora <= 3:
        nuevo_riesgo = "AMARILLO"
    elif cuotas_mora <= 10:
        nuevo_riesgo = "ROJO"
    else:
        nuevo_riesgo = "NEGRO"
        
    client = db.query(Client).filter(Client.id == client_id).first()
    if client:
        client.risk_score = nuevo_riesgo
        db.commit()
    return nuevo_riesgo
