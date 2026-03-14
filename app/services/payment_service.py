from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.payment import Payment
from app.models.loan import Loan, Installment
from app.schemas.payment_schema import PaymentCreate
from typing import Optional
from datetime import datetime

def process_payment(db: Session, payment_data: PaymentCreate, collector_id: int):
    loan = db.query(Loan).filter(Loan.id == payment_data.loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    if loan.status == "PAID":
        raise HTTPException(status_code=400, detail="Loan is already fully paid")

    if payment_data.payment_amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than zero")

    amount_to_distribute = payment_data.payment_amount
    payments_made = []

    # Filtramos cuotas que no están completamente pagadas (PENDING, LATE u otros)
    installments = db.query(Installment).filter(
        Installment.loan_id == payment_data.loan_id,
        Installment.status != "PAID"
    ).order_by(Installment.installment_number).all()

    if not installments:
        raise HTTPException(status_code=400, detail="No pending installments found")

    today = datetime.now().date()

    for installment in installments:
        if amount_to_distribute <= 0:
            break

        remaining_in_inst = installment.amount - installment.paid_amount
        if remaining_in_inst <= 0.01:
            continue

        payment_for_this = min(amount_to_distribute, remaining_in_inst)
        
        installment.paid_amount += payment_for_this
        amount_to_distribute -= payment_for_this

        # Verificamos si la cuota se pagó completa (con tolerancia)
        if installment.paid_amount >= (installment.amount - 0.01):
            loan.paid_installments += 1
            
            # Si el día en que se debió pagar es menor a HOY, y la terminan de pagar hoy, es LATE
            inst_due = installment.due_date.date() if isinstance(installment.due_date, datetime) else installment.due_date
            if inst_due < today:
                installment.status = "LATE"
            else:
                installment.status = "PAID"
        else:
            # Sigue pendiente pero con saldo abonado
            installment.status = "PENDING"

        payment = Payment(
            loan_id=loan.id,
            installment_id=installment.id,
            payment_amount=payment_for_this,
            collector_id=collector_id,
            payment_type=payment_data.payment_type
        )
        db.add(payment)
        payments_made.append(payment)

    if loan.paid_installments >= loan.installments:
        loan.status = "PAID"

    db.commit()

    if not payments_made:
        raise HTTPException(status_code=400, detail="Payment too small or fully paid already")

    for p in payments_made:
        db.refresh(p)
    db.refresh(loan)

    return payments_made

def get_payments(db: Session, skip: int = 0, limit: int = 100, loan_id: Optional[int] = None, collector_id: Optional[int] = None):
    query = db.query(Payment)
    if loan_id:
        query = query.filter(Payment.loan_id == loan_id)
    if collector_id:
        query = query.filter(Payment.collector_id == collector_id)
    return query.order_by(Payment.payment_date.desc()).offset(skip).limit(limit).all()