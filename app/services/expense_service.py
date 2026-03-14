from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import date
from app.models.expense import Expense
from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate
from typing import Optional


def create_expense(db: Session, data: ExpenseCreate, user_id: int) -> Expense:
    expense = Expense(
        description=data.description,
        amount=data.amount,
        category=data.category.upper(),
        notes=data.notes,
        date=data.date or date.today(),
        registered_by=user_id,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def get_expenses(
    db: Session,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(Expense)

    if date_from:
        query = query.filter(Expense.date >= date_from)
    if date_to:
        query = query.filter(Expense.date <= date_to)
    if category:
        query = query.filter(Expense.category == category.upper())

    return query.order_by(Expense.date.desc(), Expense.created_at.desc()).offset(skip).limit(limit).all()


def get_expense_by_id(db: Session, expense_id: int) -> Expense:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Egreso no encontrado")
    return expense


def update_expense(db: Session, expense_id: int, data: ExpenseUpdate) -> Expense:
    expense = get_expense_by_id(db, expense_id)
    update_data = data.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].upper()
    for field, value in update_data.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> None:
    expense = get_expense_by_id(db, expense_id)
    db.delete(expense)
    db.commit()


def get_daily_summary(db: Session, target_date: Optional[date] = None, user_id: Optional[int] = None):
    """
    Retorna el total de egresos y un desglose por categoría para un día específico.
    """
    target = target_date or date.today()

    base_query = db.query(Expense).filter(Expense.date == target)
    if user_id:
        base_query = base_query.filter(Expense.registered_by == user_id)

    expenses = base_query.all()

    total = sum(e.amount for e in expenses)

    # Agrupación por categoría
    by_category = {}
    for e in expenses:
        cat = e.category
        by_category[cat] = by_category.get(cat, 0) + e.amount

    return {
        "date": str(target),
        "total": round(total, 2),
        "count": len(expenses),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
    }
