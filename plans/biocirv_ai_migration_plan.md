# Plan & Accomplishments: BioCirv AI Standalone Migration

## 🎯 Objective

The goal was to transition the AI Exploration Sandbox from an isolated directory
in the `ca-biositing` monorepo into a high-quality, standalone repository
([`biocirv-ai`](https://github.com/sustainability-software-lab/biocirv-ai)) that
serves as a shared "product" for natural language geospatial analysis.

## ✅ Accomplishments

### 1. Standalone Repository Architecture

- **Namespace Package**: Implemented the PEP 420 pattern
  (`ca_biositing.ai_exploration`). This preserves the project brand while
  allowing the package to be installed independently via
  `pip install git+https://...`.
- **Build System**: Configured `pyproject.toml` with the `hatchling` backend,
  following modern Python packaging standards.
- **Environment Management**: Created a robust `pixi.toml` with specific
  environments for GIS (`geopandas`, `folium`) and development (`pytest`,
  `pre-commit`).

### 2. Hardened Core Logic

- **`sandbox_setup.py`**: Refactored the `CBORGLLM` and `SandboxResponseParser`
  into the namespace package.
- **`schema.py` (New)**: Replaced the manual metadata lists with a **dynamic
  discovery system**. The AI agent now automatically queries PostgreSQL's
  `information_schema` to find and describe all views in the `ca_biositing` and
  `analytics` schemas.
- **Geospatial Readiness**: Added hooks for automated mapping detection
  (Plotly/Folium) within the response parser.

### 3. CI/CD & Quality Standards

- **GitHub Actions**: Created a full CI pipeline (`.github/workflows/ci.yml`)
  that runs tests and coverage on Ubuntu and macOS.
- **Pre-commit**: Mirrored the parent project's strict linting and formatting
  standards (`prettier`, `codespell`, `trailing-whitespace`) to ensure code
  quality matches the core repository.

### 4. Git Integration (Submodule)

- **Submodule Linkage**: Added the new repo as a Git submodule at
  `analysis/biocirv-ai`.
- **Legacy Cleanup**: Safely removed the old `analysis/ai_exploration`
  directory.
- **Personal Fork Workflow**: All integration changes were pushed to the
  `feat-pandasai-integration` branch on the user's personal fork for clean PR
  management.

## 🏛️ Discussion: State of the Architecture

### The "Submodule vs. Package" Strategy

By structuring `biocirv-ai` as both a **submodule** and a **namespace package**,
we have achieved a highly flexible architecture:

- **For Main Project Developers**: They see the code at `analysis/biocirv-ai`.
  It is "followed" by Git but remains "inactive" in their main Pixi environment
  until they choose to install it. This prevents dependency bloat in the main
  ETL pipeline.
- **For External Researchers**: They can use the AI tools in **Google Colab** or
  other environments by simply installing the standalone package. They don't
  need to clone the 100+ models of the main repository.

### Dynamic Discovery & Resilience

The move to dynamic schema discovery in `schema.py` is a major architectural
improvement. The AI tool is no longer "brittle"—as new materialized views are
added to the database via Alembic migrations in the main project, the AI sandbox
automatically detects them on the next startup without a single line of code
change in the `biocirv-ai` repo.

## 🚀 Next Phase: Technical Refinement

### 1. Geospatial Tool Integration

A major goal for the standalone product is the ability to generate maps directly
from natural language.

- **Tools**: Integrate **Geopandas** and **Folium** more deeply into the AI
  agent's environment.
- **Capabilities**: Enable the agent to recognize `geoid` or coordinate columns
  and automatically produce choropleth maps (e.g., California county-level
  production) or point-based visualizations of facilities.
- **Workflow**: Ensure the `SandboxResponseParser` can detect Folium map objects
  and render them interactively in the notebook.

### 2. Cloud Connectivity (Google Colab)

- **Action**: Implement a secure connection from Colab to GCP-hosted databases
  (Staging/Production) via the **Cloud SQL Auth Proxy** integrated into the
  notebook setup.

### 3. Flagged Issues & Improvements

- **🚩 SmartDataFrame Parsing**: We are investigating reports of inconsistent
  parsing when using `SmartDataFrame`. The goal is to ensure the internal
  dispatching always returns native objects rather than wrapped responses.
- **🚩 Table Rendering Consistency**: Some queries still return
  `DataFrameResponse` wrappers. We are working on the `SandboxResponseParser` to
  ensure **100%** native table rendering in the VS Code Data Viewer.
- **🚩 LLM Latency**: Performance varies based on CBORG gateway load; 60s
  timeouts are in place, but we may need to implement more aggressive retry
  logic.

## 🔗 Repository Reference

- **GitHub Repo**:
  [sustainability-software-lab/biocirv-ai](https://github.com/sustainability-software-lab/biocirv-ai)
- **Local Path**: `analysis/biocirv-ai` (Submodule)
- **Namespace**: `ca_biositing.ai_exploration`

---

_Last Updated: 2026-03-28_
