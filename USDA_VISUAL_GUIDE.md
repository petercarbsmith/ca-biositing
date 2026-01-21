# Visual Guide: Your USDA Pipeline Questions Answered

## Your Three Questions in One Page

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Q1: Can I use commodity NAMES instead of numeric IDs?            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌──────────────────────────┐    ┌──────────────────────────┐
│  Names (Recommended)     │    │   IDs (Not Recommended)  │
├──────────────────────────┤    ├──────────────────────────┤
│ "ALMONDS"                │    │ 12010                    │
│ "CORN"                   │    │ 11000                    │
│ "WHEAT"                  │    │ 11000                    │
│                          │    │                          │
│ ✅ Human readable        │    │ ❌ What does 12010 mean? │
│ ✅ Matches USDA API      │    │ ❌ Requires lookup table │
│ ✅ Easy to debug         │    │ ❌ More confusing logs   │
│ ✅ Scalable              │    │ ❌ Extra conversions     │
└──────────────────────────┘    └──────────────────────────┘

Answer: YES! Use names throughout.

See: USDA_NAMES_QUICK_REFERENCE.md
     ↳ Complete working code examples


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Q2: Where does filtering logic live—code or database?            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Three Options Analyzed:

┌─────────────────────────────┐
│ Option A: Import ALL Data   │
├─────────────────────────────┤
│ ✓ Simple code               │
│ ✗ Slow (big queries)        │
│ ✗ Can't scale to all USA    │
│ ✗ Wastes storage            │
│                             │
│ "Download everything,       │
│  filter later"              │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Option B: Filter in Code    │
├─────────────────────────────┤
│ ✓ Controlled                │
│ ✗ Must change code to add   │
│   new crops                 │
│ ✗ Business logic in code    │
│ ✗ Won't scale as you grow   │
│                             │
│ "Hardcode commodity list    │
│  in Python file"            │
└─────────────────────────────┘

┌────────────────────────────────────┐
│ Option C: Filter in Database ⭐    │
├────────────────────────────────────┤
│ ✅ Add crops without code changes  │
│ ✅ Business logic in database      │
│ ✅ Scales as you grow              │
│ ✅ Maintainable for non-engineers  │
│                                    │
│ "Database tells code which         │
│  commodities to fetch"             │
└────────────────────────────────────┘

Answer: Option C (Database-driven filtering)

Why:
  • Your team can add crops by updating the database
  • No code changes needed
  • Scales from 3 commodities to 50 without touching code
  • Business users can maintain it

See: USDA_DATA_IMPORT_STRATEGY.md
     ↳ Full analysis of all three options
     ↳ Schema diagrams and tradeoffs


┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Q3: Why 5 weeks instead of 6-7 hours?                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

BOTH ARE VALID! Choose your speed:

┌────────────────────────┬──────────────┬──────────────┬──────────────┐
│ Factor                 │ 1-Day        │ 2-3 Days ⭐  │ 5-Weeks      │
├────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Total Effort           │ 6-7 hours    │ 4-5 hours    │ 4-6 hours    │
│ Timeline               │ 1 day        │ 3 days       │ 5-8 weeks    │
│ Per-day workload       │ 6-7 hrs      │ 1-2 hrs/day  │ ~30 min/week │
│ Code Reviews           │ Few          │ Multiple     │ Many         │
│ Best For               │ Blocked time │ Most teams   │ Slow onboard │
│ Risk Level             │ Medium       │ Low ⭐       │ Very low     │
│ Recommendation         │ If focused   │ Recommended  │ If relaxed   │
└────────────────────────┴──────────────┴──────────────┴──────────────┘

What was 5 weeks?
  → Conservative estimate assuming slower reviews, team learning curve
  → Good if you have less DevOps experience in your team
  → Allows time for questions and explanations

Why can it be 6-7 hours?
  → Code is straightforward (not complex)
  → If you have clear blocked time
  → With experienced developer doing all work at once

