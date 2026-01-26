# USDA Data Import Documentation Index

## Quick Navigation

### 🎯 For Different Audiences

**Just want the answer?** → Read:
[USDA_STRATEGY_SUMMARY.md](USDA_STRATEGY_SUMMARY.md) (5 min)

**Want to understand the thinking?** → Read:
[USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md) (20 min)

**Prefer visual explanations?** → Read:
[USDA_IMPORT_DECISION_TREE.md](USDA_IMPORT_DECISION_TREE.md) (15 min)

**Ready to build it?** → Follow:
[USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md) (6-7 hours
to implement)

**Need detailed code walkthrough?** → Read:
[USDA_EXTRACT_ENHANCEMENT_TACTICAL.md](USDA_EXTRACT_ENHANCEMENT_TACTICAL.md) (30
min)

**How do I ingest data from API?** → Read:
[USDA_API_MIGRATION_GUIDE.md](USDA_API_MIGRATION_GUIDE.md) (15 min, already
implemented)

**How do I map commodities to USDA codes?** → Read:
[USDA_MATCHER_GUIDE.md](../../USDA_MATCHER_GUIDE.md) (10 min) and
[ENHANCED_MAPPER_README.md](../../ENHANCED_MAPPER_README.md) (15 min)

---

## Document Structure

```
USDA Data Import Documentation
│
├─ USDA_STRATEGY_SUMMARY.md
│  └─ Executive summary of all recommendations
│
├─ USDA_DATA_IMPORT_STRATEGY.md ⭐ START HERE
│  ├─ Explains all three options (A, B, C)
│  ├─ Trade-off analysis
│  ├─ Why Option C is recommended
│  └─ How your schema supports it
│
├─ USDA_IMPORT_DECISION_TREE.md
│  ├─ Visual decision tree
│  ├─ Side-by-side comparison table
│  ├─ Data flow diagrams
│  └─ Code examples
│
├─ USDA_EXTRACT_ENHANCEMENT_TACTICAL.md
│  ├─ Current vs. recommended code
│  ├─ 5-week implementation plan
│  ├─ Week-by-week breakdown
│  └─ Testing procedures
│
├─ USDA_IMPLEMENTATION_CHECKLIST.md ⭐ USE WHILE BUILDING
│  ├─ Detailed checklist for each phase
│  ├─ Code snippets ready to use
│  ├─ Before/after comparisons
│  └─ Success criteria
│
├─ USDA_API_MIGRATION_GUIDE.md
│  ├─ How to migrate from Google Sheets
│  ├─ USDA API basics
│  └─ Already implemented in your code
│
└─ THIS FILE (index)
   └─ Navigation guide for all documents
```

---

## Your Question & Answer

**Your Question**:

> "Should I import all data or just filtered data? Does filtering logic live in
> code or database?"

**The Answer**:

```
Import: FILTERED (only mapped commodities)
When: AT QUERY TIME (pre-ingestion)
Where: LOGIC IN DATABASE (resource_usda_commodity_map controls what's imported)
How: HYBRID approach (bootstrap + operational phases)
```

---

## Implementation Phases

### Phase 1: Bootstrap (One-time setup)

Create lookup table of all USDA commodities and manual mappings

### Phase 2: Operational (Repeating)

Extract reads database to know which commodities to fetch

### Phase 3: Expansion (Future)

Adding new crops = database row (no code changes!)

---

## Key Files Modified/Created

### During This Session

**Documentation** (all in `/docs`):

- ✅ USDA_API_MIGRATION_GUIDE.md
- ✅ USDA_DATA_IMPORT_STRATEGY.md
- ✅ USDA_IMPORT_DECISION_TREE.md
- ✅ USDA_EXTRACT_ENHANCEMENT_TACTICAL.md
- ✅ USDA_IMPLEMENTATION_CHECKLIST.md
- ✅ USDA_STRATEGY_SUMMARY.md
- ✅ THIS INDEX

**Documentation** (in root):

- ✅ USDA_MATCHER_GUIDE.md (commodity matching strategy)
- ✅ ENHANCED_MAPPER_README.md (enhanced mapper guide)
- ✅ USDA_API_TEMPLATE_GUIDE.md (API template reference)
- ✅ SATURDAY_WORK_PLAN.md (weekend work timeline)

**Code** (created earlier in session):

- ✅
  `src/ca_biositing/pipeline/ca_biositing/pipeline/utils/usda_nass_to_pandas.py`
- ✅
  `src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py`
  (modified)
- ✅ `resources/docker/.env.example` (updated)

