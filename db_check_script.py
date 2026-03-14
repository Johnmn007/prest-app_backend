
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

with open("db_check.txt", "w") as f:
    try:
        with engine.connect() as conn:
            # Check column
            res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'clients' AND column_name = 'active'"))
            row = res.fetchone()
            f.write(f"Column active check: {row}\n")
            
            # Count nulls
            res = conn.execute(text("SELECT count(*) FROM clients WHERE active IS NULL"))
            count = res.scalar()
            f.write(f"Null active count: {count}\n")
            
            # Update if needed
            if count > 0:
                conn.execute(text("UPDATE clients SET active = TRUE WHERE active IS NULL"))
                conn.commit()
                f.write("Updated NULL values to TRUE\n")
            
            # Check all values
            res = conn.execute(text("SELECT id, full_name, active FROM clients"))
            f.write("All clients:\n")
            for r in res:
                f.write(f"{r}\n")
                
    except Exception as e:
        f.write(f"Error: {e}\n")
