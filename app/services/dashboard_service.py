from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
from app.models.loan import Loan, Installment
from app.models.client import Client
from app.models.payment import Payment

def get_dashboard_metrics(db: Session, collector_id: int = None, start_date: date = None, end_date: date = None):
    """
    Métricas para los cuadros estadísticos del Dashboard.
    """
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = date.today()
        
    start_time = datetime.combine(start_date, datetime.min.time())
    end_time = datetime.combine(end_date, datetime.max.time())

    # Cartera Total Activa
    portfolio_query = db.query(func.sum(Installment.amount - Installment.paid_amount))\
        .join(Loan).filter(Loan.status.in_(["ACTIVE", "DELINQUENT"]), Installment.status != "PAID")
    
    if collector_id:
        portfolio_query = portfolio_query.filter(Loan.collector_id == collector_id)
    
    total_portfolio = portfolio_query.scalar() or 0.0

    # Total de Préstamos Activos
    loan_count_query = db.query(Loan).filter(Loan.status.in_(["ACTIVE", "DELINQUENT"]))
    if collector_id:
        loan_count_query = loan_count_query.filter(Loan.collector_id == collector_id)
    
    total_active_loans = loan_count_query.count()

    # Recaudación del día
    payment_query = db.query(func.sum(Payment.payment_amount))\
        .filter(Payment.payment_date.between(start_time, end_time))
    
    if collector_id:
        payment_query = payment_query.filter(Payment.collector_id == collector_id)
        
    daily_income = payment_query.scalar() or 0.0

    # Capital en Riesgo y Clientes Morosos
    # Mora REAL = cuotas con fecha vencida (due_date < hoy) que aún NO están pagadas
    today = date.today()

    late_installments_query = db.query(func.sum(Installment.amount - Installment.paid_amount))\
        .join(Loan).filter(
            Installment.due_date < today,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"]),
            Loan.status.notin_(["PAID", "REFINANCED"])
        )

    if collector_id:
        late_installments_query = late_installments_query.filter(Loan.collector_id == collector_id)

    capital_at_risk = late_installments_query.scalar() or 0.0

    # Clientes únicos con al menos una cuota vencida sin pagar
    delinquent_clients_count = db.query(Loan.client_id)\
        .join(Installment, Loan.id == Installment.loan_id)\
        .filter(
            Installment.due_date < today,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"]),
            Loan.status.notin_(["PAID", "REFINANCED"])
        ).distinct()

    if collector_id:
        delinquent_clients_count = delinquent_clients_count.filter(Loan.collector_id == collector_id)

    total_delinquent_clients = delinquent_clients_count.count()

    # Ganancia Estimada
    profit_query = db.query(func.sum(Loan.total_amount - Loan.principal_amount))\
        .filter(Loan.status.in_(["ACTIVE", "DELINQUENT"]))
    
    if collector_id:
        profit_query = profit_query.filter(Loan.collector_id == collector_id)
        
    estimated_profit = profit_query.scalar() or 0.0

    meta_diaria = (total_portfolio / 24) if total_portfolio > 0 else 1
    performance_index = (daily_income / meta_diaria) * 100

    return {
        "total_portfolio": round(total_portfolio, 2),
        "total_active_loans": total_active_loans,
        "daily_income": round(daily_income, 2),
        "total_delinquent_clients": total_delinquent_clients,
        "capital_at_risk": round(capital_at_risk, 2),
        "estimated_profit": round(estimated_profit, 2),
        "performance_index": round(min(performance_index, 100), 2)
    }

# --- NUEVA FUNCIÓN: HOJA DE RUTA DE COBRANZA ---

