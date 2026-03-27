# Plan: Standalone AI Exploration Playground

## Objective

To enable natural language data exploration using **PandasAI 2.0+** and the
**CBORG API** without encountering dependency conflicts with the main
`ca-biositing` project stack. This standalone environment allows for rapid
prototyping and interactive visualization of materialized views.

## 🏗️ Directory Structure

The playground will be isolated in the `analysis/` root directory.

```text
/ca-biositing
├── analysis/
│   ├── ai_exploration/
│   │   ├── pixi.toml          # Independent Pixi configuration
│   │   ├── .env.example       # Template for CBORG_API_KEY and DB credentials
│   │   ├── README.md          # Setup instructions for this playground
│   │   └── ai_analysis.ipynb  # Refactored exploration notebook
```

## 🛠️ Environment Configuration (`pixi.toml`)

The `analysis/ai_exploration/pixi.toml` will be minimal to avoid solver
conflicts.

- **Python**: `~=3.12`
- **Dependencies (conda-forge)**:
  - `python-dotenv`
  - `sqlalchemy`
  - `psycopg2`
  - `matplotlib-base`
  - `plotly`
- **PyPI Dependencies**:
  - `pandasai >= 2.0.0`
  - `pandas >= 2.2.0`
  - `ipykernel`

## 🔄 Data Workflow

Since this environment is decoupled, we will not import the
`ca_biositing.datamodels` package directly. Instead, we use a SQL-first
approach:

1.  **Connection**: Establish a SQLAlchemy engine using credentials from `.env`.
2.  **Fetch**: Execute `SELECT * FROM ca_biositing.analysis_data_view` to load
    data into a standard Pandas DataFrame.
3.  **Enhance**: Wrap the DataFrame in `pandasai.SmartDataframe`.
4.  **Query**: Use natural language to generate insights and plots.

## 🔐 Authentication & API

- **CBORG API**: Configure `pandasai` to use the `https://api.cborg.lbl.gov/v1`
  endpoint.
- **Model**: Default to `gemini-2.0-flash` or `gemini-3-flash`.
- **Database**: Assume a local PostgreSQL instance (default) or a remote
  instance accessible via `localhost` (Cloud SQL Proxy).

## 📓 Notebook Sections

The refactored `ai_analysis.ipynb` will contain:

1.  **Setup**: Loading `.env` and initializing the LLM.
2.  **Database Connection**: SQLAlchemy engine setup.
3.  **Data Loading**: SQL queries to pull materialized views into memory.
4.  **AI Querying**: Examples of `SmartDataframe.chat()` for analysis.
5.  **Visualization**: Examples of automated plotting (Bar charts, Scatter
    plots).
