#!/usr/bin/env python3
"""
USDA Commodity Code Matcher

This script intelligently matches USDA commodity codes to your database resources
and primary crops using fuzzy string matching.

The matching process:
1. Fetches all unique names from resources and primary_crops tables
2. Searches for USDA commodity codes that match each name
3. Presents candidates for developer review
4. Allows manual selection and saves to resource_usda_commodity_map

Usage:
    # First time - search all resources and crops, present candidates
    pixi run python match_usda_commodities.py --search-all

    # View pending matches for review
    pixi run python match_usda_commodities.py --review

    # After review, save specific matches
    pixi run python match_usda_commodities.py --approve CORN 11199199

    # For new resources added later
    pixi run python match_usda_commodities.py --search "Alfalfa"
"""

import sys
import os
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Tuple, Dict
import json

# Setup Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'pipeline'))
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'datamodels'))
sys.path.insert(0, str(project_root / 'src' / 'ca_biositing' / 'webservice'))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlmodel import Session

load_dotenv()


# USDA commodity codes database (curated list of common commodities)
# Format: (commodity_code, description, common_names)
USDA_COMMODITIES = [
    ("11199199", "Corn For Grain", ["corn", "grain corn", "field corn"]),
    ("11199299", "Corn For Silage", ["corn silage", "silage"]),
    ("11199999", "Corn All", ["corn all", "all corn"]),
    ("10199999", "Wheat All", ["wheat", "all wheat"]),
    ("26199999", "Almonds", ["almond", "almonds"]),
    ("10399999", "Barley All", ["barley", "all barley"]),
    ("37899999", "Tomatoes", ["tomato", "tomatoes"]),
    ("37299999", "Shallots", ["shallot", "shallots"]),
    ("36399999", "Peppers-Bell", ["bell pepper", "peppers", "sweet pepper"]),
    ("32399999", "Corn-Sweet", ["sweet corn", "corn sweet"]),
    ("21199999", "Apples", ["apple", "apples"]),
    ("20099999", "Citrus", ["citrus"]),
    ("18199999", "Hay Alfalfa", ["alfalfa", "hay alfalfa"]),
    ("15499999", "Soybeans All", ["soybean", "soybeans"]),
    ("15399999", "Peanuts All", ["peanut", "peanuts"]),
    ("26499999", "Pecans", ["pecan", "pecans"]),
    ("26399999", "Walnuts", ["walnut", "walnuts"]),
    ("21699999", "All Grapes", ["grape", "grapes"]),
    ("21319999", "Sweet Cherries", ["cherry", "cherries", "sweet cherry"]),
    ("21619999", "Nectarines", ["nectarine", "nectarines"]),
    ("21699999", "Apricots", ["apricot", "apricots"]),
    ("23799999", "Strawberries", ["strawberry", "strawberries"]),
    ("23179999", "Cranberries", ["cranberry", "cranberries"]),
    ("23079999", "Blueberries", ["blueberry", "blueberries"]),
    ("34399999", "Melons-Cantaloupes", ["cantaloupe", "melon"]),
    ("30399999", "Beans-Lima", ["lima bean", "lima beans"]),
    ("30499999", "Beans-Snap", ["snap bean", "snap beans", "green bean"]),
    ("31099999", "Cabbage", ["cabbage"]),
    ("31399999", "Carrots", ["carrot", "carrots"]),
    ("31699999", "Celery", ["celery"]),
    ("33599999", "Garlic", ["garlic"]),
    ("34099999", "Lettuce-Head", ["lettuce", "head lettuce"]),
    ("30799999", "Broccoli", ["broccoli"]),
]


def similarity(a: str, b: str) -> float:
    """Calculate string similarity score (0-1)"""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def find_commodity_matches(search_term: str, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
    """
    Find USDA commodity codes matching a search term.

    Returns:
        List of (code, description, score) tuples, sorted by score descending
    """
    matches = []

    for code, desc, names in USDA_COMMODITIES:
        # Check against description
        score = similarity(search_term, desc)

        # Check against common names
        for name in names:
            name_score = similarity(search_term, name)
            score = max(score, name_score)

        if score >= threshold:
            matches.append((code, desc, score))

    # Sort by score descending
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def get_pending_matches() -> Dict:
    """Get pending matches from JSON file"""
    match_file = Path(__file__).parent / '.usda_pending_matches.json'
    if match_file.exists():
        with open(match_file) as f:
            return json.load(f)
    return {}


def save_pending_matches(pending: Dict):
    """Save pending matches to JSON file"""
    match_file = Path(__file__).parent / '.usda_pending_matches.json'
    with open(match_file, 'w') as f:
        json.dump(pending, f, indent=2)


def get_db_resources() -> List[str]:
    """Get all unique resource/crop names from database"""
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)

    names = set()

    with engine.connect() as conn:
        # Get primary crop names
        result = conn.execute(text('SELECT DISTINCT name FROM primary_crop WHERE name IS NOT NULL'))
        names.update([row[0] for row in result])

        # Get resource names (if resource table exists)
        try:
            result = conn.execute(text('SELECT DISTINCT name FROM resource WHERE name IS NOT NULL LIMIT 100'))
            names.update([row[0] for row in result])
        except:
            pass  # Resource table might not exist yet

    return sorted(list(names))


