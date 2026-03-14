from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database.connection import get_db
from app.schemas.report_schema import DashboardMetricsResponse
from app.schemas.payment_schema import PaymentResponse
from app.tasks.daily_jobs import update_late_installments
from app.services import dashboard_service
from app.routes.auth_router import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Reports"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def read_metrics(
    collector_id: Optional[int] = Query(None, description="Filter metrics by collector ID"),
    start_date: Optional[date] = Query(None, description="Start date for filtering income"),
    end_date: Optional[date] = Query(None, description="End date for filtering income"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        metrics = dashboard_service.get_dashboard_metrics(
            db, collector_id=collector_id, start_date=start_date, end_date=end_date
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dashboard metrics: {str(e)}")

@router.get("/reports/daily-income", response_model=List[PaymentResponse])
def read_daily_income_report(
    date_target: Optional[date] = Query(None, description="Date for the income report"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Return payments registered across a single target day
        payments = dashboard_service.get_daily_income_report(db, date_target=date_target)
        return payments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building daily report: {str(e)}")

@router.post("/run-mora-check", tags=["Admin Tasks"])
def run_mora_check(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Solo el admin debería poder ejecutar esto manualmente
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    resultado = update_late_installments(db)
    return {"message": "Proceso de mora completado", "detalle": resultado}


@router.get("/collection-roadmap")
def read_collection_roadmap(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    collector_id = None if current_user.role == "admin" else current_user.id
    return dashboard_service.get_collection_roadmap(db, collector_id=collector_id)


@router.get("/expiring-loans")
def read_expiring_loans(
    days_threshold: int = Query(2, description="Cuotas pendientes <= N para considerar 'por vencer'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna préstamos activos con pocas cuotas pendientes (por defecto <= 2).
    Útil para que el cobrador sepa qué créditos están a punto de cerrarse.
    """
    collector_id = None if current_user.role == "admin" else current_user.id
    return dashboard_service.get_expiring_loans(db, days_threshold=days_threshold, collector_id=collector_id)


@router.get("/reports/income-range")
def read_income_range(
    date_from: date = Query(..., description="Fecha inicio"),
    date_to:   date = Query(..., description="Fecha fin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingresos por cobranza agrupados por día dentro de un rango de fechas.
    """
    return dashboard_service.get_income_by_range(db, date_from=date_from, date_to=date_to)


@router.get("/reports/portfolio-summary")
def read_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resumen completo de la cartera: distribución por estado, monto total,
    top clientes por deuda y análisis de mora.
    """
    collector_id = None if current_user.role == "admin" else current_user.id
    return dashboard_service.get_portfolio_summary(db, collector_id=collector_id)


@router.get("/reports/cash-close")
def read_cash_close(
    target_date: Optional[date] = Query(None, description="Fecha del cierre. Por defecto: hoy"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cierre de caja del día: ingresos de cobro, egresos operativos y utilidad neta.
    """
    return dashboard_service.get_cash_close(db, target_date=target_date)
