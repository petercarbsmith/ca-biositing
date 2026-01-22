# Implementation Checklist: Making Your Extract Database-Driven

## Current State

Your extract currently does this:

```python
# usda_census_survey.py
COMMODITY = None  # or hardcoded value

raw_df = usda_nass_to_df(
    api_key=USDA_API_KEY,
    state=STATE,
    year=YEAR,
    commodity=COMMODITY
)
```

**Problem**: Either imports everything (slow) or requires code change to add new
crops.

---

## Desired End State

```python
# usda_census_survey.py
mapped_commodity_ids = _get_mapped_commodity_ids_from_database()

raw_df = usda_nass_to_df(
    api_key=USDA_API_KEY,
    state=STATE,
    year=YEAR,
    commodity_ids=mapped_commodity_ids  # ← Database controls this
)
```

**Benefit**: Add new crops by updating database; no code changes needed.

---

## Implementation Checklist

### ✅ Phase 1: Preparation (No Breaking Changes)

- [x] Read all strategy documents
- [x] Review your `resource_usda_commodity_map` table structure
- [x] Identify your key commodities (3-5 to start)
- [x] Get list of USDA commodity codes for those commodities. Commodity codes
      can be found at
      https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/commcodes.php

Example 37899999 - Tomatoes 26199999 - Almonds 26399999 - Walnuts (English)
39299999 - Sweetpotatoes 11199999 - Corn

### ✅ Phase 2: Create Infrastructure (Non-Blocking)

**Create new utility file**:
`src/ca_biositing/pipeline/ca_biositing/pipeline/utils/commodity_mapper.py`

```python
from typing import List, Optional
from sqlmodel import Session, select
from ca_biositing.datamodels import ResourceUsdaCommodityMap

def get_mapped_commodity_ids() -> Optional[List[int]]:
    """Get USDA commodity IDs mapped to our resources from database."""
    try:
        from ca_biositing.datamodels.database import engine

        with Session(engine) as session:
            statement = select(
                ResourceUsdaCommodityMap.usda_commodity_id
            ).distinct()

            results = session.exec(statement).all()
            return list(results) if results else None
    except Exception as e:
        print(f"Error querying mapped commodities: {e}")
        return None
```

**Checklist items**:

- [x] Create `commodity_mapper.py` file
- [?] Import correct modules from your datamodels
- [x] Test the function (should return None if no mappings yet)

### ✅ Phase 3: Update Utility Function (Backward Compatible)

**Modify**:
`src/ca_biositing/pipeline/ca_biositing/pipeline/utils/usda_nass_to_pandas.py`

**Add this parameter** to function signature:

```python
from typing import List

def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity: Optional[str] = None,
    commodity_ids: Optional[List[int]] = None,  # ← NEW PARAMETER
    **kwargs
) -> Optional[pd.DataFrame]:
```

**Add this logic** inside the function (after checking parameters):

```python
    # NEW: Handle commodity_ids parameter
    if commodity_ids is not None:
        logger.info(f"Querying {len(commodity_ids)} commodities by ID...")
        all_dfs = []

        for comm_id in commodity_ids:
            query_params = params.copy()
            query_params["commodity_code"] = comm_id  # API parameter for ID

            try:
                response = requests.get(BASE_URL, params=query_params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data and not isinstance(data, dict):
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
                    logger.info(f"  Commodity {comm_id}: {len(df)} records")
            except Exception as e:
                logger.error(f"  Error querying commodity {comm_id}: {e}")

        if all_dfs:
            result = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"Total: {len(result)} records from {len(commodity_ids)} commodities")
            return result
        else:
            logger.warning("No data returned for any commodity")
            return pd.DataFrame()

    # EXISTING CODE: Fall back to commodity name if IDs not provided
    if commodity is not None:
        params["commodity_desc"] = commodity
```

**Checklist items**:

- [x] Add `commodity_ids` parameter to function signature
- [x] Add loop to query multiple commodities
- [x] Maintain backward compatibility (existing `commodity` parameter still
      works)
- [?] Test with both old and new parameters

### ✅ Phase 4: Update Extract Function (The Key Change)

**Modify**:
`src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py`

**Add import**:

```python
from pipeline.utils.commodity_mapper import get_mapped_commodity_ids
```

**Replace the extract function**:

```python
@task
def extract() -> Optional[pd.DataFrame]:
    """
    Extracts USDA data ONLY for commodities mapped in resource_usda_commodity_map.

    This allows adding new crops by updating the database, no code changes needed.
    """
    logger = get_run_logger()

    # Get commodity IDs from database
    commodity_ids = get_mapped_commodity_ids()

    if not commodity_ids:
        logger.warning(
            "No commodity mappings found in resource_usda_commodity_map. "
            "Please run bootstrap_usda_commodities flow to populate commodities, "
            "then create mappings for your crops."
        )
        return None

    logger.info(f"Extracting USDA data for {len(commodity_ids)} commodities...")

    # Call utility with commodity IDs (not names)
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_ids=commodity_ids  # ← Database-driven!
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API. Aborting.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records from USDA NASS API.")
    return raw_df
```

