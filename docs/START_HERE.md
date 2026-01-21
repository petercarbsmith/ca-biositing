# START HERE: USDA Pipeline Redesign

Welcome! You've asked three important questions about moving your ETL from
Google Sheets to the USDA API. This guide answers all of them and shows you the
complete path forward.

---

## Your Questions Answered

### Q1: "Can I use commodity NAMES instead of numeric IDs?"

**Answer**: ✅ **YES, and it's better!**

Names are more user-friendly, match how USDA works naturally, and make debugging
easier.

**See**: [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)

- Complete name-based workflow (bootstrap → mapping → extraction)
- Side-by-side comparison of names vs IDs
- Ready-to-use code examples for each step

---

### Q2: "Where does the filtering logic live—code or database?"

**Answer**: 🎯 **Database (best practice for scalability)**

Your code should read from the database which crops matter, then fetch only
those from USDA. This way:

- ✅ No code changes to add new crops
- ✅ Business logic stays in database
- ✅ System scales as you grow

**See**: [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)

- Three implementation options analyzed
- Why database-driven filtering wins (Option C)
- Data flow diagrams and schema details

---

### Q3: "Why 5 weeks instead of 6-7 hours?"

**Answer**: ⏱️ **Both are valid! Choose your speed:**

| Timeline            | Best For                                               | Effort       |
| ------------------- | ------------------------------------------------------ | ------------ |
| **1 day** (6-7 hrs) | Confident developers with blocked time                 | Intensive    |
| **2-3 days**        | Most teams; balanced speed + reviews                   | Recommended  |
| **5-8 weeks**       | Teams wanting slower cadence or less DevOps experience | Conservative |

**See**: [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)

- All three timeline options with hour-by-hour breakdown
- Prerequisites for each speed
- Realistic outcomes per timeline

---

