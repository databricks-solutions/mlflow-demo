"""Helper routes for prompts and evaluation utilities."""

import os

import mlflow
import mlflow.genai
from fastapi import APIRouter
from mlflow_demo.agent.prompts import FIXED_PROMPT_TEMPLATE, ORIGINAL_PROMPT_TEMPLATE
from mlflow_demo.evaluation.evaluator import (
  UC_CATALOG,
  UC_SCHEMA,
  validate_env_vars,
)


def ensure_https_protocol(host: str | None) -> str:
  """Ensure the host URL has HTTPS protocol."""
  if not host:
    return ''

  if host.startswith('https://') or host.startswith('http://'):
    return host

  return f'https://{host}'


router = APIRouter(prefix='/api', tags=['helper'])


@router.get('/fixed-prompt')
async def get_fixed_prompt():
  """Get the fixed prompt template for evaluation."""
  return {'prompt': FIXED_PROMPT_TEMPLATE}


@router.get('/original-prompt')
async def get_original_prompt():
  """Get the original prompt template."""
  return {'prompt': ORIGINAL_PROMPT_TEMPLATE}


@router.get('/current-production-prompt')
async def get_current_production_prompt():
  """Get the current production prompt template for evaluation."""
  PROMPT_NAME, PROMPT_ALIAS = validate_env_vars()
  baseline_prompt = mlflow.genai.load_prompt(
    f'prompts:/{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}@{PROMPT_ALIAS}'
  )
  prompt_as_string = baseline_prompt.template.replace('\\n', '\n')
  prompt_as_string = prompt_as_string[1:-1]
  return {'prompt': prompt_as_string}


# from databricks.sdk import WorkspaceClient

# w = WorkspaceClient()


def get_notebook_url(name: str) -> str:
  """Get the URL for a notebook by name."""
  # Map notebook names to environment variable names
  notebook_env_vars = {
    '1_observe_with_traces': 'NOTEBOOK_URL_1_observe_with_traces',
    '2_create_quality_metrics': 'NOTEBOOK_URL_2_create_quality_metrics',
    '3_find_fix_quality_issues': 'NOTEBOOK_URL_3_find_fix_quality_issues',
    '4_human_review': 'NOTEBOOK_URL_4_human_review',
    '5_production_monitoring': 'NOTEBOOK_URL_5_production_monitoring',
  }

  # Get the environment variable name for this notebook
  env_var_name = notebook_env_vars.get(name)
  if env_var_name:
    url = os.getenv(env_var_name)
    if url:
      return url

  # Fallback to original workspace lookup if env var not found
  # DATABRICKS_HOST = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  # LHA_SOURCE_CODE_PATH = os.getenv('LHA_SOURCE_CODE_PATH')

  # for i in w.workspace.list(f'{LHA_SOURCE_CODE_PATH}/mlflow_demo/notebooks', recursive=True):
  #   if i.path and i.path.endswith(name):
  #     return f'{DATABRICKS_HOST}/editor/notebooks/{i.resource_id}'
  return 'NOT FOUND'


@router.get('/get-notebook-url/{name}')
async def get_notebook_url_route(name: str):
  """Get the URL for a notebook by name."""
  url = get_notebook_url(name)
  return {'notebook_name': name, 'url': url}