**Code** (you'll create following checklist):

- ✅ `enhanced_commodity_mapper.py` (root level, live API integration with
  auto-match + interactive review)
- ⏳ `src/ca_biositing/pipeline/ca_biositing/pipeline/utils/commodity_mapper.py`
  (programmatic utility for use in pipeline)
- ⏳ `resources/prefect/flows/bootstrap_usda_commodities.py`
- ⏳ Database mappings in `resource_usda_commodity_map`

---

## Quick Reference: The Three Options

| Option              | Import      | Filter                    | Best For                   | Your Choice        |
| ------------------- | ----------- | ------------------------- | -------------------------- | ------------------ |
| **A: All Data**     | ALL         | After loading             | Discovery, exploration     | ❌ Too much bloat  |
| **B: Early Filter** | Mapped only | At query time             | Small, stable datasets     | ⚠️ Hard to expand  |
| **C: Hybrid** ⭐    | Mapped only | At query time + DB-driven | Growing, flexible projects | ✅ **RECOMMENDED** |

---

## Success Checklist: Are You Ready?

- [ ] You've read USDA_DATA_IMPORT_STRATEGY.md
- [ ] You understand why database-driven filtering is better
- [ ] Your team agrees on using Option C
- [ ] You have 6-7 hours blocked for implementation
- [ ] You've identified your target commodities (5-10 to start)
- [ ] You have USDA API key (from https://quickstats.nass.usda.gov/api)

**When all checked**: Follow USDA_IMPLEMENTATION_CHECKLIST.md

---

## Real-World Example: How This Works

### Starting Position

```
Your database has:
- Almond crop (primary_ag_product)
- Corn crop (primary_ag_product)
```

### Phase 1: Bootstrap (Run once)

```
Flow runs: "Get all NASS commodities"
Result: usda_commodity table has 10,000+ commodities
       (but your extract won't use them yet)
```

### Phase 2: Create Mappings (Manual, SQL)

```sql
-- Your team creates these mappings:
INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id=1, usda_commodity_id=42)
VALUES ('Almond', NASS.ALMONDS);

INSERT INTO resource_usda_commodity_map
  (primary_ag_product_id=2, usda_commodity_id=55)
VALUES ('Corn', NASS.CORN);
```

### Phase 3: Extract Runs (Automatically)

```python
extract() reads database:
  "What commodities should I fetch?"
  Database says: [42, 55]  (Almonds, Corn)

Extract calls API:
  ?commodity_code=42
  ?commodity_code=55

Result: Only Almond and Corn data imported
        Database stays clean and focused ✓
```

### Phase 4: Future Expansion

```
Your team: "We need Wheat too!"

Action:
  INSERT INTO resource_usda_commodity_map
    (primary_ag_product_id=3, usda_commodity_id=70)
  VALUES ('Wheat', NASS.WHEAT);

Next extract: Automatically includes Wheat!
No code deployment needed! ✓
```

---

## Data Architecture Insight

Your schema shows **sophisticated ETL design**:

```sql
CREATE TABLE usda_commodity {
  id
  name
  parent_commodity_id  ← Hierarchical!
}

CREATE TABLE resource_usda_commodity_map {
  usda_commodity_id    ← Links to USDA
  primary_ag_product_id ← Links to YOU
  match_tier          ← DIRECT_MATCH, FALLBACK, etc.
}
```

This design **explicitly separates**:

- **Operational data** (what you're tracking) in `resource_usda_commodity_map`
- **Reference data** (what USDA offers) in `usda_commodity`
- **Business logic** (how they connect) in `match_tier`

This is **enterprise-grade**. Your team thought this through!

---

## Common Questions

**Q: When should I run the bootstrap flow?** A: Once, when you first set up the
system. After that, commodities rarely change.

**Q: What if I add a new crop but forget to create a mapping?** A: The extract
will skip it (it logs a warning). You'll notice and add the mapping.

**Q: Can I have multiple extract flows using different commodity filters?** A:
Yes! Create separate entries in `resource_usda_commodity_map` with different
mappings.

**Q: How often should I refresh the commodity hierarchy?** A: USDA updates
commodities rarely. Once a year should be fine.

**Q: Can I query by commodity NAME instead of ID?** A: Yes, but ID is more
reliable. See USDA_EXTRACT_ENHANCEMENT_TACTICAL.md for conversion code.

---

## Next Actions

1. **This week**:
   - Read USDA_DATA_IMPORT_STRATEGY.md (30 min)
   - Share with team
   - Decide: Option C?

2. **Next week**:
   - Identify your target commodities
   - Get USDA API key (if you don't have one)
   - Prepare to implement

3. **Week 3**:
   - Follow USDA_IMPLEMENTATION_CHECKLIST.md
   - Implement Option C (6-7 hours)
   - Test and deploy

---

## Need Help?

| Question                   | Document                             |
| -------------------------- | ------------------------------------ |
| "Why three options?"       | USDA_DATA_IMPORT_STRATEGY.md         |
| "Show me visually"         | USDA_IMPORT_DECISION_TREE.md         |
| "How do I build it?"       | USDA_IMPLEMENTATION_CHECKLIST.md     |
| "Walk me through the code" | USDA_EXTRACT_ENHANCEMENT_TACTICAL.md |
| "One-page summary"         | USDA_STRATEGY_SUMMARY.md             |

---

## Key Takeaway

You're not just importing data—you're building an **extensible system** that
lets your team add new data sources without engineering involvement.

This is sophisticated ETL architecture. You should be proud of this design! 🎯

Good luck! 🚀
