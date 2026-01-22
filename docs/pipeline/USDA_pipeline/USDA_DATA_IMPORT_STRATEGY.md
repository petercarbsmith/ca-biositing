# USDA Data Import Strategy: Full Data vs. Filtered Approach

## Your Question Summarized

Should you:

- **Option A**: Import ALL USDA data into your database, then filter during
  Transform?
- **Option B**: Filter at API query time, importing only data that matches your
  known resources/primary_ag_products?
- **Option C**: Hybrid approach - import commodity ontology first, then query
  strategically?

**My Recommendation: Option C (Hybrid) is best for your use case.**

Let me explain why, using your schema as evidence.

---

## Understanding Your Data Model

From your schema, you have three key tables in the "Resource Ontology Mapping"
group:

### 1. `usda_commodity` (Lookup Table - USDA's Hierarchy)

```
id | name          | usda_source | usda_code | parent_commodity_id
---|---------------|-------------|-----------|--------------------
1  | ALMONDS       | NASS        | 16020     | NULL
2  | TREE NUTS     | NASS        | 16000     | NULL
3  | ALMOND HULLS  | AMS         | 16025     | 1 (parent: ALMONDS)
```

**Purpose**: This is USDA's official commodity hierarchy. Your team's notes say:

> "Programmatically populate this table using NASS 'Group' → 'Commodity' →
> 'Class' hierarchy"

### 2. `resource_usda_commodity_map` (Bridge Table - Your Mapping)

```
id | resource_id | primary_ag_product_id | usda_commodity_id | match_tier
---|-------------|----------------------|-------------------|--------------------
1  | 5           | 3                    | 1                 | DIRECT_MATCH
2  | NULL        | 4                    | 2                 | AGGREGATE_PARENT
```

**Purpose**: Links YOUR system (resources, primary_ag_products) to USDA
commodities. **Key insight**: You can link by either `resource_id` OR
`primary_ag_product_id` (or both for different match tiers).

### 3. `usda_census_record` / `usda_survey_record` (Data Tables)

```
id | geoid | commodity_code | year | value | ... (references usda_commodity)
---|-------|----------------|------|-------|-----
1  | 06001 | 1              | 2023 | 5000  | (ALMONDS in 2023)
2  | 06002 | 3              | 2023 | 1200  | (ALMOND HULLS in 2023)
```

**Purpose**: Stores actual USDA measurements. The `commodity_code` links back to
`usda_commodity`.

---

## Trade-Offs Analysis

### Option A: Import ALL Data (Lazy Filtering)

**Flow**: Extract ALL NASS/Survey data → Transform (filter to mapped
commodities) → Load

**Pros:**

- ✅ Future-proof: If you add new crops later, data already exists
- ✅ Discovery: See what other crops are available for your regions
- ✅ Simpler initial logic: Extract function is dumb

**Cons:**

- ❌ **Database bloat**: USDA has 10,000+ commodity combinations. CA data alone
  could be 100K+ rows per year
- ❌ **Slow API calls**: 50,000 record limit means multiple requests even for CA
- ❌ **Transform complexity**: Need to join against
  `resource_usda_commodity_map` for every record
- ❌ **Schema integrity**: If you haven't created mappings yet, orphaned records
  in `usda_census_record`
- ❌ **Wasted storage**: Paying for database space for commodities you don't
  care about

**When to use**: Small datasets, exploratory analysis, you have unlimited
storage budget

---

### Option B: Query with Filters (Early Filtering)

**Flow**: Get list of mapped commodities → Extract ONLY those from API →
Transform → Load

**Pros:**

- ✅ **Clean database**: Only store what you care about
- ✅ **Fast API calls**: Much fewer records to download
- ✅ **Simpler load**: No orphaned records

**Cons:**

- ❌ **Bootstrap problem**: Can't filter until mappings exist!
- ❌ **Brittle**: Adding new crops requires code changes (new query, rerun)
- ❌ **Discovery limited**: Miss interesting data you didn't anticipate
- ❌ **Coupling**: Extract logic depends on database state (mappings table)

