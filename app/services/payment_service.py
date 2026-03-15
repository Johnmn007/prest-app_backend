import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.payment import Payment
from app.models.loan import Loan, Installment
from app.schemas.payment_schema import PaymentCreate
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def process_payment(db: Session, payment_data: PaymentCreate, collector_id: int):
    """Procesa un pago distribuyéndolo en cuotas pendientes. Operación atómica."""
    loan = db.query(Loan).filter(Loan.id == payment_data.loan_id).with_for_update().first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.status == "PAID":
        raise HTTPException(status_code=400, detail="Loan is already fully paid")

    if payment_data.payment_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    installments = (
        db.query(Installment)
        .filter(Installment.loan_id == payment_data.loan_id, Installment.status != "PAID")
        .order_by(Installment.installment_number)
        .all()
    )

    if not installments:
        raise HTTPException(status_code=400, detail="No pending installments found")

    amount_to_distribute = payment_data.payment_amount
    payments_made = []
    today = datetime.now().date()

    try:
        for installment in installments:
            if amount_to_distribute <= 0:
                break

            remaining = installment.amount - installment.paid_amount
            if remaining <= 0.01:
                continue

            applied = min(amount_to_distribute, remaining)
            installment.paid_amount += applied
            amount_to_distribute -= applied

            if installment.paid_amount >= (installment.amount - 0.01):
                loan.paid_installments += 1
                due = installment.due_date if isinstance(installment.due_date, type(today)) else installment.due_date.date()
                installment.status = "LATE" if due < today else "PAID"
            else:
                installment.status = "PENDING"

            payment = Payment(
                loan_id=loan.id,
                installment_id=installment.id,
                payment_amount=applied,
                collector_id=collector_id,
                payment_type=payment_data.payment_type,
            )
            db.add(payment)
            payments_made.append(payment)

        if not payments_made:
            raise HTTPException(status_code=400, detail="Payment too small or already fully paid")

        if loan.paid_installments >= loan.installments:
            loan.status = "PAID"

        db.commit()

        for p in payments_made:
            db.refresh(p)

        logger.info(f"Payment processed: loan={loan.id}, amount={payment_data.payment_amount}, collector={collector_id}")
        return payments_made

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing payment for loan {payment_data.loan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing payment")


def get_payments(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    loan_id: Optional[int] = None,
    collector_id: Optional[int] = None,
):
    query = db.query(Payment)
    if loan_id:
        query = query.filter(Payment.loan_id == loan_id)
    if collector_id:
        query = query.filter(Payment.collector_id == collector_id)
    return query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()
