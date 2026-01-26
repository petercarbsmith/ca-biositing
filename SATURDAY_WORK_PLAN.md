# Saturday & Monday Work Plan - USDA Data into Database

**Goal**: All USDA data (3 counties) in database by Tuesday 2pm PT **Time
Available**: ~2 hours Saturday, ~2 hours Monday, ~30 min today ✓

---

## Status: Extract (100% Ready)

Template in notebook is **production-ready** with:

- ✅ All 3 priority counties configured
- ✅ Proper 5-digit FIPS codes (06077, 06099, 06047)
- ✅ 4 statistics types (YIELD default, + PRODUCTION, AREA HARVESTED, PRICE
  RECEIVED)
- ✅ Commodity mapping from database
- ✅ Error handling with retries
- ✅ 8-column output schema ready for transform

### About Stanislaus Timeout

**Why it times out:**

- Stanislaus has large agricultural dataset (~3,000+ records per statistic)
- NASS API returns all records in one response
- 30-second default timeout sometimes too short

**Solutions (try in order):**

1. Increase retry attempts: Change `max_retries = 5` (instead of 3)
2. Increase timeout: Change `timeout=60` instead of 30
3. Query separately: Comment out Stanislaus while testing other 2 counties

---

## Saturday Work (2 hours)

### Phase 1: Test Extract (30 min)

**In notebook - "Production-Ready API Template" cell:**

```python
# 1. Run template with just San Joaquin and Merced first
COUNTIES_TO_QUERY = {
    'San Joaquin': {'fips': '06077', 'nass_code': '077'},
    'Merced': {'fips': '06047', 'nass_code': '047'},
}
SELECTED_STATISTICS = ['YIELD']  # Just one stat for testing
# Run cell, verify output_df has 8 columns and proper FIPS codes

# 2. Once that works, add Stanislaus with increased timeout
COUNTIES_TO_QUERY = {
    'San Joaquin': {'fips': '06077', 'nass_code': '077'},
    'Stanislaus': {'fips': '06099', 'nass_code': '099'},  # Add back
    'Merced': {'fips': '06047', 'nass_code': '047'},
}
max_retries = 5  # Increase
timeout = 60     # Increase
# Run cell again - should get all 3 counties
```

**Success criteria:**

- ✓ output_df has all records from 3 counties
- ✓ FIPS codes are 5 digits (06077, 06099, 06047)
- ✓ No timeout errors (or resolved with retry)

### Phase 2: Inspect Extract Output (30 min)

**In notebook - debug cell:**

```python
# Run the DataFrame inspection cell after successful extract
# Should see:
# - Total records (~8,000-10,000 for 3 counties)
# - 8 columns: commodity, year, county, fips, statistic, unit, observation, description
# - No null values in key columns
```

### Phase 3: Research Transform (1 hour)

**Read the transform function:**

```python
# Check: src/ca_biositing/pipeline/etl/transform/usda/usda_census_survey.py
# Questions to answer:
# 1. What input columns does it expect?
# 2. What does it do to the data?
# 3. What output columns does it produce?
# 4. Any data validation it performs?
```

**Document findings in a comment or note** for Monday work

---

## Monday Work (2 hours)

### Phase 1: Create Transform Task (45 min)

- Use template output_df as input
- Reshape to match expected transform input
- Run transform function
- Inspect results (output should have: geoid, commodity_code, year, observation)

### Phase 2: Create Load Task (45 min)

- Take transformed data
- Create ORM objects (UsdaCensusRecord)
- Insert into database
- Query to verify records exist with proper timestamps

### Phase 3: End-to-End Test (30 min)

- Extract all 3 counties with all 4 statistics
- Transform data
- Load to database
- Verify data integrity

---

## Quick Reference

### File Locations

- **Extract Template**: `USDA_Ingestion_Testing.ipynb` → "Production-Ready API
  Template" section
- **Transform Code**:
  `src/ca_biositing/pipeline/etl/transform/usda/usda_census_survey.py`
