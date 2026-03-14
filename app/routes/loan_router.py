from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.loan_schema import LoanCreate, LoanResponse, LoanDetailResponse
from app.services import loan_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/loans", tags=["Loans"])

@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
def create_loan(
    loan: LoanCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return loan_service.create_loan(db=db, loan=loan, collector_id=current_user.id)

@router.get("/", response_model=List[LoanResponse])
def read_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, PAID, DELINQUENT, DEFAULTED, REFINANCED)"),
    search: Optional[str] = Query(None, description="Filter by client name or DNI"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    collector_id: Optional[int] = Query(None, description="Filter by collector ID"),
    min_amount: Optional[float] = Query(None, description="Minimum principal amount"),
    max_amount: Optional[float] = Query(None, description="Maximum principal amount"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loans = loan_service.get_loans(
        db, 
        skip=skip, 
        limit=limit, 
        status=status,
        search=search,
        client_id=client_id, 
        collector_id=collector_id, 
        min_amount=min_amount, 
        max_amount=max_amount
    )
    return loans

@router.get("/{loan_id}", response_model=LoanDetailResponse)
def read_loan(
    loan_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    loan = loan_service.get_loan_with_details(db, loan_id=loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.put("/{loan_id}", response_model=LoanDetailResponse)
def update_loan(
    loan_id: int,
    loan: LoanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return loan_service.update_loan(db=db, loan_id=loan_id, loan_update=loan)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar préstamo: {str(e)}")


@router.delete("/{loan_id}")
def delete_loan(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return loan_service.delete_loan(db=db, loan_id=loan_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar préstamo: {str(e)}")