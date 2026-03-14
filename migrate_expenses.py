"""
MIGRACION SEGURA -- Tabla 'expenses' (sin perdida de datos)

Este script lee la DATABASE_URL desde el .env del proyecto y aplica
SOLO los cambios que faltan usando ALTER TABLE con IF NOT EXISTS.

SEGURO: No toca ninguna tabla existente (clients, loans, payments, etc.)
IDEMPOTENTE: Puede correrse varias veces sin romper nada
SIN DROP: No elimina columnas, solo agrega las que faltan

COMO USAR:
  1. Abri una terminal en la carpeta dilver_backend/
  2. Activa el venv:   venv\Scripts\activate
  3. Ejecuta:          python migrate_expenses.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from sqlalchemy import create_engine, text, inspect

print("")
print("=" * 60)
print("  MIGRACION DE BASE DE DATOS - Sistema Gota a Gota")
print("=" * 60)

engine = create_engine(settings.DATABASE_URL)

db_url = settings.DATABASE_URL.lower()
is_postgres = "postgresql" in db_url or "postgres" in db_url
is_sqlite   = "sqlite" in db_url
is_mysql    = "mysql" in db_url

motor = "PostgreSQL" if is_postgres else ("SQLite" if is_sqlite else "MySQL/MariaDB")
print(f"\n  Motor detectado: {motor}")
print(f"  URL: {settings.DATABASE_URL[:45]}...\n")

inspector = inspect(engine)
tables = inspector.get_table_names()

if "expenses" not in tables:
    print("  [INFO] La tabla 'expenses' NO existe. Creandola desde cero...")
    with engine.connect() as conn:
        if is_postgres:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id              SERIAL PRIMARY KEY,
                    description     VARCHAR(255) NOT NULL,
                    amount          FLOAT NOT NULL,
                    category        VARCHAR(50) NOT NULL DEFAULT 'VARIOS',
                    notes           VARCHAR(500),
                    date            DATE NOT NULL DEFAULT CURRENT_DATE,
                    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    registered_by   INTEGER REFERENCES users(id) ON DELETE SET NULL
                );
            """))
        elif is_sqlite:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    description     TEXT NOT NULL,
                    amount          REAL NOT NULL,
                    category        TEXT NOT NULL DEFAULT 'VARIOS',
                    notes           TEXT,
                    date            TEXT NOT NULL DEFAULT (date('now')),
                    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                    registered_by   INTEGER REFERENCES users(id)
                );
            """))
        else:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id              INT AUTO_INCREMENT PRIMARY KEY,
                    description     VARCHAR(255) NOT NULL,
                    amount          FLOAT NOT NULL,
                    category        VARCHAR(50) NOT NULL DEFAULT 'VARIOS',
                    notes           VARCHAR(500),
                    date            DATE NOT NULL DEFAULT (CURRENT_DATE),
                    created_at      DATETIME NOT NULL DEFAULT NOW(),
                    registered_by   INT,
                    FOREIGN KEY (registered_by) REFERENCES users(id) ON DELETE SET NULL
                );
            """))
        conn.commit()
    print("  [OK] Tabla 'expenses' creada exitosamente.\n")

else:
    print("  [OK] La tabla 'expenses' ya existe. Verificando columnas faltantes...")
    existing_cols = {col["name"] for col in inspector.get_columns("expenses")}
    print(f"       Columnas actuales: {sorted(existing_cols)}\n")

    new_columns = {
        "category": {
            "postgres": "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS category VARCHAR(50) NOT NULL DEFAULT 'VARIOS';",
            "sqlite":   "ALTER TABLE expenses ADD COLUMN category TEXT;",
            "mysql":    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS category VARCHAR(50) NOT NULL DEFAULT 'VARIOS';",
        },
        "notes": {
            "postgres": "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS notes VARCHAR(500);",
            "sqlite":   "ALTER TABLE expenses ADD COLUMN notes TEXT;",
            "mysql":    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS notes VARCHAR(500);",
        },
        "created_at": {
            "postgres": "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();",
            "sqlite":   "ALTER TABLE expenses ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'));",
            "mysql":    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS created_at DATETIME NOT NULL DEFAULT NOW();",
        },
        "registered_by": {
            "postgres": "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS registered_by INTEGER REFERENCES users(id) ON DELETE SET NULL;",
            "sqlite":   "ALTER TABLE expenses ADD COLUMN registered_by INTEGER;",
            "mysql":    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS registered_by INT;",
        },
    }

    applied = []
    skipped = []

    with engine.connect() as conn:
        for col_name, sqls in new_columns.items():
            if col_name in existing_cols:
                skipped.append(col_name)
                print(f"  [SKIP] '{col_name}' ya existe, omitida.")
                continue

            print(f"  [ADD]  Agregando columna '{col_name}'...")

            if is_postgres:
                sql = sqls["postgres"]
            elif is_sqlite:
                sql = sqls["sqlite"]
            else:
                sql = sqls["mysql"]

            try:
                conn.execute(text(sql))
                conn.commit()
                applied.append(col_name)
                print(f"         '{col_name}' agregada correctamente.")
            except Exception as e:
                print(f"  [ERROR] Fallo en '{col_name}': {e}")

        # Rellenar 'category' en registros existentes que queden NULL
        if "category" in applied and (is_sqlite or is_mysql):
            print("\n  [INFO] Rellenando columna 'category' con valor por defecto en registros existentes...")
            conn.execute(text("UPDATE expenses SET category = 'VARIOS' WHERE category IS NULL;"))
            conn.commit()
            print("         Registros actualizados correctamente.")

    print(f"\n  Columnas omitidas (ya existian): {skipped if skipped else 'ninguna'}")
    print(f"  Columnas nuevas aplicadas:       {applied if applied else 'ninguna'}")

# Verificacion final
print("\n  Verificando estado final de la tabla 'expenses'...")
inspector2 = inspect(engine)
final_cols  = [col["name"] for col in inspector2.get_columns("expenses")]
print(f"  Columnas finales: {final_cols}")

required = {"id", "description", "amount", "category", "notes", "date", "created_at", "registered_by"}
missing  = required - set(final_cols)

print("")
print("=" * 60)
if missing:
    print(f"  [ADVERTENCIA] Columnas aun faltantes: {missing}")
    print("  Revisa los errores anteriores.")
else:
    print("  MIGRACION COMPLETADA EXITOSAMENTE")
    print("  Todos tus datos anteriores estan intactos.")
    print("  Puedes reiniciar el backend normalmente.")
print("=" * 60)
print("")
