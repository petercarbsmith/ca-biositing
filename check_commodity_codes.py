#!/usr/bin/env python3
"""Check USDA commodity codes in database"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

print("Current USDA Commodities in Database:")
print("=" * 60)
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT id, name, usda_code FROM usda_commodity
        WHERE name IN ('CORN', 'ALMONDS', 'WHEAT', 'TOMATOES')
        ORDER BY id
    '''))
    for row in result:
        print(f"ID: {row[0]}, Name: {row[1]}, Code: {row[2]}")

print("\n" + "=" * 60)
print("Mapped commodities (usda_codes):")
print("=" * 60)
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT DISTINCT uc.usda_code, uc.name
        FROM resource_usda_commodity_map rcm
        JOIN usda_commodity uc ON rcm.usda_commodity_id = uc.id
        WHERE uc.usda_code IS NOT NULL
        ORDER BY uc.usda_code
    '''))
    for row in result:
        print(f"Code: {row[0]}, Name: {row[1]}")
