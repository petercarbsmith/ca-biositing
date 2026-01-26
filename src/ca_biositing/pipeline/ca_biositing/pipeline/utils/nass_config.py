"""
NASS API Configuration and Constants

This module defines configuration parameters for USDA NASS QuickStats API queries,
including geographic focus areas and data collection parameters.

Reference: https://content.ces.ncsu.edu/getting-data-from-the-national-agricultural-statistics-service-nass-using-r
"""

# ============================================================================
# GEOGRAPHIC CONFIGURATION
# ============================================================================

# Priority Counties: North San Joaquin Valley, California
# FIPS codes for counties of focus
PRIORITY_COUNTIES = {
    "San Joaquin": "06077",
    "Stanislaus": "06099",
    "Merced": "06047",
}

STATE_CODE = "CA"

# ============================================================================
# NASS API PARAMETERS EXPLANATION
# ============================================================================
"""
Key NASS API Parameters:

1. **agg_level_desc** (Aggregation Level Description)
   - "NATIONAL": Data aggregated at US national level
   - "STATE": Data aggregated at state level (e.g., all of California)
   - "COUNTY": Data aggregated at county level (finest granularity)
   - "DISTRICT": Data aggregated by agricultural district

   For county-level analysis, use "COUNTY"

2. **unit_desc** (Unit Description)
   - "ACRES": Measured in acres (for area data)
   - "BUSHELS": Measured in bushels (for yield/production)
   - "TONS": Measured in tons
   - "DOLLARS": Monetary values
   - etc.

   Example: unit_desc="ACRES" for harvested/planted acreage

3. **domain_desc** (Domain Description)
   - "TOTAL": Total for all operations (most common)
   - "FARM SIZE": Broken down by farm size
   - "ORGANIC STATUS": Broken down by organic/conventional
   - "IRRIGATED": Subset of irrigated operations only
   - etc.

   Use "TOTAL" for aggregate counts without demographic breakdowns

4. **statisticcat_desc** (Statistic Category Description)
   - "AREA HARVESTED": Acres harvested (of total planted)
   - "AREA PLANTED": Acres planted
   - "PRODUCTION": Total production amount
   - "YIELD": Production per unit area
   - etc.

   Example: For corn, statisticcat_desc="YIELD" gets bushels per acre

5. **commodity_desc** (Commodity Description)
   - "CORN": Corn (any type)
   - "ALMONDS": Almonds
   - "WHEAT": Wheat (any type)
   - "TOMATOES": Fresh market tomatoes
   - etc.

   Must match NASS exactly (case-sensitive, with spaces)

6. **prodn_practice_desc** (Production Practice Description)
   - "ALL PRODUCTION PRACTICES": All practices combined
   - "IRRIGATED": Irrigated operations only
   - "NOT IRRIGATED": Non-irrigated operations only
   - etc.
"""

# ============================================================================
# RECOMMENDED QUERY PARAMETERS FOR CA AGRICULTURE
# ============================================================================

# Default parameters for California county-level agricultural queries
DEFAULT_NASS_PARAMS = {
    "agg_level_desc": "COUNTY",      # County-level granularity
    "unit_desc": "ACRES",             # Measured in acres
    "domain_desc": "TOTAL",           # Total across all operations
    "prodn_practice_desc": "ALL PRODUCTION PRACTICES",  # All practices
}

# For yield/production data, add:
YIELD_PARAMS = {
    "statisticcat_desc": "YIELD",
    "unit_desc": "BUSHELS",  # or appropriate unit for commodity
}

# For area data (harvested/planted), add:
AREA_PARAMS = {
    "statisticcat_desc": "AREA HARVESTED",
    "unit_desc": "ACRES",
}

# ============================================================================
# COMMON CA COMMODITIES
# ============================================================================

CA_COMMODITIES = {
    "CORN": "11199199",
    "ALMONDS": "26199999",
    "WHEAT": "10199999",
    "TOMATOES": "37899999",
    "COTTON": "15199999",
    "RICE": "12199999",
    "GRAPES": "26199999",
}

# ============================================================================
# NASS API RATE LIMITING & RESPECT
# ============================================================================

# IMPORTANT: NASS API Limits
# - Maximum 50,000 records per request (hard limit)
# - Respectful clients: 1-2 second delay between requests
# - Do NOT hammer the API with rapid requests

# Rate limiting configuration
REQUEST_DELAY = 1.0  # Seconds between API requests
MAX_RETRIES = 3      # Number of retry attempts on failure
TIMEOUT = 30         # Request timeout in seconds

# ============================================================================
# DATA COLLECTION STRATEGY
# ============================================================================
"""
Recommended approach for importing CA agricultural data:

1. **Phase 1: County-Level, Single Commodity**
   - Focus: North San Joaquin Valley (San Joaquin, Stanislaus, Merced)
   - Commodity: Start with CORN
   - Years: 2018-2023 (recent 5 years)
   - Params: agg_level_desc="COUNTY", commodity_desc="CORN", statisticcat_desc="YIELD"
   - Expected: < 50k records

2. **Phase 2: Expand to Multiple Commodities**
   - Add: ALMONDS, WHEAT, TOMATOES, COTTON, RICE
   - Same geography and years
   - May need to query each commodity separately

3. **Phase 3: Expand Geographic Scope**
   - Query all 58 CA counties
   - Or query at STATE level (agg_level_desc="STATE")

4. **Record Counting**
   - Always check API response for record count
   - Log each import with timestamp and record count
   - Track total records imported per commodity/year combination
"""
