# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Configuration
# MAGIC
# MAGIC This notebook defines all configurable variables for the DC Assistant workflow. 
# MAGIC Run this notebook first, then all subsequent notebooks will automatically use these settings.
# MAGIC
# MAGIC **To customize for your workspace:** Update the variables below, then run all cells.
# MAGIC
# MAGIC - The Service Principal + Secret Scope will need to be created manually
# MAGIC - More Documentation can be found here for [secrets](https://docs.databricks.com/aws/en/security/secrets/example-secret-workflow) and here for [service principals](https://docs.databricks.com/aws/en/admin/users-groups/service-principals)

# COMMAND ----------

# MAGIC %pip install mlflow==3.9.0rc0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow

# Get the notebook path and construct experiment path
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
experiment_path = "/".join(notebook_path.split("/")[:-1])

print(f"Notebook path: {notebook_path}")
print(f"Experiment path: {experiment_path}")

# Try to get the experiment
experiment = mlflow.get_experiment_by_name(experiment_path)
print(f"\nExperiment object: {experiment}")
print(f"Type: {type(experiment)}")

# COMMAND ----------

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
experiment_path = "/".join(notebook_path.split("/")[:-1])
print(experiment_path)

# COMMAND ----------

print(experiment)

# COMMAND ----------

# MAGIC %md
# MAGIC #Set up Sources and Parameters 

# COMMAND ----------

# DBTITLE 1,Cell 3
import json
from pathlib import Path
from databricks.sdk import WorkspaceClient
import mlflow
w = WorkspaceClient() 
current_user_email = dbutils.notebook.entry_point.getDbutils().notebook().getContext().userName().get()

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
experiment_path = "/".join(notebook_path.split("/")[:-1])
experiment_name = f"{experiment_path}_experiment"

# ============================================================================
# WORKSPACE CONFIGURATION
# ============================================================================
CATALOG = "ac_demo"
SCHEMA = "dc_assistant"

# ============================================================================
# DATA COLLECTION CONFIGURATION
# ============================================================================
SEASONS = [2022, 2023, 2024]

# ============================================================================
# MLFLOW CONFIGURATION
# ============================================================================
mlflow.set_tracking_uri("databricks")

# Try to create experiment, get existing if it already exists
exp = mlflow.get_experiment_by_name(experiment_name)
if exp is None:
    EXPERIMENT_ID = mlflow.create_experiment(name=experiment_name, tags={"purpose": "football_analysis", "product": "mlflow"})
else:
    EXPERIMENT_ID = exp.experiment_id

mlflow.set_experiment(experiment_name)
print("Experiment:", experiment_name, "ID:", EXPERIMENT_ID)
    

# ============================================================================
# PROMPT REGISTRY CONFIGURATION
# ============================================================================
# We'll use the @production alias to grab the right version

PROMPT_NAME = f"{CATALOG}.{SCHEMA}.dcassistant"

# ============================================================================
# LLM ENDPOINT CONFIGURATION
# ============================================================================
LLM_ENDPOINT_NAME = "databricks-gpt-5-mini"
JUDGE_MODEL = "databricks:/databricks-gpt-5-2"  # Model used for judges/scorers
REFLECTION_MODEL = "databricks:/databricks-gpt-5-2" # Model used for GEPA optimization

# ============================================================================
# MODEL REGISTRATION CONFIGURATION
# ============================================================================
MODEL_NAME = "ac_dc_assistant"  # Note: using underscore instead of hyphen
UC_MODEL_NAME = f"{CATALOG}.{SCHEMA}.{MODEL_NAME}"

# ============================================================================
# EVALUATION DATASET CONFIGURATION
# ============================================================================
DATASET_NAME = f"{CATALOG}.{SCHEMA}.dc_assistant_eval_trace_data"
LABEL_SCHEMA_NAME = "football_analysis_base"
LABELING_SESSION_NAME = "dcassistant_eval_labeling"
ASSIGNED_USERS = [current_user_email]

# ============================================================================
# JUDGE/SCORER CONFIGURATION
# ============================================================================
ALIGNED_JUDGE_NAME = "football_analysis_judge_align"

# ============================================================================
# PROMPT OPTIMIZATION CONFIGURATION
# ============================================================================
OPTIMIZATION_DATASET_NAME = f"{CATALOG}.{SCHEMA}.dcassistant_optimization_data"

# ============================================================================
# ALIGNMENT TRACKING CONFIGURATION
# ============================================================================
ALIGNMENT_RUNS_TABLE = f"{CATALOG}.{SCHEMA}.alignment_runs"

