# Current State: AI Exploration Sandbox

This document provides a comprehensive summary of the `analysis/ai_exploration/` directory, merging the progress from all implementation phases and outlining the current hardened architecture.

## 🌟 Overview
The AI Exploration Sandbox is a standalone, isolated environment within the `ca-biositing` project designed for natural language data exploration. It leverages **PandasAI 3.0+** and the **CBORG LLM gateway** (Gemini/GPT models) to allow researchers to query PostgreSQL materialized views using plain English and receive rich, interactive visualizations.

## 🏗️ Architecture & Component Summary

### 1. Isolated Environment
- **Standalone Management**: Managed by its own `analysis/ai_exploration/pixi.toml` to prevent dependency conflicts with the main project.
- **Dedicated Kernel**: Registered as **`Python (AI Exploration)`**. This kernel must be selected in VS Code to ensure all specialized rendering and PandasAI logic function correctly.
- **Key Dependencies**: `pandasai 3.0.0`, `plotly`, `nbformat`, `sqlalchemy`, `psycopg2-binary`.

### 2. Core Infrastructure (`sandbox_setup.py`)
This file is the single source of truth for the sandbox initialization:
- **`CBORGLLM` (Hardened)**: A custom LLM wrapper for the LBL gateway. It features `requests.Session` pooling, 60-second timeouts, and robust error handling for API connectivity.
- **`SandboxResponseParser` (Premium Rendering)**: 
    - **Recursive Unwrapping**: Aggressively strips PandasAI internal wrappers to return raw `pd.DataFrame` and `go.Figure` objects.
    - **Scrollable Tables**: DataFrames render as interactive HTML tables in Jupyter and trigger the **VS Code Data Viewer**.
    - **Visualization Routing**: Automatically detects Plotly Figures, Matplotlib images (`.png`), and complex multi-paneled HTML/JSON strings, ensuring they all render directly in the notebook cell.
- **`init_sandbox(model_name=...)`**: Provides one-line initialization with upfront model selection (Gemini, GPT-4o, Claude).
- **`execute_sql_query` Skill**: A registered global skill that allows the agent to perform direct SQL joins on the database for complex queries, restricted to read-only `SELECT` operations.

### 3. Functional Notebooks
- **`sandbox_exploration.ipynb`**: The primary testing and analysis playground.
- **`ai_analysis.ipynb`**: A clean template for starting new natural language analyses.

---

## 🚀 Next Phase: Architectural Refinement (Phase 3)

### 1. Distribution Strategy: Monorepo vs. Separate Repo
The project is moving toward a **Separate Repository** approach to evolve the sandbox into a shared "product."

#### Path: The Standalone Product (Separate Repo)
- **Action**: Move `ai_exploration` to a new repository (e.g., `ca-biositing-ai`).
- **Pros**: **Ideal for Google Colab integration.** Users can `pip install` the package or clone a tiny repo directly into a Colab environment.
- **Cloud Connectivity**: Secure connection from Colab to GCP-hosted databases (Staging/Production) will be handled via the **Cloud SQL Auth Proxy** integrated into the notebook setup.
- **Independence**: Decouples the AI tool's release cycle from the main ETL pipelines.

### 2. Automatic Schema Discovery
The manual list of views in `get_agent_with_metadata` will be replaced with an automated discovery system.
- **Logic**: A startup utility will query PostgreSQL `information_schema` to find all views in the `ca_biositing` and `analytics` schemas.
- **Resilience**: This ensures the AI tool automatically adapts to new views or renamed tables in the main project without code changes.

### 3. Namespace Package Refinement
The standalone repo will still be structured as a **PEP 420 namespace package** (`ca_biositing.ai_exploration`). This maintains branding and allows for future re-integration or shared utility usage if desired.

### 4. Geospatial Tool Integration
A major goal for the standalone product is the ability to generate maps directly from natural language.
- **Tools**: Integrate **Geopandas** and **Folium** into the AI agent's environment.
- **Capabilities**: Enable the agent to recognize `geoid` or coordinate columns and automatically produce choropleth maps (e.g., California county-level production) or point-based visualizations of facilities.
- **Workflow**: Ensure the `SandboxResponseParser` can detect Folium map objects and render them interactively in the notebook.

---

## 🚩 Flagged Issues
- **Table Rendering Consistency**: While improved, some queries still return `DataFrameResponse` wrappers. We are investigating PandasAI's internal dispatching to ensure **100%** native table rendering.
- **LLM Latency**: Performance varies based on CBORG gateway load; 60s timeouts are in place to prevent hangs.

---

## 🛠️ Maintenance Commands
- **Reinstall Kernel**: `cd analysis/ai_exploration && pixi run kernel-install`
- **Verify Environment**: `cd analysis/ai_exploration && pixi run check-env`
