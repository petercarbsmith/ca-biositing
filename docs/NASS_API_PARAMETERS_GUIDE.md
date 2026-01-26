# NASS API Parameters & California Agriculture Query Strategy

## Understanding the NASS API Parameters

### 1. **agg_level_desc** (Aggregation Level)

Controls the geographic granularity of data:

- **"STATE"**: All data for California combined (coarser)
- **"COUNTY"**: Data broken down by county (finer detail) ← **We use this**
- **"DISTRICT"**: Agricultural district level
- **"NATIONAL"**: All US data

**For your project**: Use `agg_level_desc="COUNTY"` to get county-level data
without having to query each county individually. The API will return data for
all California counties in one request.

### 2. **statisticcat_desc** (Statistic Category)

What type of agricultural data you want:

- **"AREA HARVESTED"**: Acres actually harvested
- **"AREA PLANTED"**: Acres planted (may be different if some left unharvested)
- **"PRODUCTION"**: Total production amount (e.g., bushels, tons)
- **"YIELD"**: Production per unit area (e.g., bushels/acre) ← **Good for
  understanding productivity**
- **"PRICE RECEIVED"**: Market prices

**For your project**: Start with `"YIELD"` to understand productivity per acre
across counties.

### 3. **unit_desc** (Unit Description)

The measurement units for the statistic:

- **"ACRES"**: Used with area statistics (AREA HARVESTED, AREA PLANTED)
- **"BUSHELS"**: Used with yield/production for grains (corn, wheat)
- **"TONS"**: Used with yield/production for heavier crops
- **"DOLLARS"**: Used with price/value statistics
- **"POUNDS"**: Used with crops measured by weight
- **"CWT"** (hundredweight): Used for some crops

**For your project**:

- `unit_desc="BUSHELS"` when `statisticcat_desc="YIELD"` for corn/wheat
- `unit_desc="ACRES"` when `statisticcat_desc="AREA HARVESTED"`

### 4. **domain_desc** (Domain Description)

Filters to specific subsets of operations:

- **"TOTAL"**: All operations combined ← **Most common, use this**
- **"FARM SIZE"**: Broken down by farm size categories
- **"ORGANIC STATUS"**: Organic vs. conventional
- **"IRRIGATED"**: Only irrigated operations
- **"OPERAATED BY"**: Broken down by operator demographics
- etc.

**For your project**: Use `domain_desc="TOTAL"` to get aggregate data without
demographic filtering.

### 5. **commodity_desc** (Commodity Description)

The specific crop you're interested in. **Must match NASS exactly**
(case-sensitive):

- "CORN"
- "ALMONDS"
- "WHEAT"
- "TOMATOES"
- "COTTON"
- "RICE"
- "GRAPES"
- etc.

**For your project**: Use commodity codes from `get_mapped_commodity_ids()`,
which returns the correct NASS codes.

---

## Data Granularity: County vs. State

### Your Question: "Query at CA level or individual counties?"

**Answer**: When you use `agg_level_desc="COUNTY"`, the API will:

1. Return data broken down by county
2. Still only count as ONE API request
3. Each row will have a county identifier (FIPS code or name)
4. You get all ~58 CA counties in a single response

**Example Response Structure**:

```
commodity | year | county_name | county_fips | yield | unit
----------|------|-------------|-------------|-------|------
CORN      | 2023 | San Joaquin | 06077       | 142   | BUSHELS
CORN      | 2023 | Stanislaus  | 06099       | 138   | BUSHELS
CORN      | 2023 | Merced      | 06047       | 135   | BUSHELS
... (all other CA counties)
```

### Storage Strategy

**In your database**, you have two options:

**Option A (Recommended): Store individual county records**

```
usda_census_record table:
- id
- geoid (county FIPS code, e.g., 06077)
- county_name (e.g., "San Joaquin")
- commodity_name
- year
- yield / production / area_harvested
- created_at
```

**Option B: Query individual counties (less efficient)**

- Requires separate API calls for each county (more requests, slower)
- Same 50k record limit still applies
- More complex error handling

**We chose Option A** (implement both in database).

---

## North San Joaquin Valley Priority Counties

These are your three focus counties (for now):

| County      | FIPS Code | Reason                                 |
| ----------- | --------- | -------------------------------------- |
| San Joaquin | 06077     | High concentration of crops            |
| Stanislaus  | 06099     | Major agricultural region              |
| Merced      | 06047     | Part of Central Valley agriculture hub |

These are stored in `nass_config.py`:

```python
PRIORITY_COUNTIES = {
    "San Joaquin": "06077",
    "Stanislaus": "06099",
    "Merced": "06047",
}
```

---

## Record Counting for Tracking

We've added record counting to track:

- **Total records imported per commodity**
- **Records per query** (with year and parameters)
- **Import timestamp**
- **Query parameters used**

This appears in the notebook output:

```
============================================================
IMPORT SUMMARY
============================================================
Total Records Imported: 243
Parameters Used:
  - State: CA
  - Year: 2023
  - Aggregation Level: COUNTY
  - Domain: TOTAL
  - Statistic Category: YIELD
  - Unit: BUSHELS
============================================================
```

---

## Step 4 Error Analysis

When you see an error in Step 4, it could be:

1. **"No data returned"**: The commodity may not have yield data for 2023
   - Solution: Try `statisticcat_desc="AREA HARVESTED"` instead

2. **"HTTP 400 Bad Request"**: Typo in parameter (e.g., wrong commodity name)
   - Solution: Check exact spelling in NASS (case-sensitive)

3. **"HTTP 429 Too Many Requests"**: Rate limiting
   - Solution: We handle this with 1-second delays and exponential backoff

4. **"50k record limit exceeded"**: Query is too broad
   - Solution: Add more filters (specific years, commodities, statistics)

---

## Next Steps: Multi-County Import

To query all three priority counties in San Joaquin Valley:

```python
# Query San Joaquin County specifically
raw_data = usda_nass_to_df(
    commodity_ids=[commodity_ids[0]],
    api_key=api_key,
    year=2023,
    county_code="06077",  # San Joaquin
    agg_level_desc="COUNTY",
    statisticcat_desc="YIELD",
    unit_desc="BUSHELS"
)

# Repeat for other counties: 06099 (Stanislaus), 06047 (Merced)
```

Or query all CA counties at once and filter in your database:

```python
raw_data = usda_nass_to_df(
    commodity_ids=[commodity_ids[0]],
    api_key=api_key,
    year=2023,
    agg_level_desc="COUNTY",  # Gets all counties
    statisticcat_desc="YIELD",
    unit_desc="BUSHELS"
)

# Then in database layer, filter to priority counties
priority_fips = ["06077", "06099", "06047"]
```

---

## References

- NASS API Documentation: https://quickstats.nass.usda.gov/api
- R NASS Guide (excellent examples):
  https://content.ces.ncsu.edu/getting-data-from-the-national-agricultural-statistics-service-nass-using-r
- NASS Parameter Guide: https://quickstats.nass.usda.gov/param_define
- California County FIPS Codes: https://en.wikipedia.org/wiki/FIPS_code