- **Load Code**: `src/ca_biositing/pipeline/etl/load/usda/usda_census_survey.py`
- **Database Models**: Models define UsdaCensusRecord (timestamps
  auto-generated)

### Output Schema (Extract)

```
commodity   │ year │ county      │ fips  │ statistic        │ unit    │ observation │ description
CORN        │ 2022 │ San Joaquin │ 06077 │ YIELD            │ TONS    │ 42.5        │ YIELD in TONS
```

### Expected Transform Output

```
geoid   │ commodity_code │ year │ observation
06077   │ 26            │ 2022 │ 42.5
```

### Expected Load Behavior

- Records inserted into `usda_census_record` table
- `created_at` and `updated_at` auto-populated by database
- Query confirmation: `SELECT COUNT(*) FROM usda_census_record WHERE year=2022;`

---

## Troubleshooting Quick Links

| Issue               | Solution                                            |
| ------------------- | --------------------------------------------------- |
| Stanislaus timeout  | Increase `max_retries` to 5, `timeout` to 60        |
| No records returned | Check API key, verify county codes, check year data |
| Transform fails     | Check input column names match output schema        |
| Load fails          | Check database connection, verify table exists      |

---

## Notes for Continuity

**Why this approach works:**

1. Extract only - validate data shape and content
2. Transform - understand schema changes
3. Load - ensure database insertion works
4. Full flow - test end-to-end before production

**Timeline realistic?**

- Saturday extraction: ~2 hours ✓ (mostly waiting for API)
- Monday transform+load: ~2 hours ✓ (main coding work)
- Monday buffer: 30 min for debugging
- **Should complete by Monday evening** before Tuesday meeting

**If stuck on transform/load:**

- Reference existing patterns in codebase
- Check existing load function for UsdaCensusRecord
- Template is proven extract - focus on connection between
  extract→transform→load

---

**Good luck! 💪 See you Saturday!**

---

## BONUS: Enhanced Commodity Mapper (For After Tuesday)

**New script created**: `enhanced_commodity_mapper.py`

This implements your vision for commodity mapping:

1. **Fetch all CA USDA commodities** from NASS API (not just hardcoded list)
2. **Auto-match clear matches** (>90% similarity) automatically
3. **Interactive review** presents 1-5 fuzzy match candidates for you to select
4. **Leave empty if no match** - no forced mappings
5. **Save to database** with proper match_tier tracking

### Workflow (run after Tuesday meeting):

```bash
# Step 1: Fetch all California commodities (run once)
python enhanced_commodity_mapper.py --fetch-ca-commodities

# Step 2: Auto-match the obvious ones (>90% similarity)
python enhanced_commodity_mapper.py --auto-match

# Step 3: Interactively review fuzzy matches (60-90%)
python enhanced_commodity_mapper.py --review
# You'll see:
#   [1] Resource: 'Alfalfa' (primary_ag_product)
#       [1] HAY ALFALFA (code: 18199999) - 95% match
#       [2] ALFALFA SEED (code: 18299999) - 75% match
#       [3] HAY (code: 18199999) - 60% match
#       [n] No good match
#   Your selection (1-3, n, or q): 1
#   ✓ Matched: Alfalfa → HAY ALFALFA

# Step 4: Save approved mappings to database
python enhanced_commodity_mapper.py --save

# Or run entire workflow at once:
python enhanced_commodity_mapper.py --full-workflow
```

### Benefits:

- Uses live NASS API data (not hardcoded list)
- Interactive so you control quality
- Creates `resource_usda_commodity_map` entries automatically
- Tracks match quality (AUTO_MATCH vs USER_APPROVED)
- Can re-run safely (checks for existing mappings)

### Reference:

USDA Commodity Codes:
https://www.nass.usda.gov/Data_and_Statistics/County_Data_Files/Frequently_Asked_Questions/commcodes.php

**Timeline for mapping**:

- 30 min: Fetch commodities + auto-match
- 1-2 hours: Interactive review (depends on # of resources)
- Total: ~2-3 hours for complete commodity mapping

**Do this AFTER Tuesday meeting** when you have time to review matches
carefully!