Why 2-3 days is recommended?
  → Good balance: faster than 5 weeks, less intense than 1 day
  → Spreads work across days for sanity
  → Allows code review and integration testing between phases
  → Time for team to understand what's happening

Answer: Choose the timeline that fits your situation

See: USDA_BOOTSTRAP_CLARIFICATIONS.md
     ↳ Hour-by-hour breakdown for each option
     ↳ Prerequisites for each speed
```

---

## The Complete Workflow (Name-Based, Database-Driven)

```
╔════════════════════════════════════════════════════════════════╗
║                    PHASE 1: BOOTSTRAP (Once)                  ║
╚════════════════════════════════════════════════════════════════╝

Step 1: Your team decides which commodities matter
┌────────────────────────────────────────────┐
│ COMMODITIES_TO_ADD = [                     │
│   "ALMONDS",                               │
│   "CORN",                                  │
│   "WHEAT",                                 │
│ ]                                          │
└────────────────────────────────────────────┘
              ↓
Step 2: Bootstrap flow adds to usda_commodity table
┌────────────────────────────────────────────┐
│ usda_commodity:                            │
│ id | name     | usda_source                │
│ 1  | ALMONDS  | NASS                       │
│ 2  | CORN     | NASS                       │
│ 3  | WHEAT    | NASS                       │
└────────────────────────────────────────────┘
              ↓
