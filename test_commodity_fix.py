#!/usr/bin/env python
"""Test script to verify commodity_mapper returns USDA codes not IDs"""
import os
import sys

# Set environment variable for database connection
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db'

# Add paths for imports
sys.path.insert(0, 'c:\\Users\\meili\\forked\\ca-biositing\\src\\ca_biositing\\pipeline')

from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids

try:
    commodity_ids = get_mapped_commodity_ids()
    print(f"✅ SUCCESS: Got commodity IDs from database")
    print(f"   Commodity IDs: {commodity_ids}")
    print(f"   Type of first element: {type(commodity_ids[0]) if commodity_ids else 'N/A'}")

    # Verify they're strings (USDA codes) not integers (database IDs)
    if commodity_ids:
        first = commodity_ids[0]
        if isinstance(first, str) and len(first) >= 6:
            print(f"   ✅ Confirmed: First code '{first}' is a USDA code (string, length {len(first)})")
        elif isinstance(first, int):
            print(f"   ❌ ERROR: First code {first} is a database ID (int), not a USDA code!")
        else:
            print(f"   ❓ Unexpected: First code {first} is type {type(first)}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
