# Quick Reference: Names vs IDs in Your USDA Pipeline

## Complete Name-Based Workflow

### 1. Bootstrap: Adding Commodities (Simple Manual Approach)

```python
# resources/prefect/flows/bootstrap_usda_commodities.py

from prefect import flow, task
from sqlmodel import Session
from ca_biositing.datamodels import UsdaCommodity
from ca_biositing.datamodels.database import engine

# Just list the commodities YOUR team cares about
COMMODITIES_TO_ADD = [
    "ALMONDS",
    "CORN",
    "WHEAT",
    "SOYBEANS",
    "RICE, LONG GRAIN",
]

@task
def add_commodities():
    """Add commodities to database using NAMES."""
    with Session(engine) as session:
        for name in COMMODITIES_TO_ADD:
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

@flow(name="Bootstrap USDA Commodities")
def bootstrap():
    """One-time: Add commodities to system."""
    add_commodities()
    print("✓ Bootstrap complete! Commodities added.")

# Run once:
# python -c "from bootstrap_usda_commodities import bootstrap; bootstrap()"
```

**Result in database:**

```
usda_commodity table:
id | name                | usda_source
---|---------------------|------------
1  | ALMONDS             | NASS
2  | CORN                | NASS
3  | WHEAT               | NASS
4  | SOYBEANS            | NASS
5  | RICE, LONG GRAIN    | NASS
```

---

### 2. Manual Mapping: Your Crops to USDA Commodities

```sql
-- Your team does this ONCE (using SQL or app)
-- Link your crops to USDA commodities by NAME

-- First, see what commodities exist
SELECT id, name FROM usda_commodity ORDER BY name;

-- Then create mappings
-- Almond → ALMONDS
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier, note)
SELECT
  1,                                  -- Your Almond crop
  uc.id,                             -- USDA commodity ID (looked up by name)
  'DIRECT_MATCH',
  'Primary product: Almond matches USDA ALMONDS'
FROM usda_commodity uc
WHERE uc.name = 'ALMONDS';

-- Corn → CORN
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier, note)
SELECT
  2,                                  -- Your Corn crop
  uc.id,
  'DIRECT_MATCH',
  'Primary product: Corn matches USDA CORN'
FROM usda_commodity uc
WHERE uc.name = 'CORN';

-- Verify mappings were created
SELECT
  pap.name AS crop,
  uc.name AS usda_commodity,
  rum.match_tier
FROM resource_usda_commodity_map rum
JOIN primary_ag_product pap ON rum.primary_ag_product_id = pap.id
JOIN usda_commodity uc ON rum.usda_commodity_id = uc.id;
```

**Result:**

```
crop     | usda_commodity  | match_tier
---------|-----------------|------------
Almond   | ALMONDS         | DIRECT_MATCH
Corn     | CORN            | DIRECT_MATCH
```

---

### 3. Extract: Reading Names from Database

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/utils/commodity_mapper.py

from typing import Optional, List
from sqlmodel import Session, select
from ca_biositing.datamodels import ResourceUsdaCommodityMap, UsdaCommodity
from ca_biositing.datamodels.database import engine

def get_mapped_commodity_names() -> Optional[List[str]]:
    """
    Get list of USDA commodity NAMES that are mapped to your resources.

    Example return:
        ["ALMONDS", "CORN", "WHEAT"]
    """
    try:
        with Session(engine) as session:
            # Join tables to get NAMES instead of IDs
            statement = select(UsdaCommodity.name).where(
                UsdaCommodity.id.in_(
                    select(ResourceUsdaCommodityMap.usda_commodity_id)
                )
            ).distinct()

            results = session.exec(statement).all()

            if results:
                print(f"Found mapped commodities: {results}")
                return list(results)
            else:
                print("No commodity mappings found")
                return None

    except Exception as e:
        print(f"Error getting commodities: {e}")
        return None
```

**Test it:**

```python
from commodity_mapper import get_mapped_commodity_names

