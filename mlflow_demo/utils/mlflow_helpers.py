"""MLflow utility functions for tracing and UI link generation."""

import os
from typing import Optional


def setup_local_ide_env():
  """Set up environment for local IDE development.

  Loads environment variables from .env.local and adds parent directory to path.
  """
  import sys

  from dotenv import load_dotenv

  # Load environment variables from .env.local
  load_dotenv('.env.local')

  sys.path.append('../')


def setup_databricks_notebook_env():
  """Set up environment for Databricks notebook execution.

  Configures MLflow tracking for Databricks environment and loads app.yaml variables.
  """
  import os
  import sys

  import mlflow
  import yaml

  sys.path.append('../../')

  def load_app_yaml_env_vars(file_path='../../app.yaml'):
    with open(file_path, 'r') as file:
      config = yaml.safe_load(file)

    return {item['name']: item['value'] for item in config.get('env', [])}

  # Usage
  env_vars = load_app_yaml_env_vars()

  os.environ.update(env_vars)

  mlflow.set_experiment(experiment_id=os.getenv('MLFLOW_EXPERIMENT_ID'))


def get_mlflow_experiment_id() -> Optional[str]:
  """Gets the current mlflow experiment id."""
  return os.environ.get('MLFLOW_EXPERIMENT_ID', None)


def ensure_https_protocol(host: str | None) -> str:
  """Ensure the host URL has HTTPS protocol."""
  if not host:
    return ''

  if host.startswith('https://') or host.startswith('http://'):
    return host

  return f'https://{host}'


def generate_trace_links(trace_id: str = None, print_urls: bool = True) -> tuple[str, str]:
  """Generate MLflow UI links for viewing traces."""
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))

  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

  if not databricks_host or not experiment_id:
    print('⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate links')
    return

  # General experiment traces view
  traces_url = f'{databricks_host}/ml/experiments/{experiment_id}?compareRunsMode=TRACES'

  # Specific trace view if trace_id provided
  specific_trace_url = None
  if trace_id:
    specific_trace_url = (
      f'{databricks_host}/ml/experiments/{experiment_id}/traces?selectedEvaluationId={trace_id}'
    )

  if print_urls:
    print('🔗 View in MLflow UI:')
    if specific_trace_url:
      print(f'   🎯 This Trace: {specific_trace_url}')
    else:
      print(f'   📊 All Traces: {traces_url}')

  return traces_url, specific_trace_url


def generate_evaluation_links(run_id: str = None):
  """Generate MLflow UI links for viewing evaluation runs."""
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

  if not databricks_host or not experiment_id:
    print('⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate links')
    return

  # General experiment evaluation runs view
  evaluation_runs_url = f'{databricks_host}/ml/experiments/{experiment_id}/evaluation-runs'

  # Specific evaluation run view if run_id provided
  specific_evaluation_url = None
  if run_id:
    specific_evaluation_url = (
      f'{databricks_host}/ml/experiments/{experiment_id}/evaluation-runs?selectedRunUuid={run_id}'
    )

  print('🔗 View in MLflow UI:')

  if specific_evaluation_url:
    print(f'   🎯 This Evaluation Run: {specific_evaluation_url}')
  else:
    print(f'   📊 All Evaluation Runs: {evaluation_runs_url}')


def generate_dataset_link(dataset_id: str = None, print_url: bool = False) -> str:
  """Generate MLflow UI link for viewing a specific evaluation dataset.

  Args:
    dataset_id: The dataset ID to link to
    print_url: Whether to print the URL to stdout

  Returns:
    The dataset URL
  """
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')

  if not databricks_host or not experiment_id:
    if print_url:
      print('⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate dataset link')
    return ''

  if dataset_id:
    dataset_url = (
      f'{databricks_host}/ml/experiments/{experiment_id}/datasets?selectedDatasetId={dataset_id}'
    )
  else:
    # General datasets view if no specific ID provided
    dataset_url = f'{databricks_host}/ml/experiments/{experiment_id}/datasets'

  if print_url:
    print('🔗 View evaluation dataset in MLflow UI:')
    print(f'   📊 Dataset: {dataset_url}')

  return dataset_url