**When to use**: You have pre-built mappings, stable crop list, storage is
expensive

---

### Option C: Hybrid (Recommended) ⭐

**Two-phase approach:**

**Phase 1: Bootstrap (One-time, Manual Setup)**

1. Create a temporary ETL flow to import ALL USDA commodities into
   `usda_commodity` table
   - Uses NASS API's parameter endpoint to get commodity hierarchy
   - Stores in `usda_commodity` with `usda_source='NASS'`
2. Team manually creates mappings in `resource_usda_commodity_map`
   - Link "ALMONDS" (USDA) → "Almond" (primary_ag_product)
   - Link "CORN" (USDA) → "Corn" (primary_ag_product)
   - Set `match_tier` appropriately (DIRECT_MATCH, AGGREGATE_PARENT, etc.)

**Phase 2: Operational (Runs repeatedly)**

1. Extract: Query API with filter
   `commodity_code IN (list from resource_usda_commodity_map)`
2. Transform: Filter + clean data
3. Load: Insert into `usda_census_record` / `usda_survey_record`

---

## Your Current Schema Already Supports This!

Looking at your `resource_usda_commodity_map`:

```python
class ResourceUsdaCommodityMap(BaseEntity):
    resource_id = Column(Integer(), ForeignKey('resource.id'))          # Optional
    primary_ag_product_id = Column(Integer(), ForeignKey('primary_ag_product.id'))  # Optional
    usda_commodity_id = Column(Integer(), ForeignKey('usda_commodity.id'))  # Required
    match_tier = Column(Text())  # DIRECT_MATCH, CROP_FALLBACK, AGGREGATE_PARENT
    note = Column(Text())
```

**This design is perfect for Option C because:**

- ✅ You can link to either specific resources OR general crops (flexibility)
- ✅ `match_tier` lets you handle hierarchical matches (almonds → tree nuts)
- ✅ All the building blocks are there; you just need to populate them

---

## Recommended Implementation Steps

### Step 1: Bootstrap USDA Commodities (Do Once)

Create a new flow: `bootstrap_usda_commodities.py`

```python
# This runs ONCE to populate usda_commodity lookup table
@flow
def bootstrap_usda_commodities():
    """
    Download USDA commodity hierarchy and populate usda_commodity table.
    Must run before any other USDA data imports.
    """
    # Query: https://quickstats.nass.usda.gov/api/get_param_values?key=API_KEY&param=commodity_desc
    # This returns list of ALL commodities NASS tracks (Group → Commodity hierarchy)

    # Build hierarchy in memory
    # Insert into usda_commodity with usda_source='NASS'

    # Also query AMS later (market data) and insert with usda_source='AMS'
    pass
```

**Why separate?**

- Runs independently from regular data pipeline
- Can be re-run if USDA adds new commodities
- Doesn't interfere with operational flows

### Step 2: Manual Mapping (Your Team)

In your application (or SQL), manually create entries in
`resource_usda_commodity_map`:

```sql
-- Example mappings
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id, usda_commodity_id, match_tier, note)
VALUES
  (3, 1, 'DIRECT_MATCH', 'Almond = Almond'),
  (4, 2, 'AGGREGATE_PARENT', 'Corn includes all corn varieties'),
  (5, 15, 'CROP_FALLBACK', 'Wheat when specific variety not available');
```

**Key point**: Do this ONCE per crop. Then operational flows use these mappings.

### Step 3: Operational Flow (Runs Regularly)

```python
@flow
def usda_census_survey_flow():
    """Regular data import."""
    # Step 1: Get list of USDA commodities we care about
    mapped_commodities = get_mapped_commodities_from_db()
    # SELECT usda_commodity_id FROM resource_usda_commodity_map

    # Step 2: Extract ONLY those commodities
    df = extract_usda_data(
        api_key=USDA_API_KEY,
        state="CA",
        commodities=mapped_commodities
    )

    # Step 3: Transform as usual
    df_transformed = transform(df)

    # Step 4: Load
    load(df_transformed)
```

