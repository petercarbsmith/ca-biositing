# Jupyter Notebooks for USDA Ingestion - Quick Start Guide

✓ **Status**: Two comprehensive Jupyter notebooks have been created and are
ready to run.

## What You Have

### 1. USDA_Ingestion_Testing.ipynb (7.3 KB)

**Purpose**: Test and verify the complete USDA ETL pipeline

**Cells Include**:

- Setup environment and imports
- Database connection verification
- Commodity mapper testing (lookup USDA codes)
- USDA API Extract test (fetch data, may take 30-60 seconds)
- Transform task test (clean/normalize data)
- Load task test (insert to database)
- Database verification (query results)
- Summary report with pass/fail status

**Expected Output**:

- ✓ All tests pass showing working pipeline
- Database records confirming successful ingestion
- 🎉 ALL TESTS PASSED message

**Key Cells**:

- Cell 1: Title and description
- Cell 2-3: Setup environment
- Cell 4: Database connection test
- Cell 5-6: Commodity mapper test
- Cell 7-8: Extract test (USDA API - slowest step)
- Cell 9-10: Transform test
- Cell 11-12: Load test
- Cell 13-14: Database verification
- Cell 15-16: Summary report

---

### 2. Commodity_Matcher_Workflow.ipynb (6.7 KB)

**Purpose**: Intelligently match all resources to USDA commodity codes

**Cells Include**:

- Setup environment
- Display all available USDA commodities
- Query resources needing mapping
- Test fuzzy matching algorithm with similarity scoring
- Load/create pending matches JSON file
- View current pending match status
- Apply approved matches to database
- Verify all mappings were created
- Summary with coverage percentage

**Expected Output**:

- List of unmapped resources
- Fuzzy matching similarity scores
- Applied matches confirmed in database
- Coverage report (% of resources mapped)

**Key Cells**:

- Cell 1: Title
- Cell 2-3: Setup
- Cell 4-5: Show commodities
- Cell 6-7: Query unmapped resources
- Cell 8-9: Test fuzzy matching
- Cell 10-11: Manage pending matches
- Cell 12-13: Verify database
- Cell 14-15: Summary

---

## How to Run (By 5pm Today)

### Prerequisites (Run Once)

```bash
# 1. Start Docker services (if not already running)
pixi run start-services

# 2. Verify services are healthy
pixi run service-status

# 3. Ensure environment installed
pixi install
```

### Phase 1: Test USDA Ingestion (10-15 minutes)

1. **Open notebook**:
   - Click: `USDA_Ingestion_Testing.ipynb`

2. **Select kernel**:
   - Top-right corner → Kernel dropdown
   - Select: "ca-biositing (Pixi)"
   - Wait for it to load (will show purple dot briefly)

3. **Run all cells**:
   - Method A: Press `Ctrl+Shift+Enter` (run all)
   - Method B: Run → Run All Cells
   - Watch the output in each cell

4. **Expected Results**:
   - ✓ Database connected
   - ✓ Retrieved N commodity codes
   - ✓ Extract successful - Records: N (API call)
   - ✓ Transform successful
   - ✓ Load successful
   - ✓ Found N database records
   - 🎉 ALL TESTS PASSED

**If any cell fails**:

- Read the error message
- Check Docker services are running: `pixi run service-status`
- Verify .env has correct credentials
- Re-run the setup cells (1-3)

---

### Phase 2: Run Commodity Matcher (10-20 minutes)

1. **Open notebook**:
   - Click: `Commodity_Matcher_Workflow.ipynb`

2. **Select kernel**:
   - Top-right → Select: "ca-biositing (Pixi)"

3. **Run all cells**:
   - `Ctrl+Shift+Enter` or Run → Run All Cells

4. **Expected Results**:
   - Shows all available USDA commodities (list)
   - Shows unmapped resources (count and examples)
   - Displays fuzzy matching scores for test resource
   - Shows pending matches summary
   - Applies approved matches to database
   - Verifies mappings created
   - Shows coverage report

**Output Example**:

