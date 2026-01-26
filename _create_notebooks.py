#!/usr/bin/env python
"""Create comprehensive Jupyter notebooks for USDA testing and commodity matching."""

import json
from pathlib import Path

# USDA Testing Notebook
usda_testing = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# USDA Ingestion Pipeline Testing\n\nComplete end-to-end testing of Extract→Transform→Load"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Setup Environment"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["import os, sys, json, pandas as pd\nfrom pathlib import Path\nfrom sqlalchemy import create_engine, text\nfrom datetime import datetime\n\nworkspace_root = Path(r'c:\\Users\\meili\\forked\\ca-biositing')\nsys.path.insert(0, str(workspace_root / 'src' / 'ca_biositing' / 'pipeline'))\nsys.path.insert(0, str(workspace_root / 'src' / 'ca_biositing' / 'datamodels'))\nos.chdir(str(workspace_root))\n\nfrom dotenv import load_dotenv\nload_dotenv(workspace_root / '.env')\nengine = create_engine(os.getenv('DATABASE_URL'))\n\nprint('✓ Environment configured')\nprint(f'✓ Working directory: {os.getcwd()}')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 1: Test Database Connection"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["try:\n    with engine.connect() as conn:\n        result = conn.execute(text('SELECT version();'))\n        version = result.fetchone()[0]\n        print(f'✓ Database connected')\n        print(f'  PostgreSQL: {version[:60]}...')\nexcept Exception as e:\n    print(f'✗ Database connection failed: {e}')\n    raise"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 2: Test Commodity Mapper"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["from ca_biositing.pipeline.utils.commodity_mapper import get_commodity_codes\n\nprint('Testing Commodity Mapper:')\nprint('='*50)\n\ntry:\n    commodity_codes = get_commodity_codes()\n    print(f'✓ Retrieved {len(commodity_codes)} commodity codes:')\n    for crop_name, usda_code in commodity_codes.items():\n        print(f'  - {crop_name}: {usda_code}')\nexcept Exception as e:\n    print(f'✗ Failed: {e}')\n    raise"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 3: Test USDA Extract (API)"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["from ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df\n\nprint('Testing USDA Extract (may take 30-60 seconds):')\nprint('='*50)\n\ncommodity_ids = list(commodity_codes.values())[:1]\nprint(f'Fetching for commodity: {commodity_ids[0]}\\n')\n\ntry:\n    raw_data = usda_nass_to_df(\n        commodity_codes=commodity_ids,\n        api_key=os.getenv('USDA_NASS_API_KEY')\n    )\n    print(f'✓ Extract successful!')\n    print(f'  Records: {len(raw_data)}')\n    print(f'  Columns: {list(raw_data.columns)}')\nexcept Exception as e:\n    print(f'✗ Extract failed: {e}')\n    raise"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 4: Test Transform"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["from ca_biositing.pipeline.etl.transform.usda.usda_census_survey import validate_and_clean_usda_data\n\nprint('Testing Transform:')\nprint('='*50)\n\nif 'raw_data' in locals() and len(raw_data) > 0:\n    try:\n        transformed_data = validate_and_clean_usda_data(raw_data.copy())\n        print(f'✓ Transform successful!')\n        print(f'  Before: {len(raw_data)} → After: {len(transformed_data)} records')\n        print(f'  Columns: {list(transformed_data.columns)}')\n    except Exception as e:\n        print(f'✗ Transform failed: {e}')\n        raise\nelse:\n    print('⚠ No data from extract')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 5: Test Load"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["from ca_biositing.pipeline.etl.load.usda.usda_census_survey import load_usda_data\n\nprint('Testing Load:')\nprint('='*50)\n\nif 'transformed_data' in locals() and len(transformed_data) > 0:\n    try:\n        etl_run_name = f'test_run_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}'\n        print(f'Loading {len(transformed_data)} records (ETL: {etl_run_name})\\n')\n        load_result = load_usda_data(transformed_data.copy(), etl_run_name, engine)\n        print(f'✓ Load successful: {load_result}')\n    except Exception as e:\n        print(f'✗ Load failed: {e}')\n        raise\nelse:\n    print('⚠ No data from transform')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 6: Verify Database Records"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["print('Querying Recent Records:')\nprint('='*60)\n\ntry:\n    with engine.connect() as conn:\n        result = pd.read_sql(\n            text('SELECT id, geoid, commodity_name, year, created_at FROM usda_census_record ORDER BY created_at DESC LIMIT 10'),\n            conn\n        )\n        if len(result) > 0:\n            print(f'✓ Found {len(result)} records:')\n            print(result.to_string(index=False))\n        else:\n            print('⚠ No records found')\nexcept Exception as e:\n    print(f'✗ Query failed: {e}')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Summary"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["print('\\n' + '='*60)\nprint('USDA INGESTION - TEST SUMMARY')\nprint('='*60)\n\nchecks = {\n    'Environment': True,\n    'Database': 'engine' in locals(),\n    'Commodity Mapper': 'commodity_codes' in locals() and len(commodity_codes) > 0,\n    'Extract': 'raw_data' in locals() and len(raw_data) > 0,\n    'Transform': 'transformed_data' in locals() and len(transformed_data) > 0,\n    'Load': 'etl_run_name' in locals(),\n    'Database Records': len(result) > 0 if 'result' in locals() else False,\n}\n\nfor test, passed in checks.items():\n    status = '✓' if passed else '✗'\n    print(f'  {status} {test}')\n\nif all(checks.values()):\n    print('\\n🎉 ALL TESTS PASSED - USDA INGESTION WORKING!')\nelse:\n    print('\\n⚠ Some tests failed - see details above')\nprint('='*60)"]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "ca-biositing (Pixi)",
            "language": "python",
            "name": "ca-biositing"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Commodity Matcher Notebook
