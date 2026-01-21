# USDA NASS API Migration Guide

## Overview

This guide explains how the `usda_census_survey.py` extraction module was
converted from a Google Sheets source to the USDA NASS Quick Stats API. This is
a **novice-friendly walkthrough** that explains the "why" behind each decision.

---

## Why Migrate from Google Sheets to USDA API?

### Benefits of the USDA API Approach:

1. **Direct Source of Truth**: The USDA API is the official, authoritative
   source for agricultural data
2. **Real-time Updates**: Data is updated as USDA publishes new statistics
3. **Consistency**: No manual copy/paste to Google Sheets = fewer data entry
   errors
4. **Scale**: The API can handle large queries; Google Sheets has size limits
5. **Automation**: Easier to automate recurring data fetches
6. **Compliance**: Using official sources reduces audit risk

---

## Architecture: Google Sheets → USDA API

### Old Flow (Google Sheets)

```
Google Sheet (manual data entry)
    ↓
gsheet_to_pandas.py (reads sheet using gspread library)
    ↓
usda_census_survey.py extract() task
    ↓
Prefect ETL Pipeline
```

### New Flow (USDA API)

```
USDA NASS Quick Stats API
    ↓
usda_nass_to_pandas.py (utility: calls API, returns DataFrame)
    ↓
usda_census_survey.py extract() task (unchanged structure!)
    ↓
Prefect ETL Pipeline
```

**Key Insight**: The extract function **stays almost identical**. We just swap
out the data source function.

---

## USDA NASS Quick Stats API Basics

### What You Need to Know:

1. **Authentication**: Requires an API key (free, from USDA)
   - Request at: https://quickstats.nass.usda.gov/api
   - API key will be emailed to you

2. **Rate Limits**:
   - Maximum 50,000 records per API call
   - You can make multiple calls to get more data

