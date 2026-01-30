# Testing USDA ETL Production Code

## Overview

You have production code ready to test, and your database already has data from
the notebook. This guide covers:

1. **Testing approach** (unit → integration → E2E)
2. **Database reset strategies** (what to truncate vs preserve)
3. **Local testing steps** (with pixi)
4. **Success validation**
5. **Rollback on failure**

---

## Part 1: Testing Strategy

### Test Hierarchy

```
┌─────────────────────────────────────────┐
│ E2E Test: Full Flow                     │  (integration with DB)
│  - extract → transform → load           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Integration Tests: Task Level           │  (transform, load with real DB)
│  - transform(raw_data)                  │
│  - load(transformed_data)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Unit Tests: Function Level              │  (mock data, no DB)
│  - _normalize_geoid()                   │
│  - _convert_to_numeric()                │
│  - _build_lookup_maps()                 │
└─────────────────────────────────────────┘
```

### Recommended Testing Order

1. **Unit tests** - Fast, no DB, great for TDD
2. **Integration tests** - With database, real schemas
3. **E2E test** - Full flow with production data

---

## Part 2: Database Reset Strategy

### ⚠️ IMPORTANT: Preserve vs Destroy

**DO NOT** truncate entire tables if you have production data you want to keep!

#### Safe Reset: Only USDA Data

```sql
-- Keep: other data (LandIQ, Analysis, etc.)
-- Delete: Only USDA records and their observations

DELETE FROM observation
WHERE record_type IN ('usda_census_record', 'usda_survey_record');

TRUNCATE TABLE usda_census_record CASCADE;
TRUNCATE TABLE usda_survey_record CASCADE;

-- Reset sequences (so IDs start from 1)
ALTER SEQUENCE usda_census_record_id_seq RESTART WITH 1;
ALTER SEQUENCE usda_survey_record_id_seq RESTART WITH 1;
```

#### Full Reset: Everything (if testing in isolated environment)

```sql
-- Only do this if you have NO production data
TRUNCATE TABLE observation CASCADE;
TRUNCATE TABLE usda_census_record CASCADE;
TRUNCATE TABLE usda_survey_record CASCADE;
TRUNCATE TABLE dataset CASCADE;
TRUNCATE TABLE data_source CASCADE;
TRUNCATE TABLE parameter CASCADE;
TRUNCATE TABLE unit CASCADE;
```

### Database State Checks

Before testing, check what's already loaded:

```sql
SELECT COUNT(*) as usda_records FROM usda_census_record;
SELECT COUNT(*) as survey_records FROM usda_survey_record;
SELECT COUNT(*) as observations FROM observation
  WHERE record_type IN ('usda_census_record', 'usda_survey_record');
SELECT COUNT(*) as datasets FROM dataset WHERE name LIKE 'USDA_%';
```

---

## Part 3: Local Testing WITHOUT Tearing Down Services

### ✅ Recommended: Keep Services Running (Cleaner)

**Why?**

- Faster turnaround (no service startup delay)
- Easier to debug DB state
- Can inspect records between runs
- Just reset data, not infrastructure

### Step-by-Step Local Testing

#### Step 0: Ensure Services Are Running

```bash
pixi run service-status
```

Should show:

```
✓ postgres (running)
✓ prefect (running)
```

If not running:

```bash
pixi run start-services
```

#### Step 1: Reset USDA Data (First Run Only)

In VS Code terminal with PostgreSQL client:

```bash
# Connect to database
psql postgresql://user:password@localhost:5432/ca_biositing

# Run reset SQL (copy from "Safe Reset" section above)
DELETE FROM observation WHERE record_type IN ('usda_census_record', 'usda_survey_record');
TRUNCATE TABLE usda_census_record CASCADE;
TRUNCATE TABLE usda_survey_record CASCADE;
TRUNCATE TABLE dataset CASCADE WHERE name LIKE 'USDA_%';

\q  # Exit psql
```

#### Step 2: Run Unit Tests (Optional but Recommended)

```bash
pixi run pytest src/ca_biositing/pipeline/tests/test_usda_transform.py -v
pixi run pytest src/ca_biositing/pipeline/tests/test_usda_load.py -v
```

#### Step 3: Run Flow Locally

```bash
# Option A: Run directly
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# Option B: Run with Prefect (recommended - can see in UI)
pixi run prefect deployment build src/ca_biositing/pipeline/flows/usda_etl.py:usda_etl_flow \
  -n "USDA ETL Local" \
  -q default

pixi run prefect deployment run "USDA ETL Local/default"
```

#### Step 4: Validate Success

Check logs:

