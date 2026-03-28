# Handoff: AI Sandbox Resolution & Hardening (Phase 2 Completed)

**Objective:** Resolve the persistent `ModuleNotFoundError` in the AI
Exploration notebooks and align the environment with **PandasAI 3.0**
architecture.

## Implementation Summary

### 1. Environment & Kernel Stability

- **Kernel Registration**: Formally registered the `ai-exploration` Pixi
  environment as a Jupyter kernel.
  - **Display Name**: `Python (AI Exploration)`
  - **Command**: `pixi run kernel-install`
- **Robust Path Discovery**: Refactored the first cell of
  `sandbox_exploration.ipynb` and `ai_analysis.ipynb` to dynamically find
  `sandbox_setup.py`. It now injects the absolute path into `sys.path`
  regardless of whether the notebook is opened from the project root or the
  sub-directory.

### 2. PandasAI 3.0 API Alignment

- **Import Migration**: Fixed
  `ModuleNotFoundError: No module named 'pandasai.skills'` by migrating to the
  new PandasAI 3.0 pattern: `from pandasai import skill`.
- **Global Skill Management**: In 3.0, the `Agent` class automatically inherits
  all skills registered in the global `SkillsManager`.
  - **Removed**: `agent.add_skills(skill_to_add)` (which was causing an
    `AttributeError`).
  - **Fixed**: Updated `sandbox_setup.py` to check the global `SkillsManager`
    before registering `execute_sql_query` to prevent
    `ValueError: Skill ... already exists` on notebook re-runs.

### 3. Error Handling & Hardening

- **DB Connection Safety**: Added explicit checks in `get_agent_with_metadata`
  to catch database connection failures. It now raises a descriptive
  `RuntimeError` if no dataframes can be loaded (e.g., if Docker services are
  down).
- **Interactive Patching**: Maintained the global patch for interactive Plotly
  rendering to ensure charts display correctly in the notebook environment.

## Current State of `analysis/ai_exploration/`

- **Architecture**: `sandbox_setup.py` is the single source of truth for
  initialization.
- **Environment**: Managed by its own `pixi.toml`. Dependencies include
  `pandasai`, `plotly`, `sqlalchemy`, and `psycopg2-binary`.
- **Notebooks**: Fully updated with diagnostic prints (`sys.executable`,
  `os.getcwd()`) to verify the environment at runtime.

## Issues to Monitor

- **LLM Latency**: During testing, some queries via the CBORG gateway may
  experience significant latency or timeouts depending on the model and gateway
  load.
- **Docker Dependency**: The sandbox requires the PostgreSQL database to be
  running (`pixi run start-services` from the root).

## Reference Files

- [`analysis/ai_exploration/sandbox_setup.py`](analysis/ai_exploration/sandbox_setup.py):
  Core initialization and custom skills.
- [`analysis/ai_exploration/pixi.toml`](analysis/ai_exploration/pixi.toml):
  Standalone environment definition.
- [`analysis/ai_exploration/sandbox_exploration.ipynb`](analysis/ai_exploration/sandbox_exploration.ipynb):
  Hardened testing notebook.
