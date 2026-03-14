from sqlalchemy import text
from app.database.connection import SessionLocal, engine
from app.models.user import User
from app.models.client import Client
from app.models.loan import Loan, Installment
from app.models.payment import Payment
from app.models.refinancing import Refinancing
from app.models.route import Route
from app.models.route_client import RouteClient
from app.models.expense import Expense
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash

def vaciar_y_resetear_bd():
    db = SessionLocal()
    print("--- Iniciando limpieza total de la base de datos ---")
    
    try:
        # 1. Borramos en orden para respetar las FK (o usamos TRUNCATE CASCADE)
        # El orden es: Tablas dependientes primero, tablas maestras al final.
        db.query(Payment).delete()
        db.query(Installment).delete()
        db.query(Refinancing).delete()
        db.query(Loan).delete()
        db.query(RouteClient).delete()
        db.query(Route).delete()
        db.query(Client).delete()
        db.query(AuditLog).delete()
        db.query(Expense).delete()
        db.query(User).delete()
        
        # 2. Reiniciamos los contadores de ID (Secuencias) para que todo empiece en 1
        tablas = [
            "payments", "installments", "refinancings", "loans", 
            "route_clients", "routes", "clients", "audit_logs", 
            "expenses", "users"
        ]
        for tabla in tablas:
            db.execute(text(f"ALTER SEQUENCE {tabla}_id_seq RESTART WITH 1"))
        
        db.commit()
        print("[OK] Base de datos vaciada y contadores reiniciados.")
        
        # 3. Crear el usuario Administrador por defecto
        admin_email = "admin@gota.com"
        admin_pass = "admin123"
        
        admin = User(
            name="Admin Dilver",
            email=admin_email,
            password_hash=get_password_hash(admin_pass),
            role="admin",
            active=True
        )
        db.add(admin)
        db.commit()
        print(f"[OK] Usuario administrador creado: {admin_email} / {admin_pass}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] No se pudo resetear la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    confirmacion = input("¿ESTÁS SEGURO? Esto borrará todos los préstamos y clientes. (s/n): ")
    if confirmacion.lower() == 's':
        vaciar_y_resetear_bd()
    else:
        print("Operación cancelada.")