def get_collection_roadmap(db: Session, collector_id: int = None):
    """
    Lista los préstamos activos que:
    - Tienen cuota programada para hoy, O
    - Tienen cuotas en mora (vencidas y sin pagar).
    Incluye today_paid / today_paid_amount para separar pendientes de cobrados.
    """
    today = date.today()

    query = db.query(
        Loan.id,
        Loan.daily_payment,
        Client.full_name.label("client_name"),
        Client.phone,
        Client.dni,
    ).join(Client, Loan.client_id == Client.id)\
     .filter(Loan.status.in_(["ACTIVE", "DELINQUENT"]))

    if collector_id:
        query = query.filter(Loan.collector_id == collector_id)

    results = query.all()
    roadmap = []

    for r in results:
        # Cuota programada para HOY
        today_inst = db.query(Installment).filter(
            Installment.loan_id == r.id,
            Installment.due_date == today,
            Installment.status != "PAID"
        ).first()

        # Cuotas en mora: vencidas (due_date < hoy) y no pagadas
        overdue_installments = db.query(Installment).filter(
            Installment.loan_id == r.id,
            Installment.due_date < today,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"])
        ).all()

        # Cuotas marcadas como LATE (ya pagadas tardíamente - historial)
        late_paid = db.query(func.count(Installment.id)).filter(
            Installment.loan_id == r.id,
            Installment.status == "LATE"
        ).scalar() or 0

        overdue_count = len(overdue_installments)
        overdue_amount = sum(i.amount - i.paid_amount for i in overdue_installments)

        # Solo aparece en la ruta si tiene cuota hoy O tiene mora pendiente
        has_today = today_inst is not None
        has_overdue = overdue_count > 0

        if not has_today and not has_overdue:
            continue

        # Deuda total del préstamo (todas las cuotas no pagadas)
        total_pending_row = db.query(
            func.sum(Installment.amount - Installment.paid_amount)
        ).filter(
            Installment.loan_id == r.id,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"])
        ).scalar() or 0.0

        # ── Pagos registrados HOY para este préstamo ────────────────────────
        today_start = datetime.combine(today, datetime.min.time())
        today_end   = datetime.combine(today, datetime.max.time())

        today_paid_amount = db.query(func.sum(Payment.payment_amount)).filter(
            Payment.loan_id == r.id,
            Payment.payment_date.between(today_start, today_end)
        ).scalar() or 0.0

        roadmap.append({
            "loan_id": r.id,
            "client_name": r.client_name,
            "client_dni": r.dni,
            "phone": r.phone,
            "daily_payment": float(r.daily_payment),
            "has_today_installment": has_today,
            "today_amount": float(today_inst.amount - today_inst.paid_amount) if today_inst else 0.0,
            "overdue_count": overdue_count,
            "overdue_amount": round(float(overdue_amount), 2),
            "late_paid_count": late_paid,
            "total_pending": round(float(total_pending_row), 2),
            # ── Nuevos campos ────────────────────────────────────────────
            "today_paid_amount": round(float(today_paid_amount), 2),
            "today_paid": today_paid_amount > 0,
        })

    # 1° Pendientes con mora · 2° Pendientes sin mora · 3° Ya cobrados hoy
    roadmap.sort(key=lambda x: (x["today_paid"], -x["overdue_count"], x["client_name"]))
    return roadmap


def get_daily_income_report(db: Session, date_target: date = None):
    if not date_target:
        date_target = date.today()
    start_time = datetime.combine(date_target, datetime.min.time())
    end_time = datetime.combine(date_target, datetime.max.time())
    return db.query(Payment).filter(Payment.payment_date.between(start_time, end_time)).all()