names = get_mapped_commodity_names()
print(names)
# Output: ["ALMONDS", "CORN"]
```

---

### 4. Utility: Query API Using Names

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/utils/usda_nass_to_pandas.py

import requests
import pandas as pd
from typing import Optional, List

def usda_nass_to_df(
    api_key: str,
    state: str = "CA",
    year: Optional[int] = None,
    commodity_names: Optional[List[str]] = None,  # ← Accept NAMES!
    **kwargs
) -> Optional[pd.DataFrame]:
    """
    Fetch USDA data using commodity NAMES (like "ALMONDS", "CORN").

    Args:
        commodity_names: List of names like ["ALMONDS", "CORN", "WHEAT"]

    Returns:
        DataFrame with USDA data
    """
    BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET"

    if commodity_names is not None:
        print(f"Querying {len(commodity_names)} commodities: {commodity_names}")
        all_dfs = []

        for name in commodity_names:
            print(f"  Fetching {name}...")

            params = {
                "key": api_key,
                "state_alpha": state,
                "format": "JSON",
                "commodity_desc": name,  # ← Use the NAME!
            }

            if year is not None:
                params["year"] = year

            params.update(kwargs)

            try:
                response = requests.get(BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                if data and not isinstance(data, dict):
                    df = pd.DataFrame(data)
                    print(f"    {name}: {len(df)} records")
                    all_dfs.append(df)
            except Exception as e:
                print(f"    Error: {e}")

        if all_dfs:
            result = pd.concat(all_dfs, ignore_index=True)
            print(f"Total: {len(result)} records from {len(commodity_names)} commodities")
            return result
        else:
            print("No data returned")
            return pd.DataFrame()

    # Fallback if no names provided
    return None
```

**Test it:**

```python
from usda_nass_to_pandas import usda_nass_to_df

df = usda_nass_to_df(
    api_key="your_api_key",
    commodity_names=["ALMONDS", "CORN"],
    state="CA",
    year=2023
)
print(df)
```

---

### 5. Extract Function: Puts It All Together

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py

import os
import pandas as pd
from typing import Optional
from prefect import task, get_run_logger
from pipeline.utils.commodity_mapper import get_mapped_commodity_names
from pipeline.utils.usda_nass_to_pandas import usda_nass_to_df

# Configuration
USDA_API_KEY = os.getenv("USDA_NASS_API_KEY", "")
STATE = "CA"
YEAR = None  # All years

@task
def extract() -> Optional[pd.DataFrame]:
    """
    Extract USDA data for mapped commodities (using NAMES).

    The extract reads which commodities your team cares about from
    the database, then fetches only those commodities from USDA.
    """
    logger = get_run_logger()

    # Step 1: Get commodity NAMES from database
    commodity_names = get_mapped_commodity_names()

    if not commodity_names:
        logger.warning(
            "No commodity mappings found in resource_usda_commodity_map. "
            "Please run bootstrap flow and create mappings."
        )
        return None

    logger.info(f"Extracting data for: {', '.join(commodity_names)}")

    # Step 2: Query USDA API with commodity NAMES
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state=STATE,
        year=YEAR,
        commodity_names=commodity_names  # ← Uses NAMES!
    )

    if raw_df is None:
        logger.error("Failed to extract data from USDA API.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records.")
    return raw_df
```

---

## Complete Data Flow (Name-Based)

```
┌─────────────────────────────────────────────────────────────────┐
│ BOOTSTRAP (Once)                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Your team lists: ["ALMONDS", "CORN", "WHEAT"]              │
│                                                                 │
│  2. Bootstrap flow inserts into usda_commodity:                │
│     id=1, name="ALMONDS"                                        │
│     id=2, name="CORN"                                           │
│     id=3, name="WHEAT"                                          │
│                                                                 │
│  3. Team creates mappings using SQL:                            │
│     resource_usda_commodity_map links:                          │
│     primary_ag_product.Almond → usda_commodity.ALMONDS         │
│     primary_ag_product.Corn → usda_commodity.CORN              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ OPERATIONAL (Every run)                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Extract reads database:                                     │
│     SELECT DISTINCT usda_commodity.name                         │
│     Result: ["ALMONDS", "CORN"]                                 │
│                                                                 │
│  2. Extract calls USDA API:                                     │
│     API call 1: ?commodity_desc=ALMONDS&state=CA               │
│     API call 2: ?commodity_desc=CORN&state=CA                  │
│                                                                 │
│  3. USDA returns data (uses names internally):                  │
│     [                                                           │
│       {commodity_desc: "ALMONDS", value: 5000, ...},           │
│       {commodity_desc: "CORN", value: 10000, ...}              │
│     ]                                                           │
│                                                                 │
│  4. Load into database                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary: Why Names Are Better

| Aspect                   | Names                       | IDs              |
| ------------------------ | --------------------------- | ---------------- |
| **What you see in logs** | `["ALMONDS", "CORN"]`       | `[1, 5]`         |
| **What USDA API uses**   | ✅ commodity_desc="ALMONDS" | ❌ Must convert  |
| **SQL queries**          | ✅ WHERE name = 'ALMONDS'   | ❌ WHERE id = 1  |
| **Human readability**    | ✅ Obvious                  | ❌ Need lookup   |
| **Database lookups**     | ✅ Natural                  | ❌ Requires join |
| **Debugging**            | ✅ Easy to trace            | ❌ Confusing     |

**Recommendation**: Use names throughout! It's more user-friendly and matches
how USDA works naturally.
