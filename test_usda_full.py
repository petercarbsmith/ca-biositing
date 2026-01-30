#!/usr/bin/env python
"""Test script to verify the full USDA ETL pipeline works with fixed commodity_mapper"""
import os
import sys

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db'
# Load USDA API key from the correct .env file
os.environ['USDA_NASS_API_KEY'] = 'A95E83AA-D37A-37D7-8365-3C77DD57CE34'

# Add paths for imports
sys.path.insert(0, 'c:\\Users\\meili\\forked\\ca-biositing\\src\\ca_biositing\\pipeline')

try:
    from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids
    from ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df

    print("[OK] Imports successful")

    # Test 1: Get commodity IDs
    print("\n--- Test 1: Get Commodity Names ---")
    commodity_names = get_mapped_commodity_ids()
    print(f"[OK] Got {len(commodity_names)} commodities: {commodity_names}")

    # Test 2: Test API call with one commodity
    print("\n--- Test 2: Test USDA API Call ---")
    print(f"API Key loaded: {bool(os.getenv('USDA_NASS_API_KEY'))}")

    if commodity_names:
        test_commodity = commodity_names[0]
        print(f"Testing API with commodity name: {test_commodity}")

        df = usda_nass_to_df(
            api_key=os.getenv('USDA_NASS_API_KEY'),
            state="CA",
            commodity_ids=[test_commodity],  # Test with just one
            agg_level_desc="COUNTY"
        )

        if df is not None:
            print(f"[OK] SUCCESS: Got {len(df)} records from USDA API")
            print(f"   Columns: {list(df.columns[:5])}...")
            print(f"   Sample record:")
            print(df.iloc[0] if len(df) > 0 else "No records")
        else:
            print("[ERROR] usda_nass_to_df returned None")
    else:
        print("[ERROR] No commodities found")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
