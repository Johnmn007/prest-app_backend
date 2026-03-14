
from app.database.connection import SessionLocal
from app.models.client import Client
from app.models.loan import Loan

db = SessionLocal()
with open("clients_debug.txt", "w") as f:
    try:
        clients = db.query(Client).all()
        f.write(f"{'ID':<5} | {'Name':<20} | {'Active Loans':<12} | {'Total Loans':<12}\n")
        f.write("-" * 60 + "\n")
        for c in clients:
            active_loans = db.query(Loan).filter(Loan.client_id == c.id, Loan.status == 'ACTIVE').count()
            total_loans = db.query(Loan).filter(Loan.client_id == c.id).count()
            f.write(f"{c.id:<5} | {c.full_name[:20]:<20} | {active_loans:<12} | {total_loans:<12}\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
    finally:
        db.close()
