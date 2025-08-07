import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()


def ensure_https_protocol(host: str | None) -> str:
  """Ensure the host URL has HTTPS protocol."""
  if not host:
    return ''

  if host.startswith('https://') or host.startswith('http://'):
    return host

  return f'https://{host}'


def get_notebook_url(name: str) -> str:
  """Get the URL for a notebook by name."""
  DATABRICKS_HOST = ensure_https_protocol(os.getenv('DATABRICKS_HOST')).rstrip('/')
  LHA_SOURCE_CODE_PATH = os.getenv('LHA_SOURCE_CODE_PATH')

  for i in w.workspace.list(f'{LHA_SOURCE_CODE_PATH}/mlflow_demo/notebooks', recursive=True):
    if i.path and i.path.endswith(name):
      return f'{DATABRICKS_HOST}/editor/notebooks/{i.resource_id}'
  return 'NOT FOUND'


notebooks = [
  '1_observe_with_traces',
  '2_create_quality_metrics',
  '3_find_fix_quality_issues',
  '4_human_review',
  '5_production_monitoring',
]

env_vars = []
for notebook in notebooks:
  url = get_notebook_url(notebook)
  var_name = f'NOTEBOOK_URL_{notebook}'
  env_vars.append(f'{var_name}={url}')
  print(f'{var_name}={url}')

# Update .env.local
with open('.env.local', 'r') as f:
  lines = f.readlines()

# Remove existing notebook URL variables
lines = [line for line in lines if not line.startswith('NOTEBOOK_URL_')]

# Add new notebook URL variables
for env_var in env_vars:
  lines.append(f'{env_var}\n')

with open('.env.local', 'w') as f:
  f.writelines(lines)