def generate_prompt_link(prompt_name: Optional[str] = None, print_url: bool = True) -> str:
  """Generate MLflow UI link for viewing a prompt in the experiment's prompt registry.

  Args:
    prompt_name: The name of the prompt to link to (optional)
    print_url: Whether to print the URL to stdout

  Returns:
    The prompt URL
  """
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = os.getenv('MLFLOW_EXPERIMENT_ID')
  uc_catalog = os.getenv('UC_CATALOG')
  uc_schema = os.getenv('UC_SCHEMA')

  if not databricks_host or not experiment_id:
    if print_url:
      print('⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate prompt link')
    return ''

  if prompt_name and uc_catalog and uc_schema:
    # Full prompt path with catalog.schema.prompt_name
    full_prompt_name = f'{uc_catalog}.{uc_schema}.{prompt_name}'
    prompt_url = f'{databricks_host}/ml/experiments/{experiment_id}/prompts/{full_prompt_name}'
  elif prompt_name:
    # Just prompt name without catalog/schema
    prompt_url = f'{databricks_host}/ml/experiments/{experiment_id}/prompts/{prompt_name}'
  else:
    # General prompts view if no specific prompt provided
    prompt_url = f'{databricks_host}/ml/experiments/{experiment_id}/prompts'

  if print_url:
    print('🔗 View prompt in MLflow UI, where you can visualize the differences:')
    print(f'   📝 Prompt: {prompt_url}')

  return prompt_url


def generate_evaluation_comparison_link(
  selected_run_id: str, compare_to_run_id: str, print_url: bool = True
) -> str:
  """Generate MLflow UI link for comparing two evaluation runs side-by-side.

  Args:
    selected_run_id: The primary evaluation run ID to view
    compare_to_run_id: The evaluation run ID to compare against
    print_url: Whether to print the URL to stdout

  Returns:
    The comparison URL
  """
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = get_mlflow_experiment_id()

  if not databricks_host or not experiment_id:
    if print_url:
      print('⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate comparison link')
    return ''

  comparison_url = (
    f'{databricks_host}/ml/experiments/{experiment_id}/evaluation-runs'
    f'?selectedRunUuid={selected_run_id}&compareToRunUuid={compare_to_run_id}'
  )

  if print_url:
    print('🔗 View evaluation comparison in MLflow UI:')
    print(f'   📊 Compare Runs: {comparison_url}')

  return comparison_url


def generate_labeling_schema_link(print_url: bool = True) -> str:
  """Generate MLflow UI link for viewing labeling schemas in the experiment.

  Args:
    print_url: Whether to print the URL to stdout

  Returns:
    The labeling schema URL
  """
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = get_mlflow_experiment_id()

  if not databricks_host or not experiment_id:
    if print_url:
      print(
        '⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate labeling schema link'
      )
    return ''

  labeling_schema_url = f'{databricks_host}/ml/experiments/{experiment_id}/label-schemas'

  if print_url:
    print('🔗 View labeling schemas in MLflow UI:')
    print(f'   🏷️ Label Schemas: {labeling_schema_url}')

  return labeling_schema_url


def generate_labeling_session_link(session_id: Optional[str] = None, print_url: bool = True) -> str:
  """Generate MLflow UI link for viewing labeling sessions in the experiment.

  Args:
    session_id: The labeling session ID to link to (optional)
    print_url: Whether to print the URL to stdout

  Returns:
    The labeling session URL
  """
  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  experiment_id = get_mlflow_experiment_id()

  if not databricks_host or not experiment_id:
    if print_url:
      print(
        '⚠️ Missing DATABRICKS_HOST or MLFLOW_EXPERIMENT_ID - cannot generate labeling session link'
      )
    return ''

  if session_id:
    labeling_session_url = (
      f'{databricks_host}/ml/experiments/{experiment_id}/labeling-sessions'
      f'?selectedLabelingSessionId={session_id}'
    )
  else:
    # General labeling sessions view if no specific session ID provided
    labeling_session_url = f'{databricks_host}/ml/experiments/{experiment_id}/labeling-sessions'

  if print_url:
    print('🔗 View labeling sessions in MLflow UI:')
    print(f'   🏷️ Labeling Session: {labeling_session_url}')

  return labeling_session_url
