#!/usr/bin/env python3
"""
Quick Start: USDA Data Import Pipeline

This script demonstrates how to run the complete USDA ETL pipeline.
It handles all setup and can be run anytime after database seeding.

Usage:
    pixi run python run_usda_import.py
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


def check_prerequisites():
    """Verify all prerequisites are met"""
    print("Checking prerequisites...")

    # Check USDA API key
    api_key = os.getenv('USDA_NASS_API_KEY')
    if not api_key:
        print("✗ USDA_NASS_API_KEY not found in environment")
        print("  Add it to your .env file or set it as environment variable")
        return False
    print(f"✓ USDA API key found: {api_key[:10]}...")

    # Check database
    try:
        from sqlalchemy import create_engine, text
        # Load from .env (now has correct localhost credentials)
        db_url = os.getenv(
            'DATABASE_URL',
            'postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db'
        )
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[OK] Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("  Ensure services are running: pixi run start-services")
        return False

    # Check commodity mappings
    try:
        from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids
        ids = get_mapped_commodity_ids()
        if ids:
            print(f"✓ Found {len(ids)} mapped commodities: {ids}")
        else:
            print("✗ No mapped commodities found")
            print("  Run: pixi run python src/ca_biositing/pipeline/ca_biositing/pipeline/utils/seed_usda_commodities.py")
            return False
    except Exception as e:
        print(f"✗ Failed to check mappings: {e}")
        return False

    return True


def run_pipeline():
    """Run the USDA ETL pipeline (direct, no Prefect server required)"""
    try:
        print_banner("USDA ETL Pipeline Execution")

        # Import pipeline components directly (no Prefect decorator execution)
        from ca_biositing.pipeline.etl.extract.usda_census_survey import extract
        from ca_biositing.pipeline.etl.transform.usda.usda_census_survey import transform
        from ca_biositing.pipeline.etl.load.usda.usda_census_survey import load

        print("[1/3] Extracting USDA data...\n")
        raw_data = extract()
        if raw_data is None or len(raw_data) == 0:
            print("✗ Extract returned no data\n")
            return False
        print(f"✓ Extracted {len(raw_data)} records\n")

        print("[2/3] Transforming data...\n")
        transformed_data = transform({"usda_census_survey": raw_data})
        if transformed_data is None or len(transformed_data) == 0:
            print("✗ Transform returned no data\n")
            return False
        print(f"✓ Transformed {len(transformed_data)} records\n")

        print("[3/3] Loading data...\n")
        success = load(transformed_data)
        if success:
            print_banner("✓ Pipeline Completed Successfully!")
            print("Data has been loaded into the usda_census_record table.")
            print("\nNext steps:")
            print("  - Query results: SELECT * FROM usda_census_record LIMIT 10;")
            print("  - View mappings: SELECT * FROM resource_usda_commodity_map;")
            return True
        else:
            print_banner("✗ Pipeline Failed")
            print("Check logs above for details")
            return False

    except Exception as e:
        print_banner("✗ Pipeline Error")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    print_banner("USDA Data Import - Quick Start")

    # Check prerequisites
    if not check_prerequisites():
        print("\n✗ Prerequisites not met. Aborting.")
        return 1

    # Run pipeline
    if not run_pipeline():
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