**Checklist items**:

- [x] Add import for `get_mapped_commodity_ids`
- [x] Replace extract function with new version
- [x] Maintain same return type (DataFrame or None)
- [x] Keep error handling
- [?] Test locally

### ✅ Phase 5: Create Bootstrap Flow (Optional, For Later)

**Create**: `resources/prefect/flows/bootstrap_usda_commodities.py`

```python
from prefect import flow, task, get_run_logger
from ca_biositing.pipeline.utils.usda_nass_to_pandas import get_available_parameters
from ca_biositing.datamodels import UsdaCommodity
from sqlmodel import Session
from ca_biositing.datamodels.database import engine
import os

@task
def fetch_commodities_from_api(api_key: str):
    """Download list of all NASS commodities from USDA API."""
    logger = get_run_logger()
    logger.info("Fetching commodity list from USDA NASS API...")

    params = get_available_parameters(api_key)

    if "commodity_desc" not in params:
        logger.error("Failed to fetch commodities")
        return None

    logger.info(f"Found {len(params['commodity_desc'])} commodities")
    return params['commodity_desc']

@task
def insert_commodities(commodity_names):
    """Insert commodities into usda_commodity table."""
    logger = get_run_logger()
    logger.info(f"Inserting {len(commodity_names)} commodities into database...")

    with Session(engine) as session:
        for name in commodity_names:
            # Check if already exists
            existing = session.query(UsdaCommodity).filter(
                UsdaCommodity.name == name
            ).first()

            if not existing:
                commodity = UsdaCommodity(
                    name=name,
                    usda_source="NASS",
                    description=f"NASS commodity: {name}"
                )
                session.add(commodity)

        session.commit()

    logger.info("Bootstrap complete!")

@flow(name="Bootstrap USDA Commodities")
def bootstrap_usda_commodities():
    """One-time: Download all USDA commodities and populate lookup table."""
    api_key = os.getenv("USDA_NASS_API_KEY")

    if not api_key:
        print("ERROR: USDA_NASS_API_KEY not set in environment")
        return

    commodities = fetch_commodities_from_api(api_key)
    if commodities:
        insert_commodities(commodities)

# Don't forget to register this with Prefect!
# Add to your deployment configuration
```

**Checklist items**:

