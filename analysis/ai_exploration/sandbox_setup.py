import os
import pandas as pd
import requests
import plotly.io as pio
from dotenv import load_dotenv
from pandasai.llm.base import LLM
import pandasai.core.response.base as response_base
from pandasai.core.response.parser import ResponseParser
from sqlalchemy import create_engine, text
from IPython.display import HTML, display
try:
    import folium
except ImportError:
    folium = None

# Set Plotly as default renderer for Jupyter
pio.renderers.default = 'notebook_connected'

# Load environment variables
load_dotenv()

class CBORGLLM(LLM):
    """Custom LLM class for CBORG (OpenAI-compatible) gateway in PandasAI 3.0"""
    def __init__(self, api_token, api_base="https://api.cborg.lbl.gov/v1", model="gemini-2.0-flash"):
        super().__init__()
        self.api_token = api_token
        self.api_base = api_base
        self.model = model

    def call(self, instruction, context=None):
        prompt = instruction.to_string()
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @property
    def type(self):
        return "cborg"

# --- GLOBAL PATCH FOR INTERACTIVE RENDERING ---
def patched_repr_html(self):
    """Ensure any response containing an HTML path or Plotly object renders in the notebook"""
    try:
        # 1. Handle direct Figure objects (Plotly)
        # Avoid calling Plotly-specific to_html on DataFrames
        if not isinstance(self.value, pd.DataFrame) and hasattr(self.value, 'to_html'):
            return self.value.to_html(include_plotlyjs='cdn', full_html=False)

        # 2. Handle DataFrames
        if isinstance(self.value, pd.DataFrame):
            return self.value._repr_html_()

        # 3. Handle HTML file paths
        if isinstance(self.value, str) and self.value.endswith('.html'):
            # Extract filename just in case it's a relative path mismatch
            fname = os.path.basename(self.value)

            # Search paths: direct, relative to CWD, relative to project root
            paths_to_try = [
                self.value,
                os.path.join(os.getcwd(), self.value),
                os.path.abspath(os.path.join(os.getcwd(), "..", "..", self.value)),
                os.path.abspath(os.path.join(os.getcwd(), "..", "..", "exports", "charts", fname))
            ]

            for path in paths_to_try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return f.read()

        # 4. Handle Folium Map objects (if folium is installed)
        if folium and isinstance(self.value, folium.Map):
            return self.value._repr_html_()

    except Exception as e:
        return f"<p style='color:red'>Rendering Error: {e}</p>"

    return None

# --- PATCH FOR VALIDATOR ---
# PandasAI 3.0 validator is too strict for interactive Plotly objects.
# We patch it to allow objects with to_html() or DataFrames to pass through.
_original_validate_response = ResponseParser._validate_response

def patched_validate_response(self, result: dict):
    if result.get("type") == "plot":
        val = result.get("value")
        # If it's a Plotly Figure or something we can render as HTML, it's valid for us
        if hasattr(val, "to_html") or hasattr(val, "_repr_html_"):
            return
    return _original_validate_response(self, result)

ResponseParser._validate_response = patched_validate_response

def init_sandbox():
    """Initializes the sandbox environment and returns the LLM and DB engine."""
    # Apply the patch to the base response class
    response_base.BaseResponse._repr_html_ = patched_repr_html
    print("PandasAI patched globally for interactive Plotly rendering.")

    api_key = os.getenv("CBORG_API_KEY")
    api_url = os.getenv("CBORG_API_URL", "https://api.cborg.lbl.gov/v1")
    model_name = os.getenv("CBORG_MODEL", "gemini-3-flash")

    if not api_key:
        raise ValueError("CBORG_API_KEY not found. Please check your .env file in analysis/ai_exploration/.")

    llm = CBORGLLM(api_token=api_key, api_base=api_url, model=model_name)
    print(f"Using model: {model_name} via {api_url}")

    DB_USER = os.getenv("DB_USER", "biocirv_user")
    DB_PASS = os.getenv("DB_PASSWORD", "biocirv_dev_password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "biocirv_db")

    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(DATABASE_URL)
    print(f"Connected to {DB_NAME}")

    return llm, engine


def fetch_table_metadata(engine, table_name, schema=None):
    """
    Fetches column names and types for a given table to provide context to the LLM.
    In the future, this can be expanded to fetch comments/descriptions.
    """
    if schema is None:
        schema = os.getenv("DB_SCHEMA", "ca_biositing")

    query = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"schema": schema, "table": table_name})
        columns = [f"{row[0]} ({row[1]})" for row in result]

    return ", ".join(columns)