---

## Implementation for Your Extract Function

Here's how to update your `usda_census_survey.py`:

```python
def extract() -> Optional[pd.DataFrame]:
    """
    Extracts USDA data, but ONLY for commodities mapped in resource_usda_commodity_map.

    This prevents downloading irrelevant data while keeping the option to add new
    commodities later by updating mappings in the database.
    """
    logger = get_run_logger()

    # Get the list of USDA commodity IDs we care about
    # This queries the database for all commodities linked to our resources
    mapped_commodity_ids = get_mapped_commodity_ids()

    if not mapped_commodity_ids:
        logger.warning(
            "No commodity mappings found in resource_usda_commodity_map. "
            "Please populate this table first (bootstrap_usda_commodities flow)."
        )
        return None

    logger.info(f"Extracting data for {len(mapped_commodity_ids)} mapped commodities...")

    # Extract only the commodities we care about
    raw_df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        state="CA",
        commodities=mapped_commodity_ids  # Pass list of IDs to filter
    )

    if raw_df is None:
        logger.error("Failed to extract USDA data.")
        return None

    logger.info(f"Successfully extracted {len(raw_df)} records.")
    return raw_df
```

Helper function (add to utils):

```python
def get_mapped_commodity_ids() -> List[int]:
    """
    Returns list of USDA commodity IDs that are mapped to our resources.
    """
    from sqlalchemy import select
    from sqlmodel import Session
    from ca_biositing.datamodels import ResourceUsdaCommodityMap

    with Session(engine) as session:
        statement = select(
            ResourceUsdaCommodityMap.usda_commodity_id
        ).distinct()
        result = session.exec(statement).all()
        return result
```

---

## Why This Solves Your Confusion

Your confusion came from this valid worry:

> "Does logic live in the code or the database?"

**Answer**: Both, but at different times:

1. **Setup-time logic** (code): Bootstrap script that populates USDA commodity
   hierarchy
2. **Database state** (schema): `resource_usda_commodity_map` stores YOUR
   business logic (which commodities matter)
3. **Operational logic** (code): Extract uses database state to filter API
   queries

This is the **proper separation of concerns**:

- Code: HOW to talk to USDA API
- Database: WHAT commodities you care about
- Extract: Reads database to decide WHICH data to fetch

---

## Suggested Tweaks to Your Plan

| Your Idea                           | My Suggestion                                | Why                    |
| ----------------------------------- | -------------------------------------------- | ---------------------- |
| "Import all data as a df"           | Import strategically using mappings          | Avoids DB bloat        |
| "Transform step handles filtering"  | Transform should enrich/validate, not filter | Separation of concerns |
| "Pass list of commodities to query" | ✅ YES, exactly this                         | Right approach         |
| "Do this pre-ingestion"             | ✅ YES, bootstrap phase                      | Smart move             |

---

## Quick Checklist: What You Need to Do

- [ ] **Phase 1 (Setup - Once)**
  - [ ] Create `bootstrap_usda_commodities.py` flow
  - [ ] Populate `usda_commodity` table with NASS hierarchy
  - [ ] Manually create mappings in `resource_usda_commodity_map`

- [ ] **Phase 2 (Operational - Repeating)**
  - [ ] Update `usda_census_survey.py` extract to query
        `resource_usda_commodity_map`
  - [ ] Update `usda_nass_to_pandas.py` to accept commodity list filter
  - [ ] Test with mapped commodities

- [ ] **Later (Expansion)**
  - [ ] Add new crops by updating `resource_usda_commodity_map` (no code
        changes!)
  - [ ] Periodically add new AMS market data via similar approach

---

## Final Thoughts

Your instinct was correct: **"logic pre-ingestion lives in the database, not
confusion."**

This is sophisticated ETL design—using your database schema to control what data
flows through the pipeline. It's much better than hardcoding commodity lists in
Python!

You're thinking like a data architect. This approach will scale well as your
bioeconomy data grows.
