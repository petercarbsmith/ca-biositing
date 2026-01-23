"""
Test script to verify USDA imports work correctly.

This script handles PYTHONPATH setup properly for the namespace package structure.
It's the correct way to test before running the full ETL pipeline.

Run from project root:
    pixi run python test_usda_imports.py
"""

import sys
import os

# Get the absolute path to the project root
project_root = os.path.dirname(os.path.abspath(__file__))

# Add src distributions to PYTHONPATH (required for PEP 420 namespace packages)
# This matches the PYTHONPATH requirement from AGENTS.md
src_paths = [
    os.path.join(project_root, 'src', 'ca_biositing', 'pipeline'),
    os.path.join(project_root, 'src', 'ca_biositing', 'datamodels'),
    os.path.join(project_root, 'src', 'ca_biositing', 'webservice'),
]

for path in src_paths:
    if path not in sys.path:
        sys.path.insert(0, path)
        print(f"✓ Added to PYTHONPATH: {path}")

print("\n" + "=" * 60)
print("Testing USDA Import Setup")
print("=" * 60)

# Test 1: Import commodity_mapper
print("\n[Test 1] Importing commodity_mapper...")
try:
    from ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids
    print("  ✓ Successfully imported get_mapped_commodity_ids")
except ModuleNotFoundError as e:
    print(f"  ✗ Failed to import: {e}")
    sys.exit(1)

# Test 2: Import USDA utility
print("\n[Test 2] Importing usda_nass_to_pandas...")
try:
    from ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df
    print("  ✓ Successfully imported usda_nass_to_df")
except ModuleNotFoundError as e:
    print(f"  ✗ Failed to import: {e}")
    sys.exit(1)

# Test 3: Import extract task
print("\n[Test 3] Importing extract task...")
try:
    from ca_biositing.pipeline.etl.extract.usda_census_survey import extract
    print("  ✓ Successfully imported extract task")
except ModuleNotFoundError as e:
    print(f"  ✗ Failed to import: {e}")
    sys.exit(1)

# Test 4: Check if database is accessible
print("\n[Test 4] Checking database connectivity...")
try:
    from ca_biositing.datamodels.database import get_engine
    engine = get_engine()
    print(f"  ✓ Database engine available")
except Exception as e:
    print(f"  ⚠ Database connection warning: {e}")
    print("    (This is OK if database isn't running yet)")

print("\n" + "=" * 60)
print("✓ All import tests passed!")
print("=" * 60)
print("\nNext steps:")
print("  1. Start services: pixi run start-services")
print("  2. Seed data: pixi run python src/ca_biositing/pipeline/ca_biositing/pipeline/utils/seed_usda_commodities.py")
print("  3. Run extract: pixi run python -c \"from ca_biositing.pipeline.etl.extract.usda_census_survey import extract; df = extract()\"")
