#!/usr/bin/env python3
"""
Direct USDA ETL test - bypasses Prefect for local testing.

This runs the extract→transform→load pipeline without requiring Prefect server.
Use this for quick testing during development.

Usage:
    pixi run python test_usda_direct.py
"""

import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Setup Python path for namespace packages
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'pipeline'))
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'datamodels'))
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'webservice'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def print_banner(text):
    """Print a formatted banner"""
    width = 70
    print("\n" + "=" * width)
    print(text.center(width))
    print("=" * width + "\n")


def main():
    """Run the USDA ETL pipeline directly without Prefect"""
    print_banner("USDA ETL - Direct Test (No Prefect Server)")

    # Import the utility functions directly (bypass @task decorators)
    try:
        from ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df
        from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids
        print("[OK] All ETL utilities imported successfully\n")
    except Exception as e:
        print(f"[ERROR] Failed to import utilities: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 1: Extract
    print("=" * 70)
    print("STEP 1: EXTRACT - Fetching USDA data")
    print("=" * 70)
    try:
        # Get commodity IDs from database
        commodity_ids = get_mapped_commodity_ids()
        if not commodity_ids:
            print("[ERROR] No commodity mappings found in database")
            print("        Run: pixi run python src/ca_biositing/pipeline/ca_biositing/pipeline/utils/seed_usda_commodities.py")
            return False

        print(f"[OK] Found {len(commodity_ids)} mapped commodities: {commodity_ids}")

        # Extract USDA data
        api_key = os.getenv("USDA_NASS_API_KEY")
        raw_data = usda_nass_to_df(
            api_key=api_key,
            state="CA",
            year=None,
            commodity_ids=commodity_ids
        )

        if raw_data is None or raw_data.empty:
            print("[WARN] Extract returned no data")
            return False
        print(f"[OK] Extracted {len(raw_data)} records from USDA API")
        print(f"     Columns: {list(raw_data.columns)}")
        print(f"     Sample:\n{raw_data.head(2).to_string()}\n")
    except Exception as e:
        print(f"[ERROR] Extract failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Transform
    print("=" * 70)
    print("STEP 2: TRANSFORM - Cleaning and normalizing data")
    print("=" * 70)
    try:
        # Import transform logic
        import pandas as pd

        # Simple transform: validate and clean
        cleaned_data = raw_data.copy()
        cleaned_data.columns = [col.lower() for col in cleaned_data.columns]

        # Remove rows with null values
        cleaned_data = cleaned_data.dropna()

        if cleaned_data.empty:
            print("[WARN] Transform resulted in no data")
            return False
        print(f"[OK] Transformed {len(cleaned_data)} records")
        print(f"     Columns: {list(cleaned_data.columns)}")
        print(f"     Sample:\n{cleaned_data.head(2).to_string()}\n")
    except Exception as e:
        print(f"[ERROR] Transform failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Load
    print("=" * 70)
    print("STEP 3: LOAD - Inserting into database")
    print("=" * 70)
    try:
        from sqlalchemy import create_engine
        from sqlmodel import Session

        # Create database connection
        db_url = os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        # Insert records
        inserted_count = 0
        with Session(engine) as session:
            for _, row in cleaned_data.iterrows():
                try:
                    # Build insert statement
                    from sqlalchemy import text

                    # Note: This is a simplified load for testing
                    # The actual load task has more fields and validation
                    insert_sql = text("""
                        INSERT INTO usda_census_record (
                            geoid, commodity_code, year, value,
                            source_reference, notes, created_at, updated_at
                        ) VALUES (
                            :geoid, :commodity_code, :year, :value,
                            :source_reference, :notes, NOW(), NOW()
                        )
                    """)

                    session.execute(insert_sql, {
                        "geoid": row.get("geoid", ""),
                        "commodity_code": row.get("commodity_code", ""),
                        "year": row.get("year", 0),
                        "value": row.get("value", 0),
                        "source_reference": "USDA NASS QuickStats",
                        "notes": ""
                    })
                    inserted_count += 1
                except Exception as e:
                    print(f"  [WARN] Failed to insert row: {e}")
                    continue

            session.commit()

        print(f"[OK] Loaded {inserted_count} records into usda_census_record table\n")

    except Exception as e:
        print(f"[ERROR] Load failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print_banner("Pipeline Completed Successfully!")
    print(f"Summary:")
    print(f"  - Extracted: {len(raw_data)} records from USDA API")
    print(f"  - Transformed: {len(cleaned_data)} records (cleaned)")
    print(f"  - Loaded: Records inserted into database")
    print(f"\nYou can verify by querying:")
    print(f"  SELECT COUNT(*) FROM usda_census_record;")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
