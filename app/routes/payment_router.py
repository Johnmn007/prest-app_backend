from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.payment_schema import PaymentCreate, PaymentResponse
from app.services import payment_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/", response_model=List[PaymentResponse], status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return payment_service.process_payment(db=db, payment_data=payment, collector_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error processing payment: {str(e)}")

@router.get("/", response_model=List[PaymentResponse])
def read_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    loan_id: Optional[int] = Query(None, description="Filter payments by loan ID"),
    collector_id: Optional[int] = Query(None, description="Filter payments by collector ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payments = payment_service.get_payments(
        db, skip=skip, limit=limit, loan_id=loan_id, collector_id=collector_id
    )
    return payments