```bash
pixi run service-logs  # Check Prefect logs
```

Query database to verify:

```sql
SELECT COUNT(*) FROM usda_census_record;        -- Should be > 0
SELECT COUNT(*) FROM usda_survey_record;        -- Should be > 0
SELECT COUNT(*) FROM observation
  WHERE record_type IN ('usda_census_record', 'usda_survey_record');  -- Should be > 0

SELECT COUNT(DISTINCT etl_run_id) FROM observation
  WHERE record_type = 'usda_census_record';  -- Should track runs
```

---

## Part 4: Local Testing WITH Service Teardown (if Needed)

### When to Use This Approach

- Database corruption suspected
- Need completely clean state
- Docker networking issues
- Full integration test

### Step-by-Step with Teardown

```bash
# 1. Stop all services (kills containers, keeps volumes)
pixi run docker compose down

# 2. Remove USDA data volumes (CAREFUL - deletes data!)
# (Optional - only if you want fresh database)
pixi run docker compose down -v

# 3. Rebuild services with fresh state
pixi run docker compose up -d

# 4. Wait for postgres to be ready
sleep 10

# 5. Run migrations to recreate schema
pixi run migrate

# 6. Now run the ETL flow
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
```

---

## Part 5: Success Validation Checklist

### ✅ Complete Validation Script

Create file: `validate_usda_load.sql`

```sql
-- USDA ETL Validation Script
-- Run after ETL completes

\echo '=== USDA ETL Validation ==='

\echo ''
\echo '1. COUNT RECORDS BY TYPE'
SELECT
  'usda_census_record' as type,
  COUNT(*) as count
FROM usda_census_record
UNION ALL
SELECT
  'usda_survey_record' as type,
  COUNT(*) as count
FROM usda_survey_record;

\echo ''
\echo '2. VERIFY DATASET LINKAGE'
SELECT
  'Census records with dataset_id' as check_name,
  COUNT(*) as total,
  COUNT(dataset_id) as with_dataset_id,
  ROUND(100.0 * COUNT(dataset_id) / COUNT(*), 1) as percent
FROM usda_census_record
UNION ALL
SELECT
  'Survey records with dataset_id',
  COUNT(*),
  COUNT(dataset_id),
  ROUND(100.0 * COUNT(dataset_id) / COUNT(*), 1)
FROM usda_survey_record;

\echo ''
\echo '3. VERIFY OBSERVATION LINKAGE'
SELECT
  'Observations with valid parent records' as check_name,
  COUNT(*) as total,
  SUM(CASE
    WHEN record_type = 'usda_census_record'
    AND EXISTS (SELECT 1 FROM usda_census_record c WHERE c.id = observation.record_id::integer)
    THEN 1
    WHEN record_type = 'usda_survey_record'
    AND EXISTS (SELECT 1 FROM usda_survey_record s WHERE s.id = observation.record_id::integer)
    THEN 1
    ELSE 0
  END) as valid_parents
FROM observation
WHERE record_type IN ('usda_census_record', 'usda_survey_record');

\echo ''
\echo '4. VERIFY ETLS AND LINEAGE'
SELECT
  COUNT(DISTINCT etl_run_id) as distinct_etl_runs,
  COUNT(DISTINCT lineage_group_id) as distinct_lineage_groups,
  MIN(created_at) as earliest_record,
  MAX(created_at) as latest_record
FROM observation
WHERE record_type IN ('usda_census_record', 'usda_survey_record');

\echo ''
\echo '5. SAMPLE RECORDS'
\echo 'Census Record Sample:'
SELECT
  id, geoid, year, commodity_code, dataset_id, created_at
FROM usda_census_record
LIMIT 3;

\echo ''
\echo 'Observation Sample:'
SELECT
  id, record_id, record_type, parameter_id, unit_id, value, created_at
FROM observation
WHERE record_type = 'usda_census_record'
LIMIT 3;

\echo ''
\echo '=== VALIDATION COMPLETE ==='
```

Run validation:

```bash
psql postgresql://user:password@localhost:5432/ca_biositing -f validate_usda_load.sql
```

---

## Part 6: Rollback on Failure

### If ETL Partially Loads

The code has **3-level deduplication**, so it's idempotent:

- **Level 1**: Existing DB check (skips if key exists)
- **Level 2**: Batch tracking (skips if seen in current load)
- **Level 3**: PostgreSQL ON CONFLICT (catches duplicates at insert)

**This means:**

- ✅ Safe to re-run after failure
- ✅ No duplicate keys will be inserted
- ✅ Partial load won't corrupt data

### If Data IS Corrupted