def get_expiring_loans(db: Session, days_threshold: int = 2, collector_id: int = None):
    """
    Retorna préstamos activos cuyo número de cuotas pendientes (no pagadas) es <= days_threshold.
    Incluye: porcentaje de avance, cuotas restantes, monto pendiente y fecha de fin.
    Ordenados de menor a mayor cuotas restantes (los más urgentes primero).
    """
    query = db.query(Loan).join(Client, Loan.client_id == Client.id)\
        .filter(Loan.status.in_(["ACTIVE", "DELINQUENT"]))

    if collector_id:
        query = query.filter(Loan.collector_id == collector_id)

    loans = query.all()
    result = []

    for loan in loans:
        # Cuotas NO pagadas
        pending_installments = db.query(Installment).filter(
            Installment.loan_id == loan.id,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"])
        ).order_by(Installment.due_date.desc()).all()

        remaining_count = len(pending_installments)

        # Solo incluir si tiene pocas cuotas restantes
        if remaining_count > days_threshold:
            continue

        # Monto pendiente total
        pending_amount = sum(i.amount - i.paid_amount for i in pending_installments)

        # Fecha de la última cuota pendiente
        last_due_date = pending_installments[0].due_date if pending_installments else loan.end_date

        # Porcentaje completado
        progress_pct = round((loan.paid_installments / loan.installments) * 100, 1) if loan.installments > 0 else 0

        result.append({
            "loan_id": loan.id,
            "client_name": loan.client.full_name,
            "client_dni": loan.client.dni,
            "phone": loan.client.phone,
            "principal_amount": float(loan.principal_amount),
            "total_amount": float(loan.total_amount),
            "daily_payment": float(loan.daily_payment),
            "installments": loan.installments,
            "paid_installments": loan.paid_installments,
            "remaining_installments": remaining_count,
            "pending_amount": round(float(pending_amount), 2),
            "progress_pct": progress_pct,
            "last_due_date": str(last_due_date),
            "end_date": str(loan.end_date),
        })

    # Más urgentes primero (menos cuotas restantes)
    result.sort(key=lambda x: (x["remaining_installments"], x["client_name"]))
    return result


# ── REPORTE 1: Ingresos por rango de fechas ───────────────────────────────────

def get_income_by_range(db: Session, date_from: date, date_to: date):
    """
    Retorna los ingresos totales por día dentro del rango, más el acumulado
    y número de cobros. Útil para graficar tendencias.
    """
    from app.models.expense import Expense

    # Serie de días del rango
    delta = (date_to - date_from).days + 1
    dates = [date_from + timedelta(days=i) for i in range(delta)]

    series = []
    total_acum = 0.0

    for d in dates:
        start = datetime.combine(d, datetime.min.time())
        end   = datetime.combine(d, datetime.max.time())

        day_income = db.query(func.sum(Payment.payment_amount))\
            .filter(Payment.payment_date.between(start, end)).scalar() or 0.0

        day_expenses = db.query(func.sum(Expense.amount))\
            .filter(Expense.date == d).scalar() or 0.0

        day_count = db.query(func.count(Payment.id))\
            .filter(Payment.payment_date.between(start, end)).scalar() or 0

        total_acum += day_income
        series.append({
            "date":        str(d),
            "label":       d.strftime("%d/%m"),
            "income":      round(float(day_income), 2),
            "expenses":    round(float(day_expenses), 2),
            "net":         round(float(day_income - day_expenses), 2),
            "count":       day_count,
            "accumulated": round(total_acum, 2),
        })

    total_income   = sum(s["income"]   for s in series)
    total_expenses = sum(s["expenses"] for s in series)

    return {
        "date_from":       str(date_from),
        "date_to":         str(date_to),
        "total_income":    round(total_income, 2),
        "total_expenses":  round(total_expenses, 2),
        "net_profit":      round(total_income - total_expenses, 2),
        "total_payments":  sum(s["count"] for s in series),
        "series":          series,
    }


# ── REPORTE 2: Resumen de Cartera ─────────────────────────────────────────────

