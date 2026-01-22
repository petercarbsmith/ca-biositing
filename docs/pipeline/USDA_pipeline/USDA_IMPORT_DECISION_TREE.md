# USDA Import Strategy: Visual Decision Guide

## Decision Tree: Which Approach for Your Project?

```
START: Import USDA data
│
├─ Question 1: Do you already have mappings in resource_usda_commodity_map?
│  │
│  ├─ YES → Question 2
│  │
│  └─ NO → Go to PHASE 1: Bootstrap
│            (Create commodity hierarchy + manual mappings)
│
├─ Question 2: Do you need ALL commodities or just yours?
│  │
│  ├─ ALL commodities → Option A (Full Import)
│  │   Use when: Exploratory, unlimited storage, discovery mode
│  │
│  └─ ONLY mapped → Question 3
│
├─ Question 3: Is your crop list stable (won't change)?
│  │
│  ├─ STABLE → Option B (Filtered Query)
│  │   Use when: Fixed crop set, limited storage, production
│  │
│  └─ GROWING → Option C (Hybrid) ⭐ RECOMMENDED
│      Use when: You'll add new crops, want flexibility, future-proof
│
END: Choose implementation approach
```

---

## At-a-Glance Comparison

```
┌─────────────────────────┬────────────────────┬────────────────────┬────────────────────┐
│ Factor                  │ Option A (All)     │ Option B (Filtered) │ Option C (Hybrid)  │
├─────────────────────────┼────────────────────┼────────────────────┼────────────────────┤
│ Database Size           │ 100K+ rows/year    │ 1-5K rows/year     │ 1-5K rows/year     │
│ API Calls               │ Many (>50K limit)  │ Few (efficient)    │ Few (efficient)    │
│ Setup Complexity        │ Low                │ Medium (mappings)  │ Medium (bootstrap) │
│ Operational Complexity  │ High (filter later)│ Low                │ Low                │
│ Future Scalability      │ Good               │ Poor (code changes)│ Excellent (data)   │
│ Discovery               │ Yes (see all data) │ No (filtered out)  │ Possible (manual)  │
│ Storage Cost            │ High               │ Low                │ Low                │
│ Data Integrity Risk     │ Orphaned records   │ Low                │ Low                │
├─────────────────────────┼────────────────────┼────────────────────┼────────────────────┤
│ Recommended for ca-bio..│ ❌ No              │ ❌ Maybe           │ ⭐ YES!            │
└─────────────────────────┴────────────────────┴────────────────────┴────────────────────┘
```

---

## Data Flow Diagrams

### Option A: Import All Data

```
USDA NASS API (all commodities)
        │
        ↓ (50K record chunks)
    Extract ALL
        │
        ↓ (DataFrame: all commodities)
    Transform
        │
        ├─ Join with resource_usda_commodity_map ← Database lookup
        ├─ Filter to mapped only
        └─ Enrich/clean
        │
        ↓ (Filtered DataFrame)
    Load
        │
        ↓
    usda_census_record (hundreds of thousands of rows)
        │
    Query 1: SELECT * WHERE usda_commodity_id IN (mapped_ids)
    Takes time to filter & join at query time
```

**Problem**: You're moving the filtering work to QUERY TIME instead of IMPORT
TIME.

---

### Option B: Query with Filters

```
Get mapped commodity list from DB
        │
        ├─ Query: SELECT usda_commodity_id FROM resource_usda_commodity_map
        └─ Result: [1, 5, 12, 18, ...]
        │
        ↓
USDA NASS API (filtered query)
        │
        ├─ ?key=KEY&commodity_desc=CORN&state_alpha=CA&year=2023
        ├─ ?key=KEY&commodity_desc=ALMONDS&state_alpha=CA&year=2023
        └─ etc.
        │
        ↓ (Only relevant records)
    Extract
        │
        ↓
    Transform (just enrich, no filtering)
        │
        ↓
    Load
        │
        ↓
    usda_census_record (only thousands of rows)
        │
    Query 1: SELECT * ← Fast, small table
```

**Pro**: Efficient, but tightly couples Extract to database state. **Con**:
Can't add new crops without code changes.

---

### Option C: Hybrid (Recommended)