# ============================================================================
# UNITY CATALOG TOOLS CONFIGURATION
# ============================================================================
# Base schema for all UC functions (functions are defined in 02_FunctionDefinition.ipynb)
UC_TOOLS_SCHEMA = f"{CATALOG}.{SCHEMA}"
UC_TOOL_NAMES = [
    f"{UC_TOOLS_SCHEMA}.who_got_ball_by_down_distance",
    f"{UC_TOOLS_SCHEMA}.who_got_ball_by_offense_situation",
    f"{UC_TOOLS_SCHEMA}.tendencies_by_offense_formation",
    f"{UC_TOOLS_SCHEMA}.tendencies_by_down_distance",
    f"{UC_TOOLS_SCHEMA}.tendencies_by_drive_start",
    f"{UC_TOOLS_SCHEMA}.tendencies_by_score_2nd_half",
    f"{UC_TOOLS_SCHEMA}.tendencies_two_minute_drill",
    f"{UC_TOOLS_SCHEMA}.who_got_ball_by_down_distance_and_form",
    f"{UC_TOOLS_SCHEMA}.who_got_ball_two_minute_drill",
    f"{UC_TOOLS_SCHEMA}.first_play_after_turnover",
    f"{UC_TOOLS_SCHEMA}.screen_play_tendencies",
    f"{UC_TOOLS_SCHEMA}.success_by_pass_rush_and_coverage",
]

# ============================================================================
# PROMPT REGISTRY AUTHENTICATION CONFIGURATION
# ============================================================================
# Prompt Registry requires manual authentication for deployed agents
# See: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#manual-authentication
#
# Choose ONE authentication method:
# Option 1: OAuth (recommended) - Set USE_OAUTH = True
# Option 2: PAT - Set USE_OAUTH = False
USE_OAUTH = True  # Set to False to use PAT instead

import os

# Databricks Secrets configuration
# IMPORTANT: These are KEY NAMES (identifiers) only, NOT the actual secret values!
# Override via environment variables when running in jobs/clusters to avoid hardcoding anywhere.
SECRET_SCOPE_NAME = os.getenv("DATABRICKS_SECRET_SCOPE_NAME", "dc-assistant-secrets")
SERVICE_PRINCIPAL_NAME = os.getenv("SERVICE_PRINCIPAL_NAME", "dc-assistant-secret")

# For OAuth authentication (key names only)
# See the next cell for details on how to create the secret scope and store the client ID and secret for OAuth authentication
OAUTH_CLIENT_ID_KEY = os.getenv("OAUTH_CLIENT_ID_KEY", "oauth-client-id")
OAUTH_CLIENT_SECRET_KEY = os.getenv("OAUTH_CLIENT_SECRET_KEY", "oauth-client-secret")

# For PAT authentication (key name only)
PAT_KEY = os.getenv("PAT_KEY", "databricks-pat")

# Databricks workspace URL (without trailing slash)
# Example: "https://your-workspace.cloud.databricks.com"
DATABRICKS_HOST = "https://e2-demo-field-eng.cloud.databricks.com/"  # TODO: Set your workspace URL
service_principals = list(w.service_principals.list(filter=f"displayName eq \"{SERVICE_PRINCIPAL_NAME}\""))
if service_principals:
  service_principal = service_principals[0]
  OAUTH_CLIENT_ID = service_principal.application_id

# ============================================================================
# ASSEMBLE CONFIG DICTIONARY
# ============================================================================
CONFIG = {
    "workspace": {
        "catalog": CATALOG,
        "schema": SCHEMA,
    },
    "data_collection": {
        "seasons": SEASONS,
    },
    "mlflow": {
        "experiment_id": EXPERIMENT_ID,
    },
    "prompt_registry": {
        "prompt_name": PROMPT_NAME,
        "reflection_model": REFLECTION_MODEL,
    },
    "llm": {
        "endpoint_name": LLM_ENDPOINT_NAME,
        "judge_model": JUDGE_MODEL,
    },
    "model": {
        "model_name": MODEL_NAME,
        "uc_model_name": UC_MODEL_NAME,
    },
    "evaluation": {
        "dataset_name": DATASET_NAME,
        "label_schema_name": LABEL_SCHEMA_NAME,
        "labeling_session_name": LABELING_SESSION_NAME,
        "assigned_users": ASSIGNED_USERS,
    },
    "judges": {
        "aligned_judge_name": ALIGNED_JUDGE_NAME,
    },
    "optimization": {
        "optimization_dataset_name": OPTIMIZATION_DATASET_NAME,
    },
    "alignment": {
        "alignment_runs_table": ALIGNMENT_RUNS_TABLE,
    },
    "tools": {
        "uc_tool_names": UC_TOOL_NAMES,
    },
    "prompt_registry_auth": {
        "use_oauth": USE_OAUTH,
        "secret_scope_name": SECRET_SCOPE_NAME,
        "oauth_client_id_key": OAUTH_CLIENT_ID_KEY,
        "oauth_client_secret_key": OAUTH_CLIENT_SECRET_KEY,
        "oauth_client_id": OAUTH_CLIENT_ID, 
        "pat_key": PAT_KEY,
        "databricks_host": DATABRICKS_HOST,
    },
}