Step 3: Team creates resource mappings (SQL or app)
┌────────────────────────────────────────────┐
│ resource_usda_commodity_map:               │
│ pap_id | usda_id | match_tier              │
│ 1      | 1       | DIRECT_MATCH (Almond→AL│
│ 2      | 2       | DIRECT_MATCH (Corn→COR)│
└────────────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════╗
║              PHASE 2: OPERATIONAL (Every ETL Run)              ║
╚════════════════════════════════════════════════════════════════╝

Step 1: Extract queries database for commodity NAMES
┌────────────────────────────────────────────┐
│ commodity_mapper.get_mapped_commodity_names()
│ Returns: ["ALMONDS", "CORN", "WHEAT"]     │
└────────────────────────────────────────────┘
              ↓
Step 2: Extract calls USDA API with NAMES
┌────────────────────────────────────────────┐
│ usda_nass_to_df(                           │
│   api_key="xxx",                           │
│   state="CA",                              │
│   commodity_names=["ALMONDS", "CORN"]      │
│ )                                          │
│                                            │
│ API calls:                                 │
│ GET ?commodity_desc=ALMONDS&state=CA      │
│ GET ?commodity_desc=CORN&state=CA         │
└────────────────────────────────────────────┘
              ↓
Step 3: Load into database
┌────────────────────────────────────────────┐
│ usda_survey_record:                        │
│ id | commodity_desc | state | value | year │
│ 1  | ALMONDS        | CA    | 5000  | 2023 │
│ 2  | CORN           | CA    | 10000 | 2023 │
│ 3  | ALMONDS        | CA    | 5100  | 2024 │
└────────────────────────────────────────────┘
              ↓
Step 4: Transform and match resources
┌────────────────────────────────────────────┐
│ Final result linked to primary_ag_product: │
│ "Almond" resource → 5000, 5100 values      │
│ "Corn" resource → 10000 values             │
└────────────────────────────────────────────┘
```

---

## Code: The Core Functions

```python
# 1. GET COMMODITY NAMES FROM DATABASE
def get_mapped_commodity_names() -> List[str]:
    """What commodities does our team care about?"""
    # Returns: ["ALMONDS", "CORN", "WHEAT"]
    #
    # Query: SELECT DISTINCT name FROM usda_commodity
    #        WHERE id IN (SELECT DISTINCT usda_commodity_id
    #                     FROM resource_usda_commodity_map)


# 2. QUERY USDA API WITH NAMES
def usda_nass_to_df(
    api_key: str,
    commodity_names: List[str] = None,  # ← Names!
    state: str = "CA",
    **kwargs
) -> pd.DataFrame:
    """Fetch data for commodity NAMES"""
    # For each name, call:
    # GET https://quickstats.nass.usda.gov/api/api_GET
    #     ?commodity_desc=ALMONDS
    #     &state=CA
    #     &key=<api_key>


# 3. EXTRACT: READS NAMES, CALLS API
@task
def extract() -> pd.DataFrame:
    """Main extraction task"""
    names = get_mapped_commodity_names()      # ["ALMONDS", "CORN"]
    df = usda_nass_to_df(
        api_key=USDA_API_KEY,
        commodity_names=names                 # ← Use names!
    )
    return df
```

---

## Timeline Breakdown

### 1-Day Intensive (6-7 hours straight)

```
9 AM  | Start: Create commodity_mapper.py         (30 min)
10 AM | Create bootstrap_usda_commodities.py      (30 min)
11 AM | Local unit tests                          (1 hour)
12 PM | Lunch break
1 PM  | Run bootstrap + mappings                  (30 min)
1:30 PM | Integration tests                       (1 hour)
2:30 PM | Deploy to Docker                        (30 min)
3 PM  | Verify in database, done! ✓              (30 min)
```

### 2-3 Days Hybrid ⭐ RECOMMENDED

```
Day 1 (4 hours):
  ├─ 1 hr: Create commodity_mapper.py
  ├─ 1 hr: Create bootstrap flow
  ├─ 1 hr: Local unit tests
  └─ 1 hr: Code review with team

Day 2 (3 hours):
  ├─ 30 min: Run bootstrap
  ├─ 30 min: Create mappings
  ├─ 1 hr: Integration tests
  └─ 30 min: Deploy to staging

Day 3 (2 hours):
  ├─ 1 hr: Full pipeline test
  ├─ 30 min: Data quality review
  └─ 30 min: Move to production
```

### 5-Week Conservative

```
Week 1: Understand architecture (read docs, plan)
Week 2: Create commodity_mapper.py (with review)
Week 3: Create bootstrap flow (with review)
Week 4: Deploy and test (with review)
Week 5: Data quality verification, production (with review)

= Same 4-6 hours of actual work, but spread across 5 weeks
  with multiple review cycles and time for learning
```

---

## Decision Matrix: Which Timeline?

```
Are you a developer         YES ──────→ 1-Day Intensive
who can block 6-7 hours?     NO ──────→ Next question

Do you want time for         YES ──────→ 2-3 Days Hybrid ⭐
reviews between phases?       NO ──────→ Next question

Do you have lots of time     YES ──────→ 5-Week Conservative
to spread this out?           NO ──────→ 2-3 Days Hybrid
```

---

## What Success Looks Like

```
✅ Commodity table populated with ["ALMONDS", "CORN", ...]
✅ Database mappings created (Almond → ALMONDS)
✅ Extract function reads from database
✅ USDA API called with commodity NAMES
✅ Data loaded with correct mappings
✅ Logs show: "Fetching ALMONDS" (not "Fetching 12010")
✅ New crops can be added via database (no code change)
✅ ETL runs successfully end-to-end
✅ Data quality verified
✅ Ready for production
```

---

## Next Steps (Choose One)

```
┌─────────────────────────────────────────┐
│ Want the complete roadmap?              │
│ → Read: START_HERE.md                   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Want working code right now?            │
│ → Read: USDA_NAMES_QUICK_REFERENCE.md  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Want to understand the architecture?    │
│ → Read: USDA_DATA_IMPORT_STRATEGY.md   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Want to pick a timeline?                │
│ → Read: USDA_BOOTSTRAP_CLARIFICATIONS.md│
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Ready to implement?                     │
│ → Read: USDA_IMPLEMENTATION_CHECKLIST.md│
└─────────────────────────────────────────┘
```

---

**Bottom Line**: Yes (names), Database (filtering), and 2-3 days (recommended).
Everything else is detail.
