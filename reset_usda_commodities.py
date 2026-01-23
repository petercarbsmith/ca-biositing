#!/usr/bin/env python3
"""Reset USDA commodities and reseed with correct USDA codes"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

print("Resetting USDA commodity data...")
print("=" * 60)

with engine.begin() as conn:
    # Delete mappings first (foreign key constraint)
    print("Deleting old mappings...")
    conn.execute(text('DELETE FROM resource_usda_commodity_map WHERE usda_commodity_id IN (1,2,3,4)'))

    # Delete old commodities
    print("Deleting old commodities...")
    conn.execute(text("DELETE FROM usda_commodity WHERE name IN ('CORN', 'ALMONDS', 'WHEAT', 'TOMATOES')"))

    print("✓ Old data deleted")

print("\nNow reseeding with correct USDA codes...")
print("=" * 60)

# Run the seed script
import subprocess
result = subprocess.run(
    ["pixi", "run", "python", "src/ca_biositing/pipeline/ca_biositing/pipeline/utils/seed_usda_commodities.py"],
    cwd=os.getcwd(),
    capture_output=True,
    text=True
)

print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr)
    print(f"Exit code: {result.returncode}")
else:
    print("\n✓ Reset and reseed complete!")

    # Verify
    print("\nVerifying new data:")
    print("=" * 60)
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT id, name, usda_code FROM usda_commodity
            WHERE name IN ('CORN', 'ALMONDS', 'WHEAT', 'TOMATOES')
            ORDER BY id
        '''))
        for row in result:
            print(f"ID: {row[0]}, Name: {row[1]}, Code: {row[2]}")