# Print configuration summary
print("Configuration details created")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2
# MAGIC
# MAGIC - Confirm Service Principal and Secret Scope Creation
# MAGIC - Grant the Service Principal Access to required catalog + schema. This will enable the deployed agent to access all required instances
# MAGIC

# COMMAND ----------

# Verify secret scope exists (credentials must be created/stored via CLI/REST as documented above)
try:
    scopes = dbutils.secrets.listScopes()
    scope_exists = any(scope.name == SECRET_SCOPE_NAME for scope in scopes)
    if scope_exists:
        print(f"Secret scope '{SECRET_SCOPE_NAME}' exists")
    else:
        print(f"Secret scope '{SECRET_SCOPE_NAME}' not found. Create it via CLI/REST/UI before proceeding.")
except Exception as e:
    print(f"WARNING: Error checking secret scope: {e}") 

service_principals = list(w.service_principals.list(filter=f"displayName eq \"{SERVICE_PRINCIPAL_NAME}\""))
if service_principals:
  service_principal = service_principals[0]
  application_id = service_principal.application_id
  print(f"Application ID: {application_id}")
else:
  print(f"Service principal '{SERVICE_PRINCIPAL_NAME}' not found.")

spark.sql(f"GRANT USAGE ON CATALOG `{CATALOG}` TO `{application_id}`")
spark.sql(f"GRANT USAGE ON SCHEMA `{CATALOG}`.`{SCHEMA}` TO `{application_id}`")
spark.sql(
    f"GRANT CREATE FUNCTION, EXECUTE, MANAGE ON SCHEMA `{CATALOG}`.`{SCHEMA}` TO `{application_id}`"
)

print("Grant statements executed successfully")

# COMMAND ----------

# Create alignment tracking table for scheduled job filtering
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {ALIGNMENT_RUNS_TABLE} (
        run_id STRING COMMENT 'Unique identifier for the alignment run',
        alignment_timestamp TIMESTAMP COMMENT 'When the alignment job completed',
        traces_processed INT COMMENT 'Number of traces processed in this run',
        status STRING COMMENT 'Status of the run: SUCCESS, FAILED, SKIPPED'
    )
    COMMENT 'Tracks alignment job runs for incremental processing'
""")

print(f"Alignment tracking table ready: {ALIGNMENT_RUNS_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Save configuration to JSON file

# COMMAND ----------


config_dir = Path("config")
config_dir.mkdir(exist_ok=True)

config_file = config_dir / "dc_assistant.json"
with open(config_file, "w") as f:
    json.dump(CONFIG, f, indent=2)

print(f"Configuration saved to: {config_file.absolute()}")
print(f"\nTo load in other notebooks, use:")
print(f"  import json")
print(f"  from pathlib import Path")
print(f"  CONFIG = json.loads(Path('config/dc_assistant.json').read_text())")


# COMMAND ----------

# MAGIC %md
# MAGIC # Also create a Python module for direct import (alternative to JSON)

# COMMAND ----------


config_py = config_dir / "dc_assistant_config.py"

config_py_content = f"""# Auto-generated configuration file
# Do not edit manually - regenerate from 00_setup.ipynb

CATALOG = "{CATALOG}"
SCHEMA = "{SCHEMA}"
SEASONS = {SEASONS}
EXPERIMENT_ID = "{EXPERIMENT_ID}"
PROMPT_NAME = "{PROMPT_NAME}"
LLM_ENDPOINT_NAME = "{LLM_ENDPOINT_NAME}"
JUDGE_MODEL = "{JUDGE_MODEL}"
MODEL_NAME = "{MODEL_NAME}"
UC_MODEL_NAME = "{UC_MODEL_NAME}"
DATASET_NAME = "{DATASET_NAME}"
LABELING_SESSION_NAME = "{LABELING_SESSION_NAME}"
ASSIGNED_USERS = {ASSIGNED_USERS}
ALIGNED_JUDGE_NAME = "{ALIGNED_JUDGE_NAME}"
UC_TOOL_NAMES = {UC_TOOL_NAMES}
USE_OAUTH = {USE_OAUTH}
SECRET_SCOPE_NAME = "{SECRET_SCOPE_NAME}"
OAUTH_CLIENT_ID_KEY = "{OAUTH_CLIENT_ID_KEY}"
OAUTH_CLIENT_SECRET_KEY = "{OAUTH_CLIENT_SECRET_KEY}"
PAT_KEY = "{PAT_KEY}"
DATABRICKS_HOST = "{DATABRICKS_HOST}"
"""

with open(config_py, "w") as f:
    f.write(config_py_content)

print(f"Python config module saved to: {config_py.absolute()}")
print(f"\nTo load in other notebooks, use:")
print(f"  import sys")
print(f"  sys.path.append('config')")
print(f"  from dc_assistant_config import *")


# COMMAND ----------

