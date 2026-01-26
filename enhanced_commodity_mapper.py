#!/usr/bin/env python3
"""
Enhanced USDA Commodity Mapper - Interactive Fuzzy Matching

This script implements the workflow:
1. Import ALL USDA commodities for California from NASS API
2. Get your project's resources + primary_ag_products
3. Auto-match clear matches (high similarity)
4. Present 1-5 fuzzy match candidates for user to select
5. Leave USDA code empty if no good match

Usage:
    # Step 1: Fetch and cache all CA USDA commodities (run once)
    python enhanced_commodity_mapper.py --fetch-ca-commodities

    # Step 2: Auto-match clear matches (>90% similarity)
    python enhanced_commodity_mapper.py --auto-match

    # Step 3: Interactive review of fuzzy matches (60-90% similarity)
    python enhanced_commodity_mapper.py --review

    # Step 4: Save approved mappings to database
    python enhanced_commodity_mapper.py --save

    # Complete workflow (all steps)
    python enhanced_commodity_mapper.py --full-workflow

Reference:
    USDA Commodity Codes: https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/commcodes.php
"""

import sys
import os
import json
import requests
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Tuple, Dict, Optional
from datetime import datetime

# Setup Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'pipeline'))
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'datamodels'))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlmodel import Session

load_dotenv()

# Cache files
CACHE_DIR = Path(__file__).parent / '.cache'
CACHE_DIR.mkdir(exist_ok=True)
CA_COMMODITIES_CACHE = CACHE_DIR / 'ca_usda_commodities.json'
PENDING_MATCHES_FILE = CACHE_DIR / 'pending_matches.json'
APPROVED_MATCHES_FILE = CACHE_DIR / 'approved_matches.json'


# ============================================================================
# STEP 1: Fetch all CA commodities from NASS API
# ============================================================================

def fetch_ca_commodities() -> List[Dict]:
    """
    Fetch all unique USDA commodities available for California from NASS API.

    Returns:
        List of {code, name, description} dicts
    """
    print("\n" + "=" * 80)
    print("STEP 1: Fetching All California USDA Commodities")
    print("=" * 80)

    api_key = os.getenv('USDA_NASS_API_KEY')
    if not api_key:
        print("ERROR: USDA_NASS_API_KEY not found in .env file")
        return []

    print(f"Querying NASS API for California commodities...")

    url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        'key': api_key,
        'state_alpha': 'CA',
        'format': 'JSON',
        'year': 2022,  # Recent year with complete data
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and 'data' in data:
            records = data['data']
        else:
            records = data if isinstance(data, list) else []

        # Extract unique commodities
        commodities = {}
        for record in records:
            code = record.get('commodity_code')
            name = record.get('commodity_desc')
            desc = record.get('short_desc')

            if code and name:
                if code not in commodities:
                    commodities[code] = {
                        'code': code,
                        'name': name,
                        'description': desc or name,
                        'source': 'NASS'
                    }

        commodity_list = list(commodities.values())
        print(f"✓ Found {len(commodity_list)} unique commodities for California")

        # Save to cache
        with open(CA_COMMODITIES_CACHE, 'w') as f:
            json.dump(commodity_list, f, indent=2)
        print(f"✓ Cached to {CA_COMMODITIES_CACHE}")

        return commodity_list

    except Exception as e:
        print(f"ERROR fetching commodities: {e}")
        return []


def load_ca_commodities() -> List[Dict]:
    """Load CA commodities from cache or fetch if not cached"""
    if CA_COMMODITIES_CACHE.exists():
        with open(CA_COMMODITIES_CACHE) as f:
            commodities = json.load(f)
        print(f"Loaded {len(commodities)} commodities from cache")
        return commodities
    else:
        print("Cache not found. Fetching from NASS API...")
        return fetch_ca_commodities()


# ============================================================================
# STEP 2: Get project resources and primary_ag_products
# ============================================================================

def get_project_resources() -> List[Dict]:
    """
    Get all resources and primary_ag_products from your database.

    Returns:
        List of {id, name, type, table} dicts
    """
    print("\n" + "=" * 80)
    print("STEP 2: Loading Project Resources")
    print("=" * 80)

    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)

    resources = []

    with engine.connect() as conn:
        # Get primary_ag_products
        try:
            result = conn.execute(text(
                'SELECT id, name FROM primary_ag_product WHERE name IS NOT NULL ORDER BY name'
            ))
            for row in result:
                resources.append({
                    'id': row[0],
                    'name': row[1],
                    'type': 'primary_ag_product',
                    'table': 'primary_ag_product'
                })
        except Exception as e:
            print(f"Warning: Could not load primary_ag_products: {e}")

        # Get resources (if table exists)
        try:
            result = conn.execute(text(
                'SELECT id, name FROM resource WHERE name IS NOT NULL ORDER BY name LIMIT 200'
            ))
            for row in result:
                resources.append({
                    'id': row[0],
                    'name': row[1],
                    'type': 'resource',
                    'table': 'resource'
                })
        except Exception as e:
            print(f"Note: Resource table not queried: {e}")

    print(f"✓ Loaded {len(resources)} project resources/crops")
    return resources