3. **Data Parameters** (What, Where, When):
   - **What**: Commodity, Data Item (e.g., "CORN", "PRODUCTION")
   - **Where**: State, County (we're filtering for California)
   - **When**: Year

4. **Response Format**: JSON array of records

### Example API Request

```
GET https://quickstats.nass.usda.gov/api/api_GET?
  key=YOUR_API_KEY
  &commodity_desc=CORN
  &state_alpha=CA
  &year=2023
  &format=JSON
```

---

## Implementation Details

### 1. New File: `usda_nass_to_pandas.py`

This utility module handles all the complexity of talking to the USDA API. Think
of it like `gsheet_to_pandas.py` but for the USDA API.

**Why separate it into a utility?**

- **Reusability**: Other extract modules can use this function
- **Testing**: Easy to test API calls independently
- **Maintenance**: API changes only require updating one file
- **Clarity**: The extract module stays simple and focused

**What the utility does:**

1. Takes your API key and search parameters
2. Makes the HTTP request to USDA
3. Handles errors gracefully (network issues, invalid parameters)
4. Converts JSON response to pandas DataFrame
5. Returns data or None if something fails

### 2. Updated: `usda_census_survey.py`

**What Changed:**

- Swapped `gsheet_to_df()` call to `usda_nass_to_df()` call
- Changed configuration from `GSHEET_NAME`, `WORKSHEET_NAME` to API parameters
- Added `USDA_API_KEY` configuration from environment
- Everything else stays the same!

**Why minimal changes?**

- The Prefect task structure (`@task` decorator) doesn't change
- The logging stays the same
- The return type (DataFrame) stays the same
- Future modules that depend on this extract function see no changes

---

## Setup Steps (for you to do)

### Step 1: Get a USDA API Key (5 minutes)

1. Go to: https://quickstats.nass.usda.gov/api
2. Fill out the form (requires valid email)
3. USDA will email you the API key immediately
4. Copy the key

### Step 2: Add API Key to Environment

Edit `resources/docker/.env` (create from `.env.example` if needed):

```dotenv
# Add this line:
USDA_NASS_API_KEY=your_api_key_here
```

The system will read this at runtime using `os.getenv()`.

### Step 3: Install `requests` Library (if not already installed)

The new utility uses Python's `requests` library to call the API. It's probably
already installed, but if you see import errors:

```bash
pixi add --pypi requests
```

---

## How the Data Flows: Step by Step

### Example: Getting 2023 Corn Production Data for California

1. **User/Flow calls**: `extract()` function
2. **Function reads config**: Gets `USDA_API_KEY` from environment
3. **Function calls utility**: `usda_nass_to_df(api_key, state="CA", year=2023)`
4. **Utility constructs URL**: Builds query with state and year filters
5. **Utility makes request**: `requests.get(api_url)` to USDA servers
6. **USDA returns**: JSON array like:
   ```json
   [
     {
       "year": 2023,
       "commodity_desc": "CORN",
       "state_alpha": "CA",
       "county_code": 123,
       "Value": 1000000,
       "unit_desc": "BU",
       ...
     },
     ...
   ]
   ```
7. **Utility converts**: Creates pandas DataFrame from JSON
8. **DataFrame returns**: Back to extract function
9. **Extract function logs**: "Successfully extracted X rows"
10. **Returns to Prefect**: DataFrame goes to next pipeline step (Transform)

---

## Common Questions

### Q: Why do I need to add code to `.env`?

**A**: Environment variables are how Prefect injects secrets without hardcoding
them. If your API key is in code, someone could accidentally commit it to git.
The `.env` file (which is `.gitignore`d) keeps it safe.

### Q: What if the API is down?

**A**: The utility catches network errors and logs them. The extract function
returns `None`, and the pipeline aborts cleanly. This is better than silently
using stale data.

### Q: Can I query multiple states?

**A**: Yes! Currently it's hardcoded for California, but you could modify the
function to accept a state parameter:

```python
def extract(state: str = "CA") -> Optional[pd.DataFrame]:
    # ... code uses state variable in API call
```

### Q: How do I know what commodities are available?

**A**: The USDA API has a metadata endpoint that lists all available
commodities. The utility could be enhanced to fetch this list, but for now,
you'd check the Quick Stats website.

### Q: Will this work with Census and Survey data?

**A**: Yes! The API returns both. The utility doesn't filter by source, so you
get both census (every 5 years) and annual survey data. You can add filtering if
needed.

---

## File Changes Summary

### Created:

- `src/ca_biositing/pipeline/ca_biositing/pipeline/utils/usda_nass_to_pandas.py`
  (new utility)

### Modified:

- `src/ca_biositing/pipeline/ca_biositing/pipeline/etl/extract/usda_census_survey.py`
  (replaced gsheet calls)
- `resources/docker/.env.example` (added USDA_NASS_API_KEY)

### No Changes to:

- Database models (they accept the same data shape)
- Transform functions (they receive the same DataFrame)
- Prefect flows (they call the same extract function)

---

## Next Steps

1. **Test locally**: Run the pipeline and check for errors
2. **Monitor logs**: Look at Prefect UI to see what data is returned
3. **Enhance gradually**: Add more filters or data sources as needed
4. **Document mappings**: Note which USDA commodities map to your resources

---

## Troubleshooting

### Error: "API key not found"

- Check that `USDA_NASS_API_KEY` is in your `.env` file
- Ensure you're in a container context (key must be passed to Docker)

### Error: "Exceeded 50,000 record limit"

- Split queries: Query one year at a time, or filter by commodity
- The utility can be enhanced with pagination logic

### Error: "Invalid parameter"

- Check commodity name spelling (USDA is picky about uppercase)
- Verify state codes match USDA format (e.g., "CA", not "California")

---

## Resources

- **USDA Quick Stats**: https://quickstats.nass.usda.gov/
- **API Documentation**: https://quickstats.nass.usda.gov/api
- **Requests Library**: https://requests.readthedocs.io/
- **Your ETL Guide**: `docs/pipeline/ETL_WORKFLOW.md`
