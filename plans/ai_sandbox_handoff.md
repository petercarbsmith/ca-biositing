# Handoff: AI-Driven Data Sandbox Implementation (Phase 1)

## Overview

We have successfully enabled natural language data exploration in the
`ca-biositing` project by creating an isolated, interactive sandbox environment.
This allows users to query bioeconomy production data and USDA census views
using plain English and receive interactive visualizations.

## Current State of `analysis/ai_exploration/`

### 1. Isolated Environment

- **Standalone `pixi.toml`**: Created a dedicated environment to manage
  **PandasAI 3.0.0** and its strict dependencies (legacy Pandas/NumPy versions)
  without affecting the main project.
- **Key Dependencies**: Added `pandasai`, `plotly`, `nbformat` (for rendering),
  and `sqlalchemy`.
- **Kernel**: Registered as `Python (AI Exploration)`.

### 2. Implementation Highlights

- **CBORG Integration**: Developed a custom `CBORGLLM` wrapper. Since PandasAI
  3.0 is modular and lacks built-in providers for the CBORG gateway, this
  wrapper uses the `requests` library to interface with Gemini models via LBL's
  API.
- **Interactive Visualizations**:
  - Resolved rendering issues where Plotly would only output file paths.
  - Implemented a **Global Monkeypatch** on
    `pandasai.core.response.base.BaseResponse` to intercept HTML file paths and
    inject the Plotly content directly into the notebook using `_repr_html_`.
- **Database Connectivity**: Connected to the local PostgreSQL instance to pull
  three key views:
  - `analysis_data_view`
  - `usda_census_view`
  - `analysis_average_view`

### 3. Functional Notebooks

- **`sandbox_exploration.ipynb`**: The primary user playground with
  pre-configured cells for:
  - Total volume aggregations by crop category.
  - Leading county filters for almond residues.
  - **Interactive Scatter Plots**: Glucan vs. Xylan analysis with hover support.
  - **Multi-DataFrame Analysis**: Initial demonstration of correlating analysis
    data with USDA census stats.
- **`ai_analysis.ipynb`**: An updated template notebook following the same
  architecture.

---

## Future Avenues for Improvement (Phase 2)

### 1. Hardening & User Experience

- **Logic Extraction**: Refactor the setup logic (LLM initialization, DB engine
  creation, and monkeypatching) out of the notebook cells and into a standalone
  script (e.g., `analysis/ai_exploration/setup.py`).
- **One-Line Initialization**: Aim for a single import statement or function
  call at the top of the notebook to hide implementation details from the
  end-user.

### 2. High-Performance Connectivity

- **SQL Connectors**: Currently, data is pre-loaded into Pandas DataFrames. We
  should explore using **PandasAI SQL Connectors** to query PostgreSQL directly.
- **Benefits**: This would allow the LLM to generate SQL that executes on the
  database engine, significantly improving join performance and reducing memory
  overhead for large views.

### 3. Metadata & Context Enrichment

- **Automated Metadata**: Implement logic to fetch column descriptions or table
  comments from the PostgreSQL `information_schema` or `pg_description`.
- **Context Dictionaries**: Create a structured mapping file that provides the
  LLM with deep context about what specific parameters (like `xylan`, `glucan`,
  `unit`) actually mean in the bioeconomy domain. This will improve query
  accuracy and insight generation.

### 4. SmartDataLake Optimization

- Continue refining the `SmartDatalake` implementation to ensure the AI
  understands the relationships between production records and USDA regional
  statistics more reliably.

### 5. Geospatial Visualization Integration

- **Geopandas/Folium Support**: Investigate enabling the AI to generate
  geospatial figures (e.g., choropleth maps of California counties) by
  integrating libraries like `geopandas` or `folium`.
- **Spatial Queries**: Experiment with natural language prompts that require
  spatial understanding, such as "Map the total volume of residues for all
  counties in the Central Valley."
- **Coordinate Mapping**: Ensure the agent can correctly interpret the `geoid`
  or latitude/longitude columns to produce accurate map layers.