def get_portfolio_summary(db: Session, collector_id: int = None):
    """
    Visión completa de la cartera: distribución por estado, top deudores,
    análisis de mora y estadísticas generales.
    """
    loan_query = db.query(Loan).join(Client, Loan.client_id == Client.id)
    if collector_id:
        loan_query = loan_query.filter(Loan.collector_id == collector_id)

    all_loans = loan_query.all()

    # Distribución por estado
    dist = {}
    for loan in all_loans:
        dist[loan.status] = dist.get(loan.status, 0) + 1

    # Monto total prestado (principal) activo
    active_loans = [l for l in all_loans if l.status in ("ACTIVE", "DELINQUENT")]

    total_principal    = sum(l.principal_amount for l in active_loans)
    total_to_collect   = sum(l.total_amount for l in active_loans)

    # Mora: cuotas vencidas no pagadas
    today = date.today()
    mora_loans = []
    for loan in active_loans:
        overdue = db.query(Installment).filter(
            Installment.loan_id == loan.id,
            Installment.due_date < today,
            Installment.status.notin_(["PAID", "LATE", "REFINANCED"])
        ).all()
        if overdue:
            overdue_amount = sum(i.amount - i.paid_amount for i in overdue)
            mora_loans.append({
                "loan_id":       loan.id,
                "client_name":   loan.client.full_name,
                "phone":         loan.client.phone,
                "overdue_count": len(overdue),
                "overdue_amount": round(float(overdue_amount), 2),
                "total_pending": round(float(loan.total_amount - sum(
                    i.paid_amount for i in loan.installment_details
                )), 2),
                "daily_payment": float(loan.daily_payment),
            })

    mora_loans.sort(key=lambda x: -x["overdue_amount"])

    # Top 10 clientes por deuda pendiente
    client_debt = []
    for loan in active_loans:
        pending = db.query(func.sum(Installment.amount - Installment.paid_amount))\
            .filter(Installment.loan_id == loan.id,
                    Installment.status.notin_(["PAID", "LATE", "REFINANCED"]))\
            .scalar() or 0
        client_debt.append({
            "loan_id":      loan.id,
            "client_name":  loan.client.full_name,
            "principal":    float(loan.principal_amount),
            "pending":      round(float(pending), 2),
            "progress_pct": round((loan.paid_installments / loan.installments) * 100, 1) if loan.installments else 0,
            "daily_payment": float(loan.daily_payment),
            "status":       loan.status,
        })
    client_debt.sort(key=lambda x: -x["pending"])

    return {
        "total_active_loans":   len(active_loans),
        "total_all_loans":      len(all_loans),
        "status_distribution":  dist,
        "total_principal":      round(total_principal, 2),
        "total_to_collect":     round(total_to_collect, 2),
        "total_overdue_loans":  len(mora_loans),
        "overdue_loans":        mora_loans,
        "top_debtors":          client_debt[:10],
    }


# ── REPORTE 3: Cierre de Caja ─────────────────────────────────────────────────

def get_cash_close(db: Session, target_date: date = None):
    """
    Cierre de caja del día: total cobrado, total egresado, utilidad neta,
    desglose de pagos y desglose de egresos por categoría.
    """
    from app.models.expense import Expense

    d = target_date or date.today()
    start = datetime.combine(d, datetime.min.time())
    end   = datetime.combine(d, datetime.max.time())

    # Ingresos del día (todos los pagos)
    payments = db.query(Payment).filter(Payment.payment_date.between(start, end)).all()
    total_income = sum(p.payment_amount for p in payments)

    # Egresos del día
    expenses = db.query(Expense).filter(Expense.date == d).all()
    total_expenses = sum(e.amount for e in expenses)

    # Egresos por categoría
    exp_by_cat = {}
    for e in expenses:
        exp_by_cat[e.category] = exp_by_cat.get(e.category, 0) + e.amount

    # Pagos por tipo
    pay_by_type = {}
    for p in payments:
        pay_by_type[p.payment_type] = pay_by_type.get(p.payment_type, 0) + p.payment_amount

    # Número de préstamos únicos cobrados
    unique_loans_paid = len({p.loan_id for p in payments})

    return {
        "date":              str(d),
        "total_income":      round(float(total_income),   2),
        "total_expenses":    round(float(total_expenses), 2),
        "net_profit":        round(float(total_income - total_expenses), 2),
        "payment_count":     len(payments),
        "unique_loans_paid": unique_loans_paid,
        "expense_count":     len(expenses),
        "income_by_type":    {k: round(float(v), 2) for k, v in pay_by_type.items()},
        "expenses_by_category": {k: round(float(v), 2) for k, v in exp_by_cat.items()},
        "payments":          [
            {
                "id":             p.id,
                "loan_id":        p.loan_id,
                "amount":         float(p.payment_amount),
                "type":           p.payment_type,
                "collector_id":   p.collector_id,
                "time":           p.payment_date.strftime("%H:%M"),
            }
            for p in sorted(payments, key=lambda x: x.payment_date)
        ],
        "expenses_detail": [
            {
                "id":          e.id,
                "description": e.description,
                "amount":      float(e.amount),
                "category":    e.category,
                "notes":       e.notes,
            }
            for e in expenses
        ],
    }
