from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database.connection import get_db
from app.schemas.installment_schema import InstallmentResponse
from app.models.loan import Loan, Installment
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/installments", tags=["Installments"])

@router.get("/pending", response_model=List[InstallmentResponse])
def get_pending_installments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    collector_id: Optional[int] = Query(None, description="Filter by Collector ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Installment).join(Loan).filter(Installment.status.in_(["PENDING", "LATE"]))
    
    if collector_id:
        query = query.filter(Loan.collector_id == collector_id)
        
    # Order by oldest due date first
    installments = query.order_by(Installment.due_date.asc()).offset(skip).limit(limit).all()
    return installments

@router.get("/loan/{loan_id}", response_model=List[InstallmentResponse])
def read_installments_by_loan(
    loan_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    installments = db.query(Installment).filter(Installment.loan_id == loan_id).order_by(Installment.installment_number).all()
    return installments