- [x] Create file
- [ ] Use get_available_parameters utility
- [ ] Test the flow independently (don't run yet!)
- [ ] Add to deployment configuration

### ✅ Phase 6: Manual Setup (Your Team - Database Mappings)

**Step 1: Access Your Database Using DBCode**

1. Open VS Code
2. Click the **DBCode** icon in the sidebar (or open command palette and search
   "DBCode")
3. If not already connected, create connection:
   - Host: `localhost`
   - Port: `5432`
   - Username/Password: from `resources/docker/.env`
   - Database: `ca_biositing`
4. Right-click the connection → **New Query**
5. Paste SQL commands below

**Step 2: Understand Your Data**

```sql
-- See USDA commodities available
SELECT id, code, name FROM usda_commodity ORDER BY id;
-- Example: 1 | 26399999 | Walnuts, 2 | 26199999 | Almonds, 5 | 11199999 | Corn

-- See YOUR resources
SELECT id, name FROM primary_ag_product ORDER BY id;
-- Example: 1 | Almond, 2 | Corn, 3 | Walnut
```

**Step 3: Create Mappings**

```sql
-- Link YOUR Almond crop to USDA Almonds (IDs from Step 2)
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier)
VALUES (1, 2, 'DIRECT_MATCH');  -- Your #1 → USDA #2

-- Link YOUR Corn crop to USDA Corn
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier)
VALUES (2, 5, 'DIRECT_MATCH');  -- Your #2 → USDA #5
```

**Step 4: Verify**

```sql
SELECT pap.name, uc.name FROM resource_usda_commodity_map rum
JOIN primary_ag_product pap ON rum.primary_ag_product_id = pap.id
JOIN usda_commodity uc ON rum.usda_commodity_id = uc.id;
-- Should show: Almond | Almonds, Corn | Corn
```

**Checklist items**:

- [ ] Access database
- [ ] Run Step 2 queries
- [ ] Write INSERT for YOUR crops (using IDs from Step 2)
- [ ] Run INSERT commands
- [ ] Run Step 4 verification (should see your crops, not 0 rows)

### ✅ Phase 7: Testing (Step-by-Step)

**Important**: Tests 1-3 are INDEPENDENT LOCAL TESTS (separate from Phase 2-5
"test locally")

- Test 1: Can code read database?
- Test 2: Can code call USDA API?
- Test 3: Does extract function work?
- Test 4: Does full Docker pipeline work?

#### Test 1: Database Utility (Do Mappings Exist?)

```python
# Run locally (NOT in Docker)
from src.ca_biositing.pipeline.ca_biositing.pipeline.utils.commodity_mapper import get_mapped_commodity_ids

ids = get_mapped_commodity_ids()
print(f"IDs: {ids}")
```

**Expected**: `IDs: [2, 5]` (or whatever IDs you mapped in Phase 6) **If 0 or
None**: Go back to Phase 6, re-run verification query

#### Test 2: USDA API (Can We Fetch Data?)

```python
# Run locally
from src.ca_biositing.pipeline.ca_biositing.pipeline.utils.usda_nass_to_pandas import usda_nass_to_df

df = usda_nass_to_df(
    api_key="your_api_key",
    state="CA",
    commodity_ids=[2, 5],
    year=2023
)
print(f"Rows: {len(df)}")
print(df.head())
```

**Expected**: DataFrame with 50+ rows, columns like 'Commodity', 'Value', 'Year'
**If error**: Check API key is correct, internet connection works

#### Test 3: Extract Function (Full Local Test)

```python
# Run locally
from src.ca_biositing.pipeline.ca_biositing.pipeline.etl.extract.usda_census_survey import extract

df = extract()
print(f"Rows: {len(df)}")
print(df.head())
```

**Expected**: DataFrame with data (row count depends on commodities mapped) **If
error**: Tests 1-2 must pass first

#### Test 4: Full Docker Pipeline

```bash
pixi run deploy
pixi run run-etl
pixi run service-logs
```

**Expected**: See "Task finished successfully" in logs, check
http://0.0.0.0:4200 for green checkmarks **If error**: See Phase 8
troubleshooting

**Checklist items**:

- [ ] Test 1: Returns commodity IDs (not None/0)
- [ ] Test 2: Returns data from USDA API
- [ ] Test 3: Extract function completes
- [ ] Test 4: Docker pipeline succeeds

### ✅ Phase 8: Deployment (When Ready)

```bash
# Commit all changes
git add .
git commit -m "feat: make USDA extract database-driven for easier crop additions"

# Deploy (when ready)
pixi run deploy

# Run ETL
pixi run run-etl
```

**Checklist items**:

- [ ] All tests pass locally
- [ ] Code reviewed by team
- [ ] Changes committed
- [ ] Deployed to test environment
- [ ] Monitor logs for issues

---

## Rollback Plan (If Needed)

If something goes wrong, you can safely rollback because the changes are
backward compatible:

```python
# Fall back to old behavior temporarily
raw_df = usda_nass_to_df(
    api_key=USDA_API_KEY,
    state=STATE,
    year=YEAR,
    commodity="CORN"  # Use old parameter
    # commodity_ids not provided → uses old code path
)
```

---

## Before/After Comparison

### Before: Hardcoded or All Data

```python
# Configuration (in code)
COMMODITY = "CORN"  # or None

# Extract
raw_df = usda_nass_to_df(..., commodity=COMMODITY)

# Problem: To add wheat, must edit code and redeploy
```

### After: Database-Driven

```python
# Configuration (in database)
# INSERT INTO resource_usda_commodity_map ...

# Extract
mapped_ids = get_mapped_commodity_ids()  # Reads DB
raw_df = usda_nass_to_df(..., commodity_ids=mapped_ids)

# Benefit: To add wheat, just SQL (no code deployment needed!)
```

---

## Success Criteria

You'll know you're done when:

- ✅ Extract function reads commodity list from database
- ✅ Adding a new crop requires only a SQL INSERT (no code change)
- ✅ Tests pass with different commodity mappings
- ✅ Pipeline logs show only mapped commodities are imported
- ✅ Team can add crops without involving engineers

---

## Time Estimate

### Conservative Path (5 Weeks)

Spread across multiple weeks with team review cycles between phases.

### Recommended Path (2-3 Days)

**Day 1** (3-4 hours): Code everything **Day 2** (2-3 hours): Integration
testing + database setup **Day 3** (1-2 hours): Deploy + monitor

### Fast Path (1 Day - 6-7 Hours)

All phases in sequence if you have a clear day:

| Phase             | Effort                        | Time          |
| ----------------- | ----------------------------- | ------------- |
| 1. Preparation    | Read docs                     | 30 min        |
| 2. Create utils   | Code commodity_mapper.py      | 1 hour        |
| 3. Update utility | Update usda_nass_to_pandas.py | 1 hour        |
| 4. Update extract | Modify to use database        | 30 min        |
| 5. Bootstrap flow | Create bootstrap flow         | 1 hour        |
| 6. Manual setup   | Create DB mappings            | 30 min        |
| 7. Testing        | Test all steps                | 1 hour        |
| 8. Deployment     | Deploy & monitor              | 30 min        |
| **Total**         |                               | **6-7 hours** |

**See [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md) for
timeline options**

---

## Need Help?

Refer back to:

- **Why**: USDA_DATA_IMPORT_STRATEGY.md
- **How**: USDA_EXTRACT_ENHANCEMENT_TACTICAL.md
- **Visual**: USDA_IMPORT_DECISION_TREE.md

You've got this! 🚀
