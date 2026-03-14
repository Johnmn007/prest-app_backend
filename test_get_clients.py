
from app.database.connection import SessionLocal
from app.services import client_service
import traceback

db = SessionLocal()
try:
    clients = client_service.get_clients(db)
    print(f"Success! Found {len(clients)} clients.")
    for c in clients:
        print(f"Client: {c.full_name}, Active: {c.active}")
except Exception as e:
    print("Error calling get_clients:")
    traceback.print_exc()
finally:
    db.close()
