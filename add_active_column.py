
from sqlalchemy import text
from app.database.connection import engine

def add_active_to_clients():
    try:
        with engine.connect() as conn:
            # PostgreSQL command to add column if not exists
            conn.execute(text("ALTER TABLE clients ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("Successfully checked/added 'active' column to 'clients' table.")
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_active_to_clients()