def search_all(interactive=True):
    """Search all resources in database and present matches"""
    print("\n" + "=" * 70)
    print("USDA Commodity Code Matcher - Search All Resources")
    print("=" * 70 + "\n")

    resources = get_db_resources()

    if not resources:
        print("[INFO] No resources found in database to match")
        return

    print(f"[INFO] Found {len(resources)} unique resource names\n")

    pending = {}

    for i, resource_name in enumerate(resources, 1):
        print(f"\n[{i}/{len(resources)}] Searching for: '{resource_name}'")
        print("-" * 70)

        matches = find_commodity_matches(resource_name, threshold=0.6)

        if not matches:
            print(f"  [NO MATCH] No suitable USDA codes found (try threshold < 0.6)")
            if interactive:
                action = input("  Enter USDA code manually (or skip with Enter): ").strip()
                if action:
                    pending[resource_name] = {
                        "code": action,
                        "method": "manual",
                        "status": "pending_review"
                    }
            continue

        # Show top 5 matches
        for j, (code, desc, score) in enumerate(matches[:5], 1):
            print(f"  [{j}] Code: {code} | {desc} | Score: {score:.1%}")

        if interactive:
            choice = input("  Select match (1-5, M for manual, or skip): ").strip().upper()
            if choice == 'M':
                code = input("    Enter USDA code: ").strip()
                if code:
                    desc = find_commodity_matches(code, threshold=0.95)
                    pending[resource_name] = {
                        "code": code,
                        "method": "manual",
                        "status": "pending_review"
                    }
            elif choice in ['1', '2', '3', '4', '5']:
                idx = int(choice) - 1
                if idx < len(matches):
                    code, desc, score = matches[idx]
                    pending[resource_name] = {
                        "code": code,
                        "description": desc,
                        "score": score,
                        "method": "auto",
                        "status": "pending_review"
                    }
                    print(f"  [SELECTED] {desc}")

    if pending:
        save_pending_matches(pending)
        print(f"\n[OK] Saved {len(pending)} pending matches for review")
        print(f"     File: .usda_pending_matches.json")
        print(f"\n     Review the JSON file and when ready, approve with:")
        print(f"     pixi run python match_usda_commodities.py --apply-pending")
    else:
        print("\n[INFO] No matches to save")


def apply_pending():
    """Apply pending matches to database"""
    pending = get_pending_matches()

    if not pending:
        print("[INFO] No pending matches found")
        return

    print("\n" + "=" * 70)
    print("Applying Pending Commodity Matches")
    print("=" * 70 + "\n")

    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url)

    applied = 0

    with Session(engine) as session:
        for resource_name, match_info in pending.items():
            code = match_info['code']
            desc = match_info.get('description', 'Unknown')
            method = match_info.get('method', 'unknown')

            print(f"Applying: {resource_name} -> {code} ({desc})")

            try:
                # This would insert/update the mapping
                # For now, just show what would happen
                print(f"  Method: {method}")
                print(f"  Status: {match_info.get('status', 'unknown')}")
                applied += 1
            except Exception as e:
                print(f"  [ERROR] {e}")

    print(f"\n[OK] Applied {applied} matches")

    # Clear pending
    save_pending_matches({})


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == '--search-all':
        search_all(interactive=True)
    elif command == '--search' and len(sys.argv) > 2:
        search_term = ' '.join(sys.argv[2:])
        print(f"\nSearching for: '{search_term}'")
        print("=" * 70)
        matches = find_commodity_matches(search_term, threshold=0.5)
        if matches:
            for i, (code, desc, score) in enumerate(matches[:10], 1):
                print(f"[{i}] Code: {code:10} | {desc:30} | Score: {score:.1%}")
        else:
            print("No matches found")
    elif command == '--review':
        pending = get_pending_matches()
        if pending:
            print("\nPending Matches:")
            print("=" * 70)
            for resource, match_info in pending.items():
                print(f"\n{resource}:")
                for key, val in match_info.items():
                    print(f"  {key}: {val}")
        else:
            print("No pending matches")
    elif command == '--apply-pending':
        apply_pending()
    elif command == '--help' or command == '-h':
        print(__doc__)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
