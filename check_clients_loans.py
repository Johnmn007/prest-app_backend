
from app.database.connection import SessionLocal
from app.models.client import Client
from app.models.loan import Loan

db = SessionLocal()
try:
    clients = db.query(Client).all()
    print(f"{'ID':<5} | {'Name':<20} | {'Active Loans':<12} | {'Total Loans':<12}")
    print("-" * 60)
    for c in clients:
        active_loans = db.query(Loan).filter(Loan.client_id == c.id, Loan.status == 'ACTIVE').count()
        total_loans = db.query(Loan).filter(Loan.client_id == c.id).count()
        print(f"{c.id:<5} | {c.full_name[:20]:<20} | {active_loans:<12} | {total_loans:<12}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
