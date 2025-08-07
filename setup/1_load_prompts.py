import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

from mlflow_demo.agent.prompts import ORIGINAL_PROMPT_TEMPLATE

# Unity Catalog schema to store the prompt in
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')
PROMPT_NAME = os.environ.get('PROMPT_NAME')
# Exit if required environment variables are not set
if not UC_CATALOG or not UC_SCHEMA or not PROMPT_NAME:
  print('Error: UC_CATALOG, UC_SCHEMA, and PROMPT_NAME environment variables must be set')
  sys.exit(1)


import mlflow

prompt = mlflow.genai.register_prompt(
  name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
  template=ORIGINAL_PROMPT_TEMPLATE,
  commit_message='Initial email generation template',
)


print(f'added prompt to UC: {prompt.name}@{prompt.version}')

mlflow.genai.set_prompt_alias(
  name=f'{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}',
  alias='production',
  version=prompt.version,
)

print(f'added alias `production`to prompt: {prompt.name}@{prompt.version}')