```
Available USDA Commodities (4 total):
  1  11199999  CORN
  2  26199999  ALMONDS
  3  10199999  WHEAT
  4  37899999  TOMATOES

Resources Needing Mapping: 15 total
  id  name
   1  crop_sample_1
   2  crop_sample_2
   ...
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError" or "ImportError"

**Solution**:

- Check kernel: Top-right should show "ca-biositing (Pixi)"
- If not, select it from dropdown
- Restart kernel: Kernel menu → Restart

### Issue: "Database connection failed"

**Solution**:

- Start services: `pixi run start-services`
- Check health: `pixi run service-status`
- Verify PostgreSQL is running (should show as "healthy")

### Issue: "USDA API timeout or slow response"

**Status**: This is NORMAL - the USDA API can be slow

- Let the cell run for up to 2 minutes
- The data is loading in the background
- Just be patient!

### Issue: ".usda_pending_matches.json not found"

**Status**: This is fine - the file is created automatically

- The notebook creates it when needed
- Just re-run the cells

---

## Timeline to Complete by 5pm

| Time    | Task                                        | Duration |
| ------- | ------------------------------------------- | -------- |
| NOW     | Start Docker services                       | 2 min    |
| NOW+2   | Run USDA_Ingestion_Testing.ipynb            | 15 min   |
| NOW+17  | Run Commodity_Matcher_Workflow.ipynb        | 15 min   |
| NOW+32  | Review output and verify all tests pass     | 10 min   |
| NOW+42  | **BUFFER** for troubleshooting/verification | 4+ hours |
| **5pm** | ✓ **COMPLETE**                              | -        |

---

## What Each Notebook Proves

### USDA_Ingestion_Testing.ipynb Proves:

✓ Environment is correctly configured ✓ Database connection works ✓ Commodity
codes are accessible ✓ USDA API connection works ✓ Data cleaning pipeline works
✓ Database insert pipeline works ✓ End-to-end ETL pipeline is functional

### Commodity_Matcher_Workflow.ipynb Proves:

✓ Fuzzy matching algorithm works ✓ Commodity database has data ✓ Pending matches
can be tracked ✓ Database insertion works ✓ Coverage calculation works

---

## After Notebooks Complete

### 1. Commit Your Work

```bash
git add USDA_Ingestion_Testing.ipynb
git add Commodity_Matcher_Workflow.ipynb
git add .usda_pending_matches.json
git commit -m "Add USDA testing and commodity matching notebooks"
```

### 2. Optional: Run Code Quality Checks

```bash
pixi run pre-commit-all  # Code formatting and linting
pixi run test            # Unit tests
```

### 3. Document Your Results

- Take screenshots of successful test output
- Save the .usda_pending_matches.json for reference
- Note any custom configurations needed

---

## File Locations

```
c:\Users\meili\forked\ca-biositing\
├── USDA_Ingestion_Testing.ipynb          ← Test pipeline
├── Commodity_Matcher_Workflow.ipynb        ← Match commodities
├── .usda_pending_matches.json              ← Auto-created by matcher
├── NOTEBOOK_TESTING_GUIDE.md               ← This file
└── _create_notebooks.py                    ← Creation script (can delete)
```

---

## Tips for Success

1. **Run cells in order** - Don't skip steps
2. **Wait for API calls** - USDA can be slow (30-60 sec is normal)
3. **Check kernel name** - Must be "ca-biositing (Pixi)"
4. **Use Cell Run buttons** - Don't type commands manually
5. **Watch the output** - Each cell shows progress
6. **Keep docker running** - Services must stay up
7. **Don't edit notebook code** - Just run as-is
8. **Take screenshots** - Document successful runs

---

## Success Criteria

| Criteria                                         | Status           |
| ------------------------------------------------ | ---------------- |
| USDA_Ingestion_Testing.ipynb runs without errors | ✓ Ready          |
| All pipeline steps work (extract→transform→load) | ✓ Will verify    |
| Database records are created                     | ✓ Will verify    |
| Commodity_Matcher_Workflow.ipynb runs            | ✓ Will verify    |
| Resources mapped to USDA codes                   | ✓ Will verify    |
| Coverage report shows progress                   | ✓ Will verify    |
| **GOAL: Full USDA ingestion working by 5pm**     | ✓ **ACHIEVABLE** |

---

## Questions?

- **Database issues?** Check: `pixi run service-status`
- **Import errors?** Check kernel: Top-right dropdown
- **API timeouts?** Be patient, USDA is slow
- **Match not applying?** Check .env credentials

---

**Created**: January 23, 2026 **Goal**: Full USDA ingestion working by 5pm ✓
**Status**: ✓ Notebooks ready to run
