import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')


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


from datetime import datetime

import mlflow
from mlflow.genai import label_schemas


def create_labeling_schemas():
  """Create labeling schemas for human expert evaluation."""
  schemas = {}

  schema_configs = {
    'accuracy': {
      'title': 'Are all facts accurate?',
      'instruction': 'Check that all information comes from customer data with no fabrication or errors.',
      'options': [
        'All Facts Correct',
        'Some Facts Incorrect',
        'Major Errors/Fabrication',
      ],
    },
    'personalized': {
      'title': 'Is this email personalized?',
      'instruction': "Evaluate if the email is tailored to this customer's specific situation and cannot be reused for others.",
      'options': [
        'Highly Personalized',
        'Somewhat Personalized',
        'Generic/Not Personalized',
      ],
    },
    'relevance': {
      'title': 'Is the email relevant to this customer?',
      'instruction': 'Check if urgent issues are prioritized first and content follows proper importance order.',
      'options': [
        'Perfectly Focused',
        'Somewhat Focused',
        'Poorly Focused',
      ],
    },
  }

  for schema_name, config in schema_configs.items():
    try:
      schema = label_schemas.create_label_schema(
        name=schema_name,
        type='feedback',
        title=config['title'],
        input=label_schemas.InputCategorical(options=['yes', 'no']),
        instruction=config['instruction'],
        enable_comment=True,
        overwrite=True,
      )
      schemas[schema_name] = schema
      print(f'Created labeling schema: {schema_name}')

    except Exception as e:
      print(f'Error creating schema {schema_name}: {e}')

  return schemas


def create_labeling_session(schemas, session_name='email_evaluation_session'):
  """Create a labeling session for human expert review."""
  try:
    schema_names = [schema.name for schema in schemas.values()]

    session = mlflow.genai.create_labeling_session(
      name='demo_labeling_session',
      assigned_users=[],  # Add specific users as needed
      label_schemas=schema_names,
    )

    print(f'Created labeling session: {session_name}')
    return session

  except Exception as e:
    print(f'Error creating labeling session: {e}')
    return None


def add_traces_to_session(session):
  """Add traces to a labeling session and return trace IDs."""
  # Normally, you would query for the relevant traces, here we just grab 3.
  traces = mlflow.search_traces(max_results=3)
  session.add_traces(traces)
  
  # Return the first trace ID for the UI to use
  if not traces.empty:
    # Get the first trace ID from the DataFrame
    first_trace_id = traces.iloc[0]['trace_id']
    return first_trace_id
  return None


# Usage example
schemas = create_labeling_schemas()
session = create_labeling_session(schemas)
sample_trace_id = add_traces_to_session(session)

# Add traces to the session for expert review
# Experts can then access the Review App to label traces
print(f'Review App URL: {session.url}')

write_env_variable('SAMPLE_LABELING_SESSION_ID', session.labeling_session_id)
write_env_variable('SAMPLE_REVIEW_APP_URL', session.url)

# Store the sample trace ID for the UI to use
if sample_trace_id:
  write_env_variable('SAMPLE_LABELING_TRACE_ID', sample_trace_id)
  print(f'Sample trace ID for labeling: {sample_trace_id}')
