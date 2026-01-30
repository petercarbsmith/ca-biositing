from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'observation'
        ORDER BY constraint_name
    """))
    print("=== OBSERVATION TABLE CONSTRAINTS ===\n")
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    # Get unique constraint details
    print("\n=== UNIQUE CONSTRAINT COLUMNS ===\n")
    result = conn.execute(text("""
        SELECT constraint_name, string_agg(column_name, ', ')
        FROM information_schema.key_column_usage
        WHERE table_name = 'observation' AND constraint_name LIKE 'uq_%'
        GROUP BY constraint_name
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]}")
