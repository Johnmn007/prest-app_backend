"""
Script para crear el usuario administrador inicial.
Solo crea el admin si no existe — NO borra datos.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def crear_admin(email: str, password: str, name: str = "Admin"):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"[INFO] El usuario '{email}' ya existe. No se realizaron cambios.")
            return

        admin = User(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            active=True,
        )
        db.add(admin)
        db.commit()
        print(f"[OK] Admin creado: {email}")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    email = input("Email del admin: ").strip()
    password = input("Contraseña (mín. 8 caracteres): ").strip()
    name = input("Nombre completo: ").strip() or "Admin"

    if len(password) < 8:
        print("[ERROR] La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    crear_admin(email, password, name)
