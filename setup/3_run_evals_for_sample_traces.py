import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

import mlflow
from mlflow.entities import DatasetInput, LoggedModelInput

# Unity Catalog schema to store the prompt in
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')
PROMPT_ALIAS = os.environ.get('PROMPT_ALIAS')
PROMPT_NAME = os.environ.get('PROMPT_NAME')


# Exit if required environment variables are not set
if not UC_CATALOG or not UC_SCHEMA or not PROMPT_ALIAS or not PROMPT_NAME:
  print(
    'Error: UC_CATALOG, UC_SCHEMA, PROMPT_ALIAS, and PROMPT_NAME environment variables must be set'
  )
  sys.exit(1)

import json

from databricks.sdk import WorkspaceClient
from mlflow import MlflowClient
from mlflow.genai.datasets import create_dataset, get_dataset
from mlflow_demo.agent.prompts import FIXED_PROMPT_TEMPLATE
# Constants moved from server/routes/run_eval.py
FIX_DATASET_NAME = 'low_accuracy'
REGRESSION_DATASET_NAME = 'regression_set'

# Import the new scorers from the updated evaluator module
from mlflow_demo.evaluation.evaluator import SCORERS, DEV_PROMPT_ALIAS
# Evaluation functions moved here from task_runner.py
from datetime import datetime
from typing import Dict, Any
from mlflow_demo.agent.email_generator import EmailGenerator
from mlflow_demo.utils.mlflow_helpers import get_mlflow_experiment_id, ensure_https_protocol




def run_single_evaluation(dataset_name, prompt_alias, eval_run_name):
  dataset = mlflow.genai.datasets.get_dataset(
      uc_table_name=f'{UC_CATALOG}.{UC_SCHEMA}.{dataset_name}',
    )

  generator_new = EmailGenerator(prompt_alias=prompt_alias)
  def predict_fn_new(customer_name: str , user_input: str) -> Dict[str, Any]:
      return generator_new.generate_email_with_retrieval(customer_name, user_input)

  # Run evaluations
  print('Running evaluation...')
  with mlflow.start_run(run_name=f'{eval_run_name}') as run:
      eval_results = mlflow.genai.evaluate(
          data=dataset,
          predict_fn=predict_fn_new,
          scorers=SCORERS,
      )

  return eval_results.run_id


def register_new_prompt():
  # Register the new prompt and set alias
  print('Registering new prompt...')
  new_prompt = mlflow.genai.register_prompt(
      name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
      template=FIXED_PROMPT_TEMPLATE,
      commit_message='New email generation prompt to fix accuracy issues.',
  )

  mlflow.genai.set_prompt_alias(
      name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
      alias=DEV_PROMPT_ALIAS,
      version=new_prompt.version,
  )


