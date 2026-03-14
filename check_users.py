
from app.database.connection import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"User: {user.email}, Role: {user.role}, Active: {user.active}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