matcher_notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["# USDA Commodity Matcher Workflow\n\nIntelligently match resources to USDA commodity codes using fuzzy matching"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Setup"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["import os, sys, json, pandas as pd\nfrom pathlib import Path\nfrom sqlalchemy import create_engine, text\nfrom difflib import SequenceMatcher\nfrom datetime import datetime\n\nworkspace_root = Path(r'c:\\Users\\meili\\forked\\ca-biositing')\nsys.path.insert(0, str(workspace_root / 'src' / 'ca_biositing' / 'pipeline'))\nos.chdir(str(workspace_root))\n\nfrom dotenv import load_dotenv\nload_dotenv(workspace_root / '.env')\nengine = create_engine(os.getenv('DATABASE_URL'))\n\nprint('✓ Environment configured')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 1: Display Available USDA Commodities"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["with engine.connect() as conn:\n    usda_commodities = pd.read_sql(\n        text('SELECT id, usda_code, commodity_name FROM usda_commodity ORDER BY commodity_name'),\n        conn\n    )\n\nprint(f'Available USDA Commodities ({len(usda_commodities)} total):')\nprint('='*60)\nprint(usda_commodities.to_string(index=False))"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 2: Query Unmapped Resources"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["with engine.connect() as conn:\n    unmapped = pd.read_sql(\n        text('SELECT r.id, r.name FROM resource r LEFT JOIN resource_usda_commodity_map rum ON r.id = rum.resource_id WHERE rum.resource_id IS NULL ORDER BY r.name'),\n        conn\n    )\n\nprint(f'Resources Needing Mapping: {len(unmapped)} total')\nprint('='*60)\nif len(unmapped) > 0:\n    print(unmapped.head(15).to_string(index=False))\n    if len(unmapped) > 15:\n        print(f'... and {len(unmapped) - 15} more')\nelse:\n    print('✓ All resources already mapped!')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 3: Test Fuzzy Matching"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["if len(unmapped) > 0:\n    test_resource = unmapped.iloc[0]['name']\n    print(f'Testing Fuzzy Match: \"{test_resource}\"')\n    print('='*60)\n    \n    matches = []\n    for _, comm in usda_commodities.iterrows():\n        sim = SequenceMatcher(None, test_resource.lower(), comm['commodity_name'].lower()).ratio()\n        matches.append({'commodity': comm['commodity_name'], 'code': comm['usda_code'], 'score': f'{sim:.1%}'})\n    \n    matches_df = pd.DataFrame(matches).sort_values('score', ascending=False)\n    print('\\nTop 5 Matches:')\n    print(matches_df.head(5).to_string(index=False))\n    print(f'\\nBest: {matches_df.iloc[0][\"commodity\"]} ({matches_df.iloc[0][\"score\"]})')\nelse:\n    print('No unmapped resources to test')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 4: Load Pending Matches"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["pending_file = workspace_root / '.usda_pending_matches.json'\n\nif pending_file.exists():\n    with open(pending_file, 'r') as f:\n        pending = json.load(f)\n    print(f'✓ Loaded {len(pending)} pending matches')\nelse:\n    pending = {}\n    print(f'✓ Starting fresh (no existing matches)')\n    print(f'  Will create: {pending_file}')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 5: View Pending Matches Status"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["if len(pending) > 0:\n    approved = sum(1 for m in pending.values() if m.get('status') == 'approved')\n    applied = sum(1 for m in pending.values() if m.get('status') == 'applied')\n    print(f'Pending Matches ({len(pending)} total):')\n    print(f'  - Approved: {approved}')\n    print(f'  - Applied: {applied}')\nelse:\n    print('No pending matches')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Step 6: Verify Mappings in Database"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["with engine.connect() as conn:\n    result = pd.read_sql(\n        text('SELECT r.name, uc.commodity_name, uc.usda_code FROM resource_usda_commodity_map rum JOIN resource r ON r.id = rum.resource_id JOIN usda_commodity uc ON uc.id = rum.usda_commodity_id LIMIT 20'),\n        conn\n    )\n\nprint(f'Database Mappings ({len(result)} recent):')\nprint('='*60)\nif len(result) > 0:\n    print(result.to_string(index=False))\nelse:\n    print('No mappings in database yet')"]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": ["## Summary"]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": ["with engine.connect() as conn:\n    total = conn.execute(text('SELECT COUNT(*) FROM resource')).fetchone()[0]\n    mapped = conn.execute(text('SELECT COUNT(DISTINCT resource_id) FROM resource_usda_commodity_map')).fetchone()[0]\n    unmapped_count = total - mapped\n\nprint('\\n' + '='*60)\nprint('COMMODITY MATCHER - SUMMARY')\nprint('='*60)\nprint(f'Total Resources: {total}')\nprint(f'Mapped: {mapped}')\nprint(f'Awaiting: {unmapped_count}')\nif total > 0:\n    print(f'Coverage: {(mapped/total*100):.1f}%')\n    if mapped == total:\n        print('\\n🎉 ALL RESOURCES MAPPED!')\nprint('='*60)"]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "ca-biositing (Pixi)",
            "language": "python",
            "name": "ca-biositing"
        },
        "language_info": {
            "name": "python",
            "version": "3.12.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Write notebooks
workspace = Path(r'c:\Users\meili\forked\ca-biositing')

with open(workspace / 'USDA_Ingestion_Testing.ipynb', 'w') as f:
    json.dump(usda_testing, f, indent=2)
print("✓ Created USDA_Ingestion_Testing.ipynb")

with open(workspace / 'Commodity_Matcher_Workflow.ipynb', 'w') as f:
    json.dump(matcher_notebook, f, indent=2)
print("✓ Created Commodity_Matcher_Workflow.ipynb")

print("\n✓ Both Jupyter notebooks created successfully!")