def get_agent_with_metadata(llm, engine, view_names):
    """
    Creates a PandasAI agent by pre-loading DataFrames with enriched metadata.
    Includes a SQL skill to allow the agent to perform joins directly on the database.
    """
    from pandasai import skill, skills

    # In PandasAI 3.0, skills are managed globally by SkillsManager.
    # When an Agent is initialized, it automatically pulls all registered skills.

    skill_name = "execute_sql_query"
    existing_skill = next((s for s in skills._skills if s.name == skill_name), None)

    # We want to provide a list of "Authorized" tables to the LLM via the skill docstring
    authorized_tables = ", ".join([f"'{v}'" for v in view_names])

    if existing_skill is None:
        @skill
        def execute_sql_query(query: str):
            """
            Executes a SQL query against the PostgreSQL database and returns the result as a DataFrame.
            Use this for complex joins or aggregations that are more efficient in SQL.
            The schema is 'ca_biositing'.
            Available authorized tables: {authorized_tables}
            """
            # Diagnostic: Print the query being executed
            print(f"DEBUG: Executing SQL via skill: {query}")

            # 1. Clean up common LLM errors in SQL generation
            clean_query = query.replace('ca_biositing.', '') # Strip schema if LLM adds it

            # 2. Map internal table names back to real view names if the LLM used them
            # We create a mapping of any 'table_...' strings to the actual view names
            for v in view_names:
                # This is a bit of a hack, but if the LLM uses a table name that isn't one
                # of our views, we might have trouble. However, if it uses 'table_XXXX'
                # and we only have 3 views, we can try to guess or just rely on the
                # authorized_tables list in the docstring.
                pass

            # 3. Wrap query to set search_path for the transaction
            scoped_query = f"SET search_path TO {schema}, public; {clean_query}"

            try:
                with engine.connect() as conn:
                    # Use text() to ensure SQLAlchemy handles the raw SQL correctly
                    return pd.read_sql(text(scoped_query), conn)
            except Exception as e:
                print(f"DEBUG: SQL Skill Error: {e}")
                raise
    else:
        print(f"Skill '{skill_name}' already registered.")

    dataframes_dict = {}

    schema = os.getenv("DB_SCHEMA", "ca_biositing")

    from pandasai import SmartDataframe
    for view in view_names:
        try:
            df = pd.read_sql(f"SELECT * FROM {schema}.{view}", engine)
            metadata = fetch_table_metadata(engine, view)

            # CRITICAL: In PandasAI 3.0.0, we must wrap in SmartDataframe AND
            # explicitly set schema.name to bypass MaliciousQueryError.
            # Otherwise, it defaults to a randomized 'table_XXXX' string.
            sdf = SmartDataframe(df, name=view, description=f"Table {view} containing columns: {metadata}")
            sdf.schema.name = view

            dataframes_dict[view] = sdf
            print(f"- Loaded {view}: {len(df)} rows")
            print(f"  Metadata: {metadata}")
        except Exception as e:
            print(f"- Error loading {view}: {e}")

    if not dataframes_dict:
        raise RuntimeError("No dataframes could be loaded. Ensure the database services are running and accessible.")

    from pandasai import Agent
    # The Agent constructor pulls skills from the global SkillsManager.
    # Passing dataframes as a dictionary ensures authorization for those names.
    # Pass the dictionary of SmartDataframes to the Agent
    # In 3.0.0, the most stable way to handle multiple tables with custom names
    # is to pass the list of SmartDataframes, ensuring they share the same config.
    agent_config = {
        "llm": llm,
        "verbose": True,
        "enforce_privacy": False,
        "enable_cache": False,
        "use_error_correction_framework": True,
        "custom_whitelisted_dependencies": ["sqlalchemy", "psycopg2"]
    }

    # Update SmartDataframes with the global config before passing to Agent
    for sdf in dataframes_dict.values():
        sdf._config = agent_config

    # In 3.0.0, passing list(SmartDataframes) is the standard way.
    # However, to avoid the 'dict object' error during prompt serialization,
    # we ensure the Agent sees these as its primary data sources.
    agent = Agent(
        list(dataframes_dict.values()),
        config=agent_config
    )

    # Log state for debugging UndefinedError and MaliciousQueryError
    print(f"DEBUG: Agent initialized with {len(agent._state.dfs)} dataframes.")
    for i, df_obj in enumerate(agent._state.dfs):
        # In 3.0.0, df_obj should be a SmartDataframe or similar
        name = getattr(df_obj, 'name', 'N/A')
        schema_name = getattr(getattr(df_obj, 'schema', None), 'name', 'N/A')
        print(f"  df[{i}] type: {type(df_obj)}, name: {name}, schema.name: {schema_name}")

    return agent
