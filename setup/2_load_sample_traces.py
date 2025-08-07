import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import mlflow

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
import os

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

from mlflow_demo.agent.email_generator import EmailGenerator
from server.routes.email import FeedbackRating

PROMPT_NAME = os.getenv('PROMPT_NAME')
PROMPT_ALIAS = os.getenv('PROMPT_ALIAS')
if not PROMPT_NAME or not PROMPT_ALIAS:
  raise Exception('PROMPT_NAME and PROMPT_ALIAS environment variables must be set')
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')


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


def generate_email_for_customer(customer_data, line_num):
  """Generate email for a single customer."""
  try:
    customer_name = customer_data.get("account", {}).get("name", "Unknown")
    print(f'Processing customer {line_num}: {customer_name}')

    generator = EmailGenerator()
    user_input = customer_data.get("user_input")
    email_result = generator.generate_email_with_retrieval(customer_name, user_input)

    # Add metadata
    email_result['customer_name'] = customer_name
    email_result['line_number'] = line_num

    # add a tag so we know what is our sample data
    mlflow.set_trace_tag(trace_id=email_result['trace_id'], key='sample_data', value='yes')
    return email_result, None

  except Exception as e:
    error_msg = f'Error generating email for line {line_num}: {e}'
    print(error_msg)
    return None, error_msg


def process_input_data(input_file='input_data.jsonl', max_workers=5, max_records=50):
  """Load input_data.jsonl and run generate_email for every row in parallel.

  Args:
      input_file (str): Path to input JSONL file
      max_workers (int): Maximum number of parallel workers
  """
  script_dir = Path(__file__).parent
  input_path = script_dir / input_file

  if not input_path.exists():
    print(f'Error: Input file {input_path} not found!')
    return

  # Load all customer data first
  customers = []
  with open(input_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
      try:
        customer_data = json.loads(line.strip())
        customers.append((customer_data, line_num))
      except json.JSONDecodeError as e:
        print(f'Error parsing JSON on line {line_num}: {e}')

  if not customers:
    print('No valid customer data found!')
    return

  # limit to the max records
  customers = customers[:max_records]

  print(f'Processing {len(customers)} customers with {max_workers} workers...')

  results = []
  error_count = 0

  # Process customers in parallel
  with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all tasks
    future_to_customer = {
      executor.submit(generate_email_for_customer, customer_data, line_num): (
        customer_data,
        line_num,
      )
      for customer_data, line_num in customers
    }

    # Collect results as they complete
    for future in as_completed(future_to_customer):
      result, error = future.result()
      if result:
        results.append(result)
      if error:
        error_count += 1

  print('\nProcessing complete!')
  print(f'Total processed: {len(results)}')
  print(f'Total errors: {error_count}')


def save_trace_id_sample():
  traces = mlflow.search_traces(max_results=1, return_type='list')
  trace_id = traces[0].info.trace_id
  mlflow.log_feedback(
    trace_id=trace_id,
    name='user_feedback',
    value=True,
    rationale='I LOVE this email!',
    source=mlflow.entities.AssessmentSource(
      source_type='HUMAN',
      source_id='first.last@company.com',
    ),
  )

  write_env_variable('SAMPLE_TRACE_ID', trace_id)


if __name__ == '__main__':
  process_input_data()
  save_trace_id_sample()