```
┌──────────────────── PHASE 1: BOOTSTRAP (One-Time) ──────────────────────┐
│                                                                         │
│  bootstrap_usda_commodities.py flow:                                   │
│                                                                         │
│  USDA API (get_param_values)                                           │
│     │                                                                   │
│     ├─ Get ALL commodities for NASS                                    │
│     └─ Get ALL commodities for AMS                                     │
│     │                                                                   │
│     ↓                                                                   │
│  Build hierarchy in memory                                             │
│     │                                                                   │
│     ├─ ALMONDS (NASS, code=16020, parent=TREE NUTS)                   │
│     ├─ CORN (NASS, code=12010, parent=FIELD CROPS)                   │
│     ├─ ALMOND HULLS (AMS, code=16025, parent=ALMONDS)                │
│     └─ ...                                                              │
│     │                                                                   │
│     ↓                                                                   │
│  Insert into usda_commodity                                            │
│     │                                                                   │
│     ↓                                                                   │
│  usda_commodity table (populated ✓)                                    │
│                                                                         │
│  [MANUAL STEP - Your Team]                                             │
│  Create mappings in resource_usda_commodity_map:                       │
│     - PRIMARY_AG_PRODUCT.Almond → USDA_COMMODITY.ALMONDS             │
│     - PRIMARY_AG_PRODUCT.Corn → USDA_COMMODITY.CORN                  │
│     - Set match_tier: DIRECT_MATCH, CROP_FALLBACK, etc.             │
│                                                                         │
│  resource_usda_commodity_map table (populated ✓)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓ (Ready)
┌──────────────────── PHASE 2: OPERATIONAL (Repeating) ──────────────────┐
│                                                                         │
│  usda_census_survey.py flow (runs daily/weekly):                       │
│                                                                         │
│  1. Get mapped commodities:                                             │
│     SELECT usda_commodity_id FROM resource_usda_commodity_map          │
│     Result: [1, 5, 12, 18, ...]                                       │
│     │                                                                   │
│  2. Extract ONLY those:                                                │
│     USDA API with commodity filter                                     │
│     ?commodity_code IN [1,5,12,18]                                    │
│     │                                                                   │
│  3. Transform (enrich/validate)                                        │
│     │                                                                   │
│  4. Load into usda_census_record                                       │
│                                                                         │
│  Result: Clean, focused dataset ✓                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────── LATER: ADD NEW CROPS (Easy!) ────────────────────────┐
│                                                                           │
│  Your team says: "We want to start tracking WHEAT"                       │
│                                                                           │
│  SQL INSERT:                                                             │
│  INSERT INTO resource_usda_commodity_map                                 │
│    (primary_ag_product_id=6, usda_commodity_id=12, match_tier='...')  │
│                                                                           │
│  Next time extract runs: WHEAT data automatically included ✓              │
│  NO CODE CHANGES NEEDED!                                                 │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Your Schema Shows This is the Right Approach

```sql
-- resource_usda_commodity_map is designed for THIS
CREATE TABLE resource_usda_commodity_map (
    id INTEGER PRIMARY KEY,
    resource_id INTEGER,                    -- Can link specific resources
    primary_ag_product_id INTEGER,          -- Or general crops
    usda_commodity_id INTEGER NOT NULL,     -- Links to USDA hierarchy
    match_tier TEXT,                        -- DIRECT_MATCH, FALLBACK, etc.
    note TEXT,
    -- ... metadata columns
);

-- Your design allows:
-- 1. Hierarchical matching (almonds → tree nuts)
-- 2. Multiple match types (flexible)
-- 3. Easy expansion (add row, done!)
-- 4. Traceable lineage (note column explains mapping)
```

This table was purpose-built for **Option C**!

---

## Code Example: The Implementation

### Step 1: Bootstrap (One-time setup)

```python
# resources/prefect/flows/bootstrap_usda_commodities.py

from prefect import flow, task
from ca_biositing.pipeline.utils.usda_nass_to_pandas import get_available_parameters
from ca_biositing.datamodels import UsdaCommodity
from sqlmodel import Session, select

@task
def fetch_nass_commodities(api_key: str):
    """Fetch all NASS commodities and build hierarchy."""
    params = get_available_parameters(api_key)
    # params['commodity_desc'] = ['CORN', 'ALMONDS', 'WHEAT', ...]
    return params['commodity_desc']

@task
def populate_usda_commodity(commodities: list):
    """Insert into usda_commodity table."""
    with Session(engine) as session:
        for commodity_name in commodities:
            # Parse hierarchy (might need USDA API to get parent)
            usda_commodity = UsdaCommodity(
                name=commodity_name,
                usda_source="NASS",
                # ... other fields
            )
            session.add(usda_commodity)
        session.commit()

@flow(name="Bootstrap USDA Commodities")
def bootstrap_flow():
    """One-time setup: populate usda_commodity table."""
    api_key = os.getenv("USDA_NASS_API_KEY")
    commodities = fetch_nass_commodities(api_key)
    populate_usda_commodity(commodities)
```

### Step 2: Operational Flow

```python
# src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py

@task
def get_mapped_commodities():
    """Get list of USDA commodity IDs mapped to our resources."""
    with Session(engine) as session:
        statement = select(ResourceUsdaCommodityMap.usda_commodity_id).distinct()
        result = session.exec(statement).all()
        return result

@task
def extract() -> Optional[pd.DataFrame]:
    """Extract ONLY data for mapped commodities."""
    logger = get_run_logger()

    # Get the commodities we care about
    mapped_ids = get_mapped_commodities()
    if not mapped_ids:
        logger.error("No commodity mappings found. Run bootstrap flow first.")
        return None

    logger.info(f"Extracting data for {len(mapped_ids)} commodities...")

    # API call with filter (pseudocode - update usda_nass_to_pandas.py to support this)
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state="CA",
        commodity_ids=mapped_ids  # Filter at source
    )

    return raw_df
```

---

## Summary: Your Path Forward

1. **Now**: Continue with Option B (filtered query) for initial development
   - Gets you data quickly
   - Lets you test the Transform/Load pipeline

2. **Next**: Prepare for Option C
   - Create bootstrap flow once you have stable commodities
   - Populate `usda_commodity` table
   - Set up manual mappings

3. **Later**: Run with Option C
   - Extract uses database to know which commodities to fetch
   - Easy to add new crops (just SQL, no code)
   - Scalable as you grow

**This is sophisticated, production-ready ETL design. Well done thinking through
this!**