## The Complete Roadmap

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: UNDERSTAND THE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│ Read in this order:                                         │
│ 1. USDA_DATA_IMPORT_STRATEGY.md        (15 min)             │
│ 2. USDA_NAMES_QUICK_REFERENCE.md       (10 min)             │
│ 3. USDA_BOOTSTRAP_CLARIFICATIONS.md    (15 min)             │
│                                                             │
│ After: You understand the architecture & tradeoffs         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: CHOOSE YOUR SPEED                                 │
├─────────────────────────────────────────────────────────────┤
│ Pick ONE:                                                   │
│ □ 1-day intensive (6-7 hours, all at once)                 │
│ □ 2-3 days hybrid (4-5 hours spread across days)           │
│ □ 5-8 weeks conservative (part-time over weeks)            │
│                                                             │
│ See: USDA_BOOTSTRAP_CLARIFICATIONS.md for exact schedule    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: IMPLEMENT                                          │
├─────────────────────────────────────────────────────────────┤
│ Follow the checklist for your chosen speed:                │
│ • USDA_IMPLEMENTATION_CHECKLIST.md (all phases)            │
│ • Reference code: USDA_NAMES_QUICK_REFERENCE.md            │
│                                                             │
│ Core work:                                                  │
│ 1. Create commodity_mapper.py         (30 min)              │
│ 2. Create bootstrap_usda_commodities.py (30 min)           │
│ 3. Run bootstrap, create mappings     (1 hour)              │
│ 4. Test extraction locally            (1-2 hours)          │
│ 5. Deploy to Docker, run full flow    (1 hour)             │
│                                                             │
│ Total effort: 4-6 hours actual work (spread across your chosen timeline)
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: VERIFY & DEPLOY                                   │
├─────────────────────────────────────────────────────────────┤
│ • Run integration tests                                     │
│ • Check data quality in database                            │
│ • Deploy to production                                      │
│                                                             │
│ Reference: Phase 7 & 8 of USDA_IMPLEMENTATION_CHECKLIST.md │
└─────────────────────────────────────────────────────────────┘
```

---

## Documentation Map

### Quick Reference (Start Here)

- **[USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)** ⭐
  - Complete workflow using names instead of IDs
  - Copy-paste ready code examples
  - **Time**: 10 minutes to read

### Strategy & Architecture (Why This Works)

- **[USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)**
  - Three implementation options (Import All vs Filter Early vs Hybrid)
  - Analysis of tradeoffs
  - Schema deep-dive
  - **Time**: 20 minutes to read

- **[USDA_IMPORT_DECISION_TREE.md](USDA_IMPORT_DECISION_TREE.md)**
  - Decision flowchart for choosing your approach
  - **Time**: 5 minutes

- **[USDA_STRATEGY_SUMMARY.md](USDA_STRATEGY_SUMMARY.md)**
  - Executive summary of all options
  - **Time**: 10 minutes

### Implementation (How to Build It)

- **[USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)** ⭐
  - Three timeline options (1-day, 2-3 day, 5-week)
  - Hour-by-hour breakdown for each
  - **Time**: 15 minutes to find your option

- **[USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md)** ⭐
  - Complete 8-phase checklist
  - Code snippets for each phase
  - Testing strategy
  - **Time**: Reference while implementing (30 min to skim)

### Deep Dives (If You Need Details)

- **[USDA_API_MIGRATION_GUIDE.md](USDA_API_MIGRATION_GUIDE.md)**
  - Complete API documentation
  - How to get API key
  - All parameters explained
  - Error handling guide

- **[USDA_EXTRACT_ENHANCEMENT_TACTICAL.md](USDA_EXTRACT_ENHANCEMENT_TACTICAL.md)**
  - Detailed technical guide for extraction
  - Performance optimization tips
  - **Time**: 20 minutes

### Reference

- **[USDA_DOCUMENTATION_INDEX.md](USDA_DOCUMENTATION_INDEX.md)**
  - Full index of all documents
  - What each file covers
  - **Time**: 5 minutes

---

## What You'll Accomplish

By the end of this work, you'll have:

✅ **Automated extraction from USDA API** (no more Google Sheets manual updates)
✅ **Database-driven configuration** (add crops by updating database, not code)
✅ **Name-based commodity selection** (user-friendly, readable logs) ✅
**Scalable pipeline** (grows with your resource list without code changes) ✅
**Clean separation of concerns** (business logic in database, operational logic
in code)

---

## Getting Started (Next Steps)

### Immediate (Next 30 minutes)

1. Read [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md) for context
2. Skim [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md) for code
   examples
3. Choose your timeline in
   [USDA_BOOTSTRAP_CLARIFICATIONS.md](USDA_BOOTSTRAP_CLARIFICATIONS.md)

### Short-term (Your chosen timeline)

- Follow [USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md)
- Create commodity_mapper.py (30 min)
- Create bootstrap flow (30 min)
- Test locally (1-2 hours)
- Deploy (1 hour)

### Optional but Recommended

- Read [USDA_API_MIGRATION_GUIDE.md](USDA_API_MIGRATION_GUIDE.md) if you want
  deep API knowledge
- Check
  [USDA_EXTRACT_ENHANCEMENT_TACTICAL.md](USDA_EXTRACT_ENHANCEMENT_TACTICAL.md)
  for performance tips

---

## FAQ

### "Should I use names or IDs?"

**Names.** See [USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md)
for why and how.

### "Do I really need to understand all three options?"

**No.** Start with [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md)
and look for "Option C (Recommended)."

### "How long will this really take?"

**4-6 hours of actual work**, spread across your chosen timeline:

- 1-day intensive: 6-7 hours straight
- 2-3 day hybrid: 4-5 hours split across days (recommended for most teams)
- 5-week conservative: 1 hour per week + reviews

### "What if I hit an error?"

See error sections in
[USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md) Phase 7 and
Phase 8.

### "Can I rollback if something goes wrong?"

Yes! See "Deployment" section in
[USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md).

---

## Your Next Action

👉 **Open [USDA_DATA_IMPORT_STRATEGY.md](USDA_DATA_IMPORT_STRATEGY.md) and read
the first 15 minutes.**

After that, you'll understand the architecture and be ready to choose your
implementation speed.

---

**Questions?** Check [USDA_DOCUMENTATION_INDEX.md](USDA_DOCUMENTATION_INDEX.md)
for the document that covers your topic.

**Ready to code?** Jump to
[USDA_IMPLEMENTATION_CHECKLIST.md](USDA_IMPLEMENTATION_CHECKLIST.md) for
step-by-step guidance.

**Want quick code examples?** See
[USDA_NAMES_QUICK_REFERENCE.md](USDA_NAMES_QUICK_REFERENCE.md).