# ============================================================================
# STEP 3: Fuzzy matching logic
# ============================================================================

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate normalized string similarity (0-1)"""
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()


def find_best_matches(resource_name: str, usda_commodities: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    Find top N best matching USDA commodities for a resource name.

    Returns:
        List of {code, name, description, score} sorted by score descending
    """
    matches = []

    for commodity in usda_commodities:
        # Calculate similarity against commodity name
        name_score = calculate_similarity(resource_name, commodity['name'])

        # Also check description if different
        desc_score = calculate_similarity(resource_name, commodity.get('description', ''))

        # Take best score
        score = max(name_score, desc_score)

        matches.append({
            'code': commodity['code'],
            'name': commodity['name'],
            'description': commodity.get('description', commodity['name']),
            'score': score,
            'source': commodity.get('source', 'NASS')
        })

    # Sort by score descending
    matches.sort(key=lambda x: x['score'], reverse=True)

    return matches[:top_n]


# ============================================================================
# STEP 4: Auto-match high-confidence matches
# ============================================================================

def auto_match_clear_matches(resources: List[Dict], usda_commodities: List[Dict], threshold: float = 0.90):
    """
    Automatically match resources with USDA commodities when similarity > threshold.
    """
    print("\n" + "=" * 80)
    print(f"STEP 3: Auto-Matching Clear Matches (>{threshold:.0%} similarity)")
    print("=" * 80)

    auto_matches = []
    pending_review = []

    for resource in resources:
        matches = find_best_matches(resource['name'], usda_commodities, top_n=5)

        if not matches:
            continue

        best_match = matches[0]

        if best_match['score'] >= threshold:
            # Clear match - auto-approve
            auto_matches.append({
                'resource': resource,
                'usda_commodity': best_match,
                'status': 'auto_matched',
                'matched_at': datetime.now().isoformat()
            })
            print(f"✓ AUTO: {resource['name']} → {best_match['name']} ({best_match['score']:.1%})")
        elif best_match['score'] >= 0.60:
            # Fuzzy match - needs review
            pending_review.append({
                'resource': resource,
                'candidates': matches[:5],  # Top 5 candidates
                'status': 'pending_review'
            })
            print(f"? REVIEW: {resource['name']} (best: {best_match['name']} @ {best_match['score']:.1%})")
        else:
            # No good match
            print(f"✗ NO MATCH: {resource['name']} (best: {best_match['score']:.1%})")

    print(f"\n✓ Auto-matched: {len(auto_matches)}")
    print(f"? Pending review: {len(pending_review)}")
    print(f"✗ No match: {len(resources) - len(auto_matches) - len(pending_review)}")

    # Save auto-matches to approved file
    save_approved_matches(auto_matches)

    # Save pending for interactive review
    save_pending_matches(pending_review)

    return auto_matches, pending_review


# ============================================================================
# STEP 5: Interactive review of fuzzy matches
# ============================================================================

def interactive_review():
    """
    Present fuzzy match candidates (1-5) for user to select best match.
    """
    print("\n" + "=" * 80)
    print("STEP 4: Interactive Review of Fuzzy Matches")
    print("=" * 80)

    pending = load_pending_matches()

    if not pending:
        print("No pending matches to review. Run --auto-match first.")
        return

    approved = load_approved_matches()

    print(f"\nYou have {len(pending)} resources with fuzzy matches to review.\n")
    print("For each resource, select the best USDA commodity match:")
    print("  - Enter 1-5 to select a candidate")
    print("  - Enter 'n' to skip (no good match)")
    print("  - Enter 'q' to quit and save progress\n")

    for i, item in enumerate(pending, 1):
        resource = item['resource']
        candidates = item['candidates']

        print(f"\n[{i}/{len(pending)}] Resource: '{resource['name']}' ({resource['type']})")
        print("-" * 80)

        for j, candidate in enumerate(candidates, 1):
            print(f"  [{j}] {candidate['name']} (code: {candidate['code']}) - {candidate['score']:.1%} match")
            if candidate['description'] != candidate['name']:
                print(f"      Description: {candidate['description']}")

        print("\n  [n] No good match - leave unmapped")

        while True:
            choice = input("\nYour selection (1-5, n, or q): ").strip().lower()

            if choice == 'q':
                print("\nSaving progress and exiting...")
                save_pending_matches(pending[i:])  # Save remaining items
                save_approved_matches(approved)
                return

            if choice == 'n':
                print(f"  → Skipping '{resource['name']}' (no match)")
                break

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    selected = candidates[idx]
                    approved.append({
                        'resource': resource,
                        'usda_commodity': selected,
                        'status': 'user_approved',
                        'matched_at': datetime.now().isoformat()
                    })
                    print(f"  ✓ Matched: {resource['name']} → {selected['name']}")
                    break
                else:
                    print("  Invalid choice. Try again.")
            except ValueError:
                print("  Invalid input. Enter a number (1-5), 'n', or 'q'.")

    print(f"\n✓ Review complete! {len(approved)} total matches approved.")

    # Clear pending (all reviewed)
    save_pending_matches([])
    save_approved_matches(approved)


