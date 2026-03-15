import logging
from sqlalchemy.orm import Session
from app.models.loan import Loan, Installment
from app.models.client import Client
from app.schemas.loan_schema import LoanCreate
from datetime import timedelta, date
from typing import Optional

logger = logging.getLogger(__name__)

def generate_installments(db: Session, loan_id: int, num_installments: int, daily_payment_cents: int, start_date: date):
    """
    Genera el cronograma de pagos saltando domingos.
    Usa ISO isocalendar: día 7 = domingo.
    """
    installments_to_add = []
    current_date = start_date
    count = 0

    logger.info(f"Generating {num_installments} installments for loan {loan_id}")

    while count < num_installments:
        current_date += timedelta(days=1)
        if current_date.isocalendar()[2] == 7:  # Domingo
            continue
        count += 1
        installments_to_add.append(Installment(
            loan_id=loan_id,
            installment_number=count,
            due_date=current_date,
            amount=daily_payment_cents / 100,
            paid_amount=0.0,
            status="PENDING",
        ))

    db.add_all(installments_to_add)
    db.query(Loan).filter(Loan.id == loan_id).update({"end_date": current_date})
    db.commit()

def create_loan(db: Session, loan: LoanCreate, collector_id: int):
    """
    Crea el préstamo principal y dispara la generación de cuotas exactas.
    """
    principal_cents = int(round(loan.principal_amount * 100))
    interest_cents = int(round(principal_cents * loan.interest_rate)) 
    total_debt_cents = principal_cents + interest_cents
    daily_payment_cents = total_debt_cents // loan.installments
    
    db_loan = Loan(
        client_id=loan.client_id,
        collector_id=collector_id,
        principal_amount=loan.principal_amount,
        interest_rate=loan.interest_rate,
        total_amount=total_debt_cents / 100,
        daily_payment=daily_payment_cents / 100,
        installments=loan.installments,
        paid_installments=0,
        start_date=loan.start_date,
        end_date=loan.start_date,
        status="ACTIVE"
    )
    
    db.add(db_loan)
    db.commit()
    db.refresh(db_loan)
    
    generate_installments(db, db_loan.id, db_loan.installments, daily_payment_cents, db_loan.start_date)
    
    return get_loan_with_details(db, db_loan.id)


def update_loan(db: Session, loan_id: int, loan_update: LoanCreate):
    """
    Edita un préstamo solo si no tiene pagos registrados.
    Regenera el cronograma de cuotas desde cero.
    """
    from fastapi import HTTPException
    from app.models.payment import Payment

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    # Validar que no haya pagos registrados
    payment_count = db.query(Payment).filter(Payment.loan_id == loan_id).count()
    if payment_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede editar: este préstamo ya tiene {payment_count} pago(s) registrado(s). Use refinanciamiento."
        )

    # Recalcular
    principal_cents = int(round(loan_update.principal_amount * 100))
    interest_cents = int(round(principal_cents * loan_update.interest_rate))
    total_debt_cents = principal_cents + interest_cents
    daily_payment_cents = total_debt_cents // loan_update.installments

    # Actualizar campos del préstamo
    loan.client_id = loan_update.client_id
    loan.principal_amount = loan_update.principal_amount
    loan.interest_rate = loan_update.interest_rate
    loan.total_amount = total_debt_cents / 100
    loan.daily_payment = daily_payment_cents / 100
    loan.installments = loan_update.installments
    loan.paid_installments = 0
    loan.start_date = loan_update.start_date
    loan.end_date = loan_update.start_date  # Se recalculará
    loan.status = "ACTIVE"

    # Eliminar cuotas antiguas y regenerar
    db.query(Installment).filter(Installment.loan_id == loan_id).delete()
    db.commit()

    generate_installments(db, loan.id, loan.installments, daily_payment_cents, loan.start_date)

    return get_loan_with_details(db, loan.id)


def delete_loan(db: Session, loan_id: int):
    """
    Elimina un préstamo solo si no tiene pagos registrados.
    Las cuotas se eliminan en cascada (configurado en el modelo).
    """
    from fastapi import HTTPException
    from app.models.payment import Payment

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")

    payment_count = db.query(Payment).filter(Payment.loan_id == loan_id).count()
    if payment_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar: este préstamo tiene {payment_count} pago(s) registrado(s). Solo se pueden eliminar préstamos sin cobros."
        )

    db.delete(loan)
    db.commit()
    return {"message": "Préstamo eliminado correctamente", "id": loan_id}

def get_loans(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None, 
              search: Optional[str] = None,
              client_id: Optional[int] = None, collector_id: Optional[int] = None,
              min_amount: Optional[float] = None, max_amount: Optional[float] = None):
    # Unimos con Client para obtener el full_name del cliente en el listado
    query = db.query(Loan, Client.full_name).outerjoin(Client, Loan.client_id == Client.id)
    
    if status: query = query.filter(Loan.status == status)
    if client_id: query = query.filter(Loan.client_id == client_id)
    if collector_id: query = query.filter(Loan.collector_id == collector_id)
    if min_amount is not None: query = query.filter(Loan.principal_amount >= min_amount)
    if max_amount is not None: query = query.filter(Loan.principal_amount <= max_amount)
    # Búsqueda por nombre completo o DNI del cliente
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Client.full_name.ilike(search_pattern)) | (Client.dni.ilike(search_pattern))
        )
    
    results = query.order_by(Loan.created_at.desc()).offset(skip).limit(limit).all()
    
    # Asignamos el nombre del cliente de forma dinámica al objeto Loan devuelto a la API
    loans = []
    for db_loan, client_name in results:
        setattr(db_loan, "client_name", client_name)
        loans.append(db_loan)
        
    return loans

def get_loan_with_details(db: Session, loan_id: int):
    """
    Obtiene el préstamo con el nombre del cliente y sus cuotas ordenadas.
    """
    result = db.query(Loan, Client.full_name).join(
        Client, Loan.client_id == Client.id
    ).filter(Loan.id == loan_id).first()
    
    if not result:
        return None
        
    db_loan, client_full_name = result
    
    installments = db.query(Installment).filter(
        Installment.loan_id == loan_id
    ).order_by(Installment.installment_number).all()
    
    setattr(db_loan, "client_name", client_full_name)
    setattr(db_loan, "installment_details", installments)
    
    return db_loan