#### Option 1: Rollback to Before ETL Run

```bash
# Using git (if committed before running)
git log --oneline  # Find commit before ETL
git revert <commit-hash>  # Revert changes

# Using database backup
# (depends on your backup strategy)
```

#### Option 2: Manual Cleanup (Nuclear Option)

```sql
-- Delete USDA data from last failed run
DELETE FROM observation
WHERE record_type IN ('usda_census_record', 'usda_survey_record')
AND created_at > '2026-01-29 12:00:00'::timestamp;  -- Adjust time

DELETE FROM usda_census_record
WHERE created_at > '2026-01-29 12:00:00'::timestamp;

DELETE FROM usda_survey_record
WHERE created_at > '2026-01-29 12:00:00'::timestamp;
```

#### Option 3: Full USDA Reset

```bash
# Reset to clean USDA state (keeps everything else)
# Use "Safe Reset" SQL from Part 2 above

# Then re-run ETL
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl
```

---

## Part 7: Testing Checklist

### Before First Run

- [ ] Services running: `pixi run service-status`
- [ ] Database accessible: can query tables
- [ ] Note current record counts from validation script
- [ ] Review extract source (GCP credentials)

### During Run

- [ ] Check logs for errors: `pixi run service-logs`
- [ ] Monitor Prefect UI for task progress
- [ ] Watch for deduplication logging (Level 1, 2, 3)

### After Run

- [ ] Run validation script
- [ ] Compare counts before/after
- [ ] Verify dataset_id = 100% linked
- [ ] Verify foreign keys valid
- [ ] Sample records in Data Wrangler

### Expected Outcomes

- [ ] Census records > 0
- [ ] Survey records > 0
- [ ] Observations > 0
- [ ] 100% of records have dataset_id
- [ ] 100% of observations have valid parent
- [ ] etl_run_id tracked
- [ ] lineage_group_id tracked
- [ ] No duplicates (dedup Level 3 skipped none)

---

## Part 8: Common Issues & Fixes

### Issue 1: "Database connection refused"

```bash
# Check if Postgres is running
pixi run service-status

# If not, start it
pixi run start-services

# If still failing, check Postgres logs
pixi run service-logs | grep postgres
```

### Issue 2: "Lazy import error: can't find ca_biositing.datamodels"

```bash
# PYTHONPATH issue - use Pixi to run
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# NOT: python src/ca_biositing/pipeline/flows/usda_etl.py
```

### Issue 3: "No raw data to transform"

- Check that extract() is fetching from USDA API
- Verify GCP credentials.json exists in root
- Check network connectivity to USDA API

### Issue 4: "All records dropped - no required fields"

- Check if commodity mapping is working
- Verify parameter/unit records created
- Check if value conversion to numeric failing
- Look at debug output in logs

### Issue 5: "Foreign key violation"

- Likely parent record missing (should not happen with dedup)
- Check dataset_map is populated
- Verify census/survey records created before observations

---

## Part 9: Recommended Testing Workflow

### First Time

```bash
# 1. Reset database to clean state
# (use "Safe Reset" SQL)

# 2. Run unit tests
pixi run pytest src/ca_biositing/pipeline/tests/test_usda_*.py -v

# 3. Run flow locally
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# 4. Validate with script
psql -f validate_usda_load.sql

# 5. Inspect in Data Wrangler if needed
# (manually open USDA tables)
```

### Subsequent Runs (After Fixes)

```bash
# 1. Decide: reset or keep?
# - If keeping: dedup will prevent duplicates
# - If resetting: use "Safe Reset" SQL

# 2. Run flow
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl

# 3. Quick validation
psql -c "SELECT COUNT(*) FROM usda_census_record;"
psql -c "SELECT COUNT(*) FROM observation WHERE record_type = 'usda_census_record';"
```

---

## Part 10: NO - Don't Always Teardown

### Summary

| Scenario               | Action                                   | Why                       |
| ---------------------- | ---------------------------------------- | ------------------------- |
| **First test run**     | Reset data only (safe reset SQL)         | Don't need full restart   |
| **Bug fix, retry**     | Keep services, reset data if needed      | Faster iteration          |
| **Services crashed**   | Restart: `docker compose up -d`          | But keep data             |
| **Database corrupted** | Full teardown + `docker compose down -v` | Last resort               |
| **Production deploy**  | Never teardown                           | Use migrations for schema |

**Recommendation: Keep services running, just reset data between test runs.**

```bash
# What you'll do 90% of the time:
psql -f reset_usda_data.sql    # Reset data
pixi run python -m src.ca_biositing.pipeline.flows.usda_etl  # Run test
```
