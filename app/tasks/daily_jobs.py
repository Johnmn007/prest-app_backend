from sqlalchemy.orm import Session
from datetime import date
from app.models.loan import Loan, Installment

def update_late_installments(db: Session):
    """
    Busca cuotas pendientes cuya fecha de vencimiento ya pasó 
    y las marca como LATE (Vencidas).
    """
    hoy = date.today()
    
    # 1. Encontrar cuotas vencidas
    vencidas = db.query(Installment).filter(
        Installment.due_date < hoy,
        Installment.status == "PENDING"
    ).all()
    
    contador = 0
    prestamos_afectados = set()
    
    for cuota in vencidas:
        cuota.status = "LATE"
        prestamos_afectados.add(cuota.loan_id)
        contador += 1
    
    # 2. Marcar los préstamos como DELINQUENT (Morosos) si tienen cuotas LATE
    if prestamos_afectados:
        db.query(Loan).filter(
            Loan.id.in_(prestamos_afectados),
            Loan.status == "ACTIVE"
        ).update({"status": "DELINQUENT"}, synchronize_session=False)
    
    db.commit()
    return {"cuotas_afectadas": contador, "prestamos_morosos": len(prestamos_afectados)}