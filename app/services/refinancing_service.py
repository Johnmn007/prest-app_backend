from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.refinancing import Refinancing
from app.models.loan import Loan, Installment
from app.schemas.refinancing_schema import RefinancingCreate
from app.schemas.loan_schema import LoanCreate
from app.services.loan_service import create_loan
from typing import List, Optional
from datetime import date

def calculate_remaining_balance(db: Session, loan_id: int):
    # Sum the remaining amount of unpaid installments
    installments = db.query(Installment).filter(Installment.loan_id == loan_id, Installment.status != "PAID").all()
    balance = sum([round(inst.amount - inst.paid_amount, 2) for inst in installments])
    return balance

def process_refinancing(db: Session, data: RefinancingCreate, collector_id: int):
    # Step 1: Obtener préstamo original
    original_loan = db.query(Loan).filter(Loan.id == data.original_loan_id).first()
    if not original_loan:
        raise HTTPException(status_code=404, detail="Préstamo original no encontrado")

    if original_loan.status in ["REFINANCED"]:
        raise HTTPException(status_code=400, detail="Este préstamo ya fue refinanciado")

    # Step 2: Calcular saldo pendiente real (suma de cuotas no pagadas)
    remaining_balance = calculate_remaining_balance(db, original_loan.id)

    # ── Modalidad 1: RENOVACION ──────────────────────────────────────────────
    # El cliente pagó todo de golpe y solicita un nuevo crédito.
    # No es necesario que quede saldo pendiente (acepta cualquier estado).
    if data.reason == "RENOVACION":
        if data.new_principal_amount <= 0:
            raise HTTPException(status_code=400, detail="Debe indicar el monto del nuevo crédito")
        principal = data.new_principal_amount
        cash_in_hand = principal  # El cliente recibe todo

    # ── Modalidad 2: MORA ─────────────────────────────────────────────────────
    # El crédito venció en mora. La deuda pendiente SE CONVIERTE en el
    # nuevo préstamo. El cliente no recibe dinero en efectivo.
    elif data.reason == "MORA":
        if remaining_balance <= 0:
            raise HTTPException(status_code=400, detail="No hay saldo pendiente para reestructurar")
        principal = remaining_balance
        cash_in_hand = 0.0  # No recibe dinero

    # ── Modalidad 3: MORA_CAPITAL ─────────────────────────────────────────────
    # El cliente tiene deuda pendiente pero quiere un crédito mayor.
    # La deuda se absorbe dentro del nuevo monto. Recibe la diferencia en mano.
    elif data.reason == "MORA_CAPITAL":
        if remaining_balance <= 0:
            raise HTTPException(status_code=400, detail="No hay saldo pendiente para absorber")
        if data.new_principal_amount <= remaining_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Para esta modalidad el nuevo monto (S/ {data.new_principal_amount}) "
                       f"debe ser mayor a la deuda pendiente (S/ {round(remaining_balance, 2)})"
            )
        principal = data.new_principal_amount
        cash_in_hand = round(data.new_principal_amount - remaining_balance, 2)

    else:
        raise HTTPException(status_code=400, detail="Motivo inválido. Use: RENOVACION, MORA o MORA_CAPITAL")

    # Step 3: Crear el nuevo préstamo
    new_loan_data = LoanCreate(
        client_id=original_loan.client_id,
        principal_amount=principal,
        interest_rate=data.new_interest_rate,
        installments=data.new_installments,
        start_date=date.today()
    )
    new_loan = create_loan(db=db, loan=new_loan_data, collector_id=collector_id)

    # Step 4: Registrar evento de refinanciamiento
    refinancing = Refinancing(
        original_loan_id=original_loan.id,
        new_loan_id=new_loan.id,
        reason=data.reason,
        remaining_balance=remaining_balance,
        new_interest_rate=data.new_interest_rate
    )
    db.add(refinancing)

    # Step 5: Cerrar el préstamo original y marcar cuotas pendientes
    original_loan.status = "REFINANCED"
    pending_installments = db.query(Installment).filter(
        Installment.loan_id == original_loan.id,
        Installment.status.notin_(["PAID", "LATE"])
    ).all()
    for inst in pending_installments:
        inst.status = "REFINANCED"

    db.commit()
    db.refresh(refinancing)
    return refinancing


def get_refinancings(db: Session, skip: int = 0, limit: int = 100, original_loan_id: Optional[int] = None):
    query = db.query(Refinancing)
    if original_loan_id:
        query = query.filter(Refinancing.original_loan_id == original_loan_id)
    return query.offset(skip).limit(limit).all()
