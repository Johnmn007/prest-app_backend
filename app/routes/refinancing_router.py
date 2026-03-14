from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.schemas.refinancing_schema import RefinancingCreate, RefinancingResponse
from app.services import refinancing_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/refinancings", tags=["Refinancings"])

@router.post("/", response_model=RefinancingResponse, status_code=status.HTTP_201_CREATED)
def create_refinancing(
    refinancing: RefinancingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return refinancing_service.process_refinancing(db=db, data=refinancing, collector_id=current_user.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error processing refinancing: {str(e)}")

@router.get("/", response_model=List[RefinancingResponse])
def read_refinancings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    original_loan_id: Optional[int] = Query(None, description="Filter by original loan ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    refinancings = refinancing_service.get_refinancings(
        db, skip=skip, limit=limit, original_loan_id=original_loan_id
    )
    return refinancings