# ============================================================================
# STEP 6: Save approved mappings to database
# ============================================================================

def save_mappings_to_database():
    """
    Insert approved mappings into resource_usda_commodity_map table.
    """
    print("\n" + "=" * 80)
    print("STEP 5: Saving Approved Mappings to Database")
    print("=" * 80)

    approved = load_approved_matches()

    if not approved:
        print("No approved matches to save. Run --review first.")
        return

    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)

    print(f"\nSaving {len(approved)} mappings to database...")

    saved_count = 0
    skipped_count = 0

    with engine.connect() as conn:
        for item in approved:
            resource = item['resource']
            commodity = item['usda_commodity']

            # First, ensure USDA commodity exists in usda_commodity table
            check_commodity = conn.execute(text(
                "SELECT id FROM usda_commodity WHERE usda_code = :code"
            ), {'code': commodity['code']})

            commodity_id = check_commodity.scalar()

            if not commodity_id:
                # Insert USDA commodity
                result = conn.execute(text(
                    """
                    INSERT INTO usda_commodity (name, usda_code, usda_source, created_at, updated_at)
                    VALUES (:name, :code, :source, NOW(), NOW())
                    RETURNING id
                    """
                ), {
                    'name': commodity['name'],
                    'code': commodity['code'],
                    'source': commodity.get('source', 'NASS')
                })
                commodity_id = result.scalar()
                print(f"  + Created USDA commodity: {commodity['name']} (code: {commodity['code']})")

            # Check if mapping already exists
            check_mapping = conn.execute(text(
                """
                SELECT id FROM resource_usda_commodity_map
                WHERE usda_commodity_id = :commodity_id
                AND (primary_ag_product_id = :resource_id OR resource_id = :resource_id)
                """
            ), {
                'commodity_id': commodity_id,
                'resource_id': resource['id']
            })

            if check_mapping.scalar():
                print(f"  ⚠ Mapping already exists: {resource['name']} → {commodity['name']}")
                skipped_count += 1
                continue

            # Determine which column to use (primary_ag_product_id or resource_id)
            if resource['type'] == 'primary_ag_product':
                field_name = 'primary_ag_product_id'
            else:
                field_name = 'resource_id'

            # Insert mapping
            match_tier = 'AUTO_MATCH' if item['status'] == 'auto_matched' else 'USER_APPROVED'

            conn.execute(text(f"""
                INSERT INTO resource_usda_commodity_map
                ({field_name}, usda_commodity_id, match_tier, note, created_at, updated_at)
                VALUES (:resource_id, :commodity_id, :match_tier, :note, NOW(), NOW())
                """), {
                'resource_id': resource['id'],
                'commodity_id': commodity_id,
                'match_tier': match_tier,
                'note': f"Matched by enhanced_commodity_mapper.py - {item['status']} - similarity: {commodity['score']:.2%}"
            })

            conn.commit()
            saved_count += 1
            print(f"  ✓ Saved: {resource['name']} → {commodity['name']} ({match_tier})")

    print(f"\n✓ Saved {saved_count} new mappings")
    print(f"⚠ Skipped {skipped_count} existing mappings")


# ============================================================================
# File I/O helpers
# ============================================================================

def load_pending_matches() -> List[Dict]:
    """Load pending matches from file"""
    if PENDING_MATCHES_FILE.exists():
        with open(PENDING_MATCHES_FILE) as f:
            return json.load(f)
    return []


def save_pending_matches(pending: List[Dict]):
    """Save pending matches to file"""
    with open(PENDING_MATCHES_FILE, 'w') as f:
        json.dump(pending, f, indent=2)


def load_approved_matches() -> List[Dict]:
    """Load approved matches from file"""
    if APPROVED_MATCHES_FILE.exists():
        with open(APPROVED_MATCHES_FILE) as f:
            return json.load(f)
    return []


def save_approved_matches(approved: List[Dict]):
    """Save approved matches to file"""
    with open(APPROVED_MATCHES_FILE, 'w') as f:
        json.dump(approved, f, indent=2)


# ============================================================================
# Main CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced USDA Commodity Mapper with Interactive Fuzzy Matching"
    )
    parser.add_argument('--fetch-ca-commodities', action='store_true',
                       help='Fetch all CA USDA commodities from NASS API')
    parser.add_argument('--auto-match', action='store_true',
                       help='Auto-match clear matches (>90%% similarity)')
    parser.add_argument('--review', action='store_true',
                       help='Interactively review fuzzy matches')
    parser.add_argument('--save', action='store_true',
                       help='Save approved mappings to database')
    parser.add_argument('--full-workflow', action='store_true',
                       help='Run complete workflow (fetch → auto-match → review → save)')

    args = parser.parse_args()

    if args.fetch_ca_commodities or args.full_workflow:
        fetch_ca_commodities()

    if args.auto_match or args.full_workflow:
        commodities = load_ca_commodities()
        resources = get_project_resources()
        auto_match_clear_matches(resources, commodities)

    if args.review or args.full_workflow:
        interactive_review()

    if args.save or args.full_workflow:
        save_mappings_to_database()

    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
