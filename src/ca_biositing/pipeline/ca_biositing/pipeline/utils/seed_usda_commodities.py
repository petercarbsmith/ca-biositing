"""
Quick seed script to populate USDA commodities and mappings for testing.

Run this ONCE before testing the USDA import.
It populates resource_usda_commodity_map with test data so the extract can find commodities to query.

Usage:
    From project root or anywhere with pixi:
    pixi run python src/ca_biositing/pipeline/ca_biositing/pipeline/utils/seed_usda_commodities.py
"""

import sys
import os

# Ensure we can import ca_biositing modules
# Add the src directory structure to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from sqlmodel import Session, select
from sqlalchemy import create_engine
from ca_biositing.datamodels.schemas.generated.ca_biositing import (
    UsdaCommodity,
    ResourceUsdaCommodityMap,
)


def seed_usda_test_data():
    """Seed test USDA commodities and mappings."""

    # Load from .env (now has correct localhost credentials for local development)
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://biocirv_user:biocirv_dev_password@localhost:5432/biocirv_db"
    )
    print(f"Connecting to database: {db_url}")

    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        print("=" * 60)
        print("Seeding USDA test data...")
        print("=" * 60)

        # 1. Create sample USDA commodities
        # These are real USDA commodity codes from:
        # https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/commcodes.php

        commodities_to_add = [
            {"name": "CORN", "usda_source": "NASS", "usda_code": "11199199"},  # Corn For Grain
            {"name": "ALMONDS", "usda_source": "NASS", "usda_code": "26199999"},  # Almonds
            {"name": "WHEAT", "usda_source": "NASS", "usda_code": "10199999"},  # Wheat All
            {"name": "TOMATOES", "usda_source": "NASS", "usda_code": "37899999"},  # Tomatoes
        ]

        created_commodities = []
        print("\n1. Creating USDA commodities...")
        for commodity_data in commodities_to_add:
            # Check if already exists
            existing = session.exec(
                select(UsdaCommodity).where(
                    UsdaCommodity.name == commodity_data["name"]
                )
            ).first()

            if not existing:
                commodity = UsdaCommodity(**commodity_data)
                session.add(commodity)
                print(f"  [+] Created commodity: {commodity_data['name']} (code: {commodity_data['usda_code']})")
            else:
                print(f"  [*] Commodity already exists: {commodity_data['name']}")
                commodity = existing

            created_commodities.append(commodity)

        session.commit()
        print(f"\n[OK] Created/verified {len(created_commodities)} commodities")

        # 2. Get or create a primary_crop for testing
        # Note: The schema uses 'primary_crop' not 'primary_ag_product'
        print("\n2. Creating test primary_crop for mapping...")

        # Create a test primary_crop directly via SQL
        try:
            from sqlalchemy import text
            session.execute(
                text("INSERT INTO primary_crop (name) VALUES ('Test Crop') ON CONFLICT DO NOTHING")
            )
            session.commit()
            print(f"  [OK] Created/verified test primary_crop")

            # Now get it back to use in mapping
            primary_crop_id = session.execute(
                text("SELECT id FROM primary_crop WHERE name = 'Test Crop' LIMIT 1")
            ).scalar()

            if not primary_crop_id:
                print("  [FAIL] Failed to create primary_crop")
                return False

            print(f"  [OK] primary_crop ID: {primary_crop_id}")
        except Exception as e:
            print(f"  ✗ Error creating primary_crop: {e}")
            return False

        # 3. Create mappings between primary_crop and USDA commodities
        print(f"\n3. Creating mappings...")
        print(f"   Linking {len(created_commodities)} commodities to primary_crop (ID={primary_crop_id})...")

        mappings_created = 0
        for commodity in created_commodities:
            try:
                from sqlalchemy import text
                # Check if mapping already exists
                existing = session.execute(
                    text(f"SELECT id FROM resource_usda_commodity_map WHERE primary_crop_id = {primary_crop_id} AND usda_commodity_id = {commodity.id}")
                ).scalar()

                if not existing:
                    session.execute(
                        text(f"INSERT INTO resource_usda_commodity_map (primary_crop_id, usda_commodity_id, match_tier, note, created_at, updated_at) VALUES ({primary_crop_id}, {commodity.id}, 'DIRECT_MATCH', 'Test mapping for USDA import', NOW(), NOW())")
                    )
                    session.commit()
                    print(f"  [+] Created mapping: Test Crop -> {commodity.name}")
                    mappings_created += 1
                else:
                    print(f"  [*] Mapping already exists: Test Crop -> {commodity.name}")
            except Exception as e:
                print(f"  [FAIL] Error creating mapping for {commodity.name}: {e}")
                continue

        print(f"\n[OK] Created {mappings_created} new mappings")

        # 4. Verify the mappings
        print("\n4. Verifying mappings...")
        from sqlalchemy import text
        mapped_ids = session.execute(
            text("SELECT DISTINCT usda_commodity_id FROM resource_usda_commodity_map")
        ).scalars().all()
        print(f"  [OK] Found {len(mapped_ids)} mapped commodity IDs: {list(mapped_ids)}")

        print("\n" + "=" * 60)
        print("[OK] Seeding complete! You can now test the USDA import.")
        print("=" * 60)

        return True


if __name__ == "__main__":
    try:
        success = seed_usda_test_data()
        if success:
            print("\n[OK] Ready to test! Run:")
            print("   pixi run python test_usda_direct.py")
            sys.exit(0)
        else:
            print("\n[FAIL] Seeding failed. See messages above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