def run_both_evals():
  register_new_prompt()

  run_id_low_accuracy = run_single_evaluation(
      dataset_name=FIX_DATASET_NAME,
      prompt_alias=DEV_PROMPT_ALIAS,
      eval_run_name='low_accuracy_new_prompt',
  )
  print(f'Low accuracy eval run ID: {run_id_low_accuracy}')

  run_id_regression = run_single_evaluation(
      dataset_name=REGRESSION_DATASET_NAME,
      prompt_alias=DEV_PROMPT_ALIAS,
      eval_run_name='regression_new_prompt',
  )
  print(f'Regression eval run ID: {run_id_regression}')

  low_accuracy_results_original_run_id = os.getenv('FIX_QUALITY_BASELINE_RUN_ID')
  regression_results_original_run_id = os.getenv('REGRESSION_BASELINE_RUN_ID')


  import mlflow

  if mlflow.utils.databricks_utils.is_in_databricks_notebook():
    databricks_host = ensure_https_protocol(mlflow.utils.databricks_utils.get_browser_hostname())
  else:
    databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))

  write_env_variable('LOW_ACCURACY_RESULTS_URL', f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-runs?selectedRunUuid={run_id_low_accuracy}&compareToRunUuid={low_accuracy_results_original_run_id}')
  write_env_variable('REGRESSION_RESULTS_URL', f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-runs?selectedRunUuid={run_id_regression}&compareToRunUuid={regression_results_original_run_id}')




# def run_simple_evaluation(eval_request_dict: Dict[str, Any]) -> Dict[str, Any]:
#     """Run simple evaluation with custom guidelines and builtin judges."""
#     try:
#         print('Loading traces...')
#         traces = mlflow.search_traces(
#             max_results=5,
#             filter_string='attributes.status = "OK"',
#             order_by=['attributes.timestamp_ms DESC'],
#         )

#         if len(traces) == 0:
#             print('No traces found, generating some sample traces first...')
#             # Generate a few sample traces for testing
#             generator = EmailGenerator()
#             for i in range(3):
#                 result = generator.generate_email_with_retrieval(
#                     f"Test Customer {i+1}",
#                     "Generate a sample email for testing"
#                 )
#                 print(f"Generated trace: {result.get('trace_id')}")

#             # Search again
#             traces = mlflow.search_traces(
#                 max_results=5,
#                 filter_string='attributes.status = "OK"',
#                 order_by=['attributes.timestamp_ms DESC'],
#             )

#         print(f'Found {len(traces)} traces for evaluation')

#         # # Use the new custom scorers from evaluator module
#         # scorers = []

#         # # Add our custom email-specific scorers that extract email body content
#         # scorers.extend([tone, accuracy, personalized, relevance, email_is_grounded])

#         # # Add any additional custom guidelines scorers if provided
#         # for item in eval_request_dict.get('guidelines', []):
#         #     scorers.append(Guidelines(name=item['name'], guidelines=item['guideline']))

#         # # Add builtin judges
#         # builtin_scorer_map = {
#         #     'RelevanceToQuery': RelevanceToQuery(),
#         #     'Safety': Safety()
#         # }

#         # for judge_name in eval_request_dict.get('builtin_judges', []):
#         #     if judge_name in builtin_scorer_map:
#         #         scorers.append(builtin_scorer_map[judge_name])

#         generator = EmailGenerator()
#         def predict_fn(customer_name: str , user_input: str) -> Dict[str, Any]:
#             return generator.generate_email_with_retrieval(customer_name, user_input)

#         # Run the evaluation
#         print('Running evaluation...')
#         with mlflow.start_run(
#             run_name=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_test_judges'
#         ) as run:
#             results = mlflow.genai.evaluate(
#                 data=traces,
#                 predict_fn=predict_fn,
#                 scorers=SCORERS,
#             )

#         databricks_host = ensure_https_protocol(os.environ.get('DATABRICKS_HOST'))

#         result = {
#             'status': 'completed',
#             'completed_at': datetime.now().isoformat(),
#             'results': {
#                 'results_url': f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-runs?selectedRunUuid={results.run_id}',
#                 'run_id': results.run_id,
#             },
#             'error': None,
#         }

#         print('✅ Evaluation completed successfully')
#         return result

#     except Exception as e:
#         error_result = {
#             'status': 'failed',
#             'completed_at': datetime.now().isoformat(),
#             'results': None,
#             'error': str(e),
#         }

#         print(f'❌ Evaluation failed: {e}')
#         return error_result




# def run_evaluation_suite(prompt_template: str) -> Dict[str, Any]:
#     """Run the complete evaluation suite with a new prompt."""
#     try:
#         # Import evaluation constants
#         PROMPT_NAME = os.environ.get('PROMPT_NAME')
#         PROMPT_ALIAS = os.environ.get('PROMPT_ALIAS')

#         if not all([PROMPT_NAME, PROMPT_ALIAS, UC_CATALOG, UC_SCHEMA]):
#             raise Exception('Missing required environment variables for prompt registry')

#         DEV_PROMPT_ALIAS = 'development'
#         TIMESTAMP = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}'

#         # Use the new custom scorers from evaluator module
#         # eval_scorers = [tone, accuracy, personalized, relevance, email_is_grounded]

#         # Register the new prompt and set alias
#         print('Registering new prompt...')
#         new_prompt = mlflow.genai.register_prompt(
#             name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
#             template=prompt_template,
#             commit_message='New email generation prompt to fix accuracy issues.',
#         )

#         mlflow.genai.set_prompt_alias(
#             name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
#             alias=DEV_PROMPT_ALIAS,
#             version=new_prompt.version,
#         )

#         # Get some test data (using recent traces as test data)
#         print('Loading test data...')
#         traces = mlflow.search_traces(
#             max_results=3,
#             filter_string='attributes.status = "OK"',
#             order_by=['attributes.timestamp_ms DESC'],
#         )

#         if len(traces) == 0:
#             print('No traces found for testing - generating sample data')
#             # Create minimal test data
#             test_data = [
#                 {
#                     'account': {'name': 'Test Company 1'},
#                     'user_input': 'Write a professional follow-up email'
#                 },
#                 {
#                     'account': {'name': 'Test Company 2'},
#                     'user_input': 'Schedule a demo meeting'
#                 }
#             ]
#         else:
#             test_data = traces


#         generator_new = EmailGenerator(prompt_alias=DEV_PROMPT_ALIAS)
#         def predict_fn_new(customer_name: str , user_input: str) -> Dict[str, Any]:

#             return generator_new.generate_email_with_retrieval(customer_name, user_input)

#         generator_orig = EmailGenerator(prompt_alias=PROMPT_ALIAS)
#         def predict_fn_original(customer_name: str , user_input: str) -> Dict[str, Any]:
#             return generator_orig.generate_email_with_retrieval(customer_name, user_input)

#         # Run evaluations
#         print('Running new prompt evaluation...')
#         with mlflow.start_run(run_name=f'low_accuracy_new_prompt') as run:
#             new_results = mlflow.genai.evaluate(
#                 data=test_data,
#                 predict_fn=predict_fn_new,
#                 scorers=SCORERS,
#             )

#         # print('Running original prompt evaluation...')
#         # with mlflow.start_run(run_name=f'{TIMESTAMP}_original_prompt') as run:
#         #     original_results = mlflow.genai.evaluate(
#         #         data=test_data,
#         #         predict_fn=predict_fn_original,
#         #         scorers=SCORERS,
#         #     )

#         databricks_host = ensure_https_protocol(os.environ.get('DATABRICKS_HOST'))

#         result = {
#             'status': 'completed',
#             'completed_at': datetime.now().isoformat(),
#             'results': {
#                 'new_prompt_url': f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-runs?selectedRunUuid={new_results.run_id}',
#                 'comparison_url': f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-runs?selectedRunUuid={new_results.run_id}&compareToRunUuid={original_results.run_id}',
#                 'new_run_id': new_results.run_id,
#                 'original_run_id': original_results.run_id,
#             },
#             'error': None,
#         }

#         print('✅ Evaluation suite completed successfully')
#         return result

#     except Exception as e:
#         error_result = {
#             'status': 'failed',
#             'completed_at': datetime.now().isoformat(),
#             'results': None,
#             'error': str(e),
#         }

#         print(f'❌ Evaluation suite failed: {e}')
#         return error_result


def write_env_variable(key, value):
  """Write or update a variable in .env.local file."""
  env_file = project_root / '.env.local'

  # Read existing content
  lines = []
  if env_file.exists():
    with open(env_file, 'r') as f:
      lines = f.readlines()

  # Find if variable already exists
  updated = False
  for i, line in enumerate(lines):
    if line.strip().startswith(f'{key}='):
      lines[i] = f'{key}="{value}"\n'
      updated = True
      break

  # If variable doesn't exist, append it
  if not updated:
    lines.append(f'{key}="{value}"\n')

  # Write back to file
  with open(env_file, 'w') as f:
    f.writelines(lines)

  print(f'✅ Updated {key} in .env.local')


def add_all_evals():
  traces = mlflow.search_traces()

  # load evals for all records
  traces = mlflow.search_traces()

  with mlflow.start_run(run_name='load_all_evals'):
    load_evals = mlflow.genai.evaluate(
      data=traces,
      scorers=SCORERS,
    )

  mlflow.delete_run(run_id=load_evals.run_id)


# def create_metrics_test_eval_run():
#   print('Creating metrics test eval run...')
#   # Use the new scorers instead of guidelines dict
#   results = run_simple_evaluation(
#     eval_request_dict={
#       'guidelines': [],  # Empty since we're using the new custom scorers
#       'builtin_judges': [],
#     }
#   )

#   metrics_result_url = results.get('results', {}).get('results_url')
#   # print(metrics_result_url)

#   # Write metrics result URL to .env.local
#   if metrics_result_url:
#     write_env_variable('METRICS_RESULT_URL', metrics_result_url)
#   else:
#     raise Exception('No result URL found')


# def run_new_prompt_eval():
#   print('Running new prompt eval...')
#   results = run_evaluation_suite(FIXED_PROMPT_TEMPLATE)

#   new_prompt_url = results.get('results', {}).get('new_prompt_url')
#   comparison_url = results.get('results', {}).get('comparison_url')

#   print(new_prompt_url)
#   print(comparison_url)

#   # Write evaluation result URLs to .env.local
#   if new_prompt_url and comparison_url:
#     write_env_variable('NEW_PROMPT_EVAL_URL', new_prompt_url)
#     write_env_variable('PROMPT_COMPARISON_URL', comparison_url)
#   else:
#     raise Exception('No result URL found')




def run_new_prompt_eval():
  print('Running new prompt eval...')
  run_evaluation_suite(FIXED_PROMPT_TEMPLATE, '/tmp/results_prompt_test.json')
  results = json.load(open('/tmp/results_prompt_test.json'))

  low_accuracy_results_url = results.get('results').get('low_accuracy_results_url')
  regression_results_url = results.get('results').get('regression_results_url')

  print(low_accuracy_results_url)
  print(regression_results_url)

  # Write evaluation result URLs to .env.local
  if low_accuracy_results_url and regression_results_url:
    write_env_variable('LOW_ACCURACY_RESULTS_URL', low_accuracy_results_url)
    write_env_variable('REGRESSION_RESULTS_URL', regression_results_url)
  else:
    raise Exception('No result URL found')

def add_traces_to_run(run_id: str, trace_ids: list[str]):
  w._api_client.do(
    'POST',
    '/api/2.0/mlflow/traces/link-to-run',
    body={'run_id': run_id, 'trace_ids': trace_ids},
  )


def create_and_add_fix_quality_dataset():
  dataset = create_dataset(
    uc_table_name=f'{UC_CATALOG}.{UC_SCHEMA}.{FIX_DATASET_NAME}',
  )
  traces = mlflow.search_traces(filter_string='tags.eval_example = "yes"')
  dataset.merge_records(traces)
  return get_dataset(uc_table_name=f'{UC_CATALOG}.{UC_SCHEMA}.{FIX_DATASET_NAME}')


def create_and_add_dataset_regression():
  dataset = create_dataset(
    uc_table_name=f'{UC_CATALOG}.{UC_SCHEMA}.{REGRESSION_DATASET_NAME}',
  )
  traces = mlflow.search_traces(filter_string='tags.eval_example = "regression"')
  dataset.merge_records(traces)
  return get_dataset(uc_table_name=f'{UC_CATALOG}.{UC_SCHEMA}.{REGRESSION_DATASET_NAME}')


def make_eval_datasets_and_baseline_runs_for_prompt_test():
  # get all traces
  traces = mlflow.search_traces(return_type='list', filter_string='tags.sample_data = "yes"')

  failed_accuracy = []
  passed_all = []

  MLFLOW_EXPERIMENT_ID = os.getenv('MLFLOW_EXPERIMENT_ID')

  print('Finding traces for eval and regression datasets...')
  for trace in traces:
    number_passes = 0
    if len(trace.info.assessments) == 0:
      print(f'no assessments for {trace.info.trace_id}, deleting it')
      # print(trace.info.experiment_id)
      client.delete_traces(experiment_id=trace.info.experiment_id, trace_ids=[trace.info.trace_id])
    for assessment in trace.info.assessments:
      if assessment.name == 'accuracy' and assessment.feedback.value == 'no':
        if len(failed_accuracy) < 5:
          failed_accuracy.append(trace.info.trace_id)
          # print(f'failed accuracy: {trace.info.trace_id}')
      elif assessment.name == 'relevance' and assessment.feedback.value == 'yes':
        number_passes += 1
      elif assessment.name == 'personalized' and assessment.feedback.value == 'yes':
        number_passes += 1
      elif assessment.name == 'accuracy' and assessment.feedback.value == 'yes':
        number_passes += 1
    if number_passes == 3:
      if len(passed_all) < 5:
        passed_all.append(trace.info.trace_id)
        # print(f'passed all: {trace.info.trace_id}')

  print(
    f'Found {len(failed_accuracy)} traces for low accuracy and {len(passed_all)} traces for regression, adding tags'
  )
  for trace_id in failed_accuracy:
    mlflow.set_trace_tag(trace_id=trace_id, key='eval_example', value='yes')

  for trace_id in passed_all:
    mlflow.set_trace_tag(trace_id=trace_id, key='eval_example', value='regression')

  print('Creating and adding traces to eval datasets...')
  fix_quality_dataset = create_and_add_fix_quality_dataset()
  regression_dataset = create_and_add_dataset_regression()

  print('Creating evaluation runs...')

  active_model = mlflow.set_active_model(name=f'{PROMPT_NAME}@{PROMPT_ALIAS}@v1')

  regression_baseline_run = client.create_run(
    experiment_id=MLFLOW_EXPERIMENT_ID, run_name='regression_original_prompt'
  )

  mlflow.start_run(run_id=regression_baseline_run.info.run_id)

  add_traces_to_run(regression_baseline_run.info.run_id, trace_ids=passed_all)

  client.log_inputs(
    run_id=regression_baseline_run.info.run_id,
    datasets=[DatasetInput(regression_dataset._to_mlflow_entity())],
    models=[LoggedModelInput(model_id=active_model.model_id)],
  )

  mlflow.end_run()

  fix_quality_baseline_run = client.create_run(
    experiment_id=MLFLOW_EXPERIMENT_ID, run_name='low_accuracy_original_prompt'
  )

  mlflow.start_run(run_id=fix_quality_baseline_run.info.run_id)

  add_traces_to_run(fix_quality_baseline_run.info.run_id, trace_ids=failed_accuracy)

  client.log_inputs(
    run_id=fix_quality_baseline_run.info.run_id,
    datasets=[DatasetInput(fix_quality_dataset._to_mlflow_entity())],
    models=[LoggedModelInput(model_id=active_model.model_id)],
  )

  mlflow.end_run()

  print('Writing run IDs to env variables...')

  write_env_variable('REGRESSION_BASELINE_RUN_ID', regression_baseline_run.info.run_id)
  write_env_variable('FIX_QUALITY_BASELINE_RUN_ID', fix_quality_baseline_run.info.run_id)

  # reload these env vars for use by the backend in running example evals
  dotenv.load_dotenv(project_root / '.env.local')

LATEST_TRACE_EVALUATION_TIMESTAMP_MS_TAG = "mlflow.latestTraceEvaluationTimestampMs"

def tag_experiment_to_not_run_monitoring():
  """Set the monitoring tag so that monitoring job doesn't rerun evals on the traces we just evaluated above"""
  traces = mlflow.search_traces(return_type='list')
  latest_timestamp_ms = max(trace.info.timestamp_ms for trace in traces)

  client.set_experiment_tag(experiment_id=os.getenv('MLFLOW_EXPERIMENT_ID'), key=LATEST_TRACE_EVALUATION_TIMESTAMP_MS_TAG, value=str(latest_timestamp_ms))


if __name__ == '__main__':
  w = WorkspaceClient()

  client = MlflowClient()
  add_all_evals()
  make_eval_datasets_and_baseline_runs_for_prompt_test()

  run_both_evals()
  tag_experiment_to_not_run_monitoring()
