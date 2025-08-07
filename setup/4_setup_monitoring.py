import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

import os

from mlflow_demo.evaluation.evaluator import SCORERS
from mlflow.genai.scorers import ScorerSamplingConfig
from mlflow.genai.scorers import get_scorer, delete_scorer

# UNCOMMENT THIS


# These packages are automatically installed with mlflow[databricks]
from databricks.agents.monitoring import (
  create_external_monitor,
)


# Unity Catalog schema to store the prompt in
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')
# Exit if required environment variables are not set
if not UC_CATALOG or not UC_SCHEMA:
  print('Error: UC_CATALOG and UC_SCHEMA environment variables must be set')
  sys.exit(1)


# # Enable sync of traces to a delta table
# external_monitor = create_external_monitor(
#   # Change to a Unity Catalog schema where you have CREATE TABLE permissions.
#   catalog_name=UC_CATALOG,
#   schema_name=UC_SCHEMA,
#   assessments_config={},
# )

for scorer in SCORERS:
  # Register each scorer with MLflow
  try:
    scorer.register()
  except Exception as e:
    print(f'⚠️ Warning: Scorer {scorer.name} registration failed or already exists: {e}')
    print('   Attempting to re-register by deleting existing scorer...')
    delete_scorer(name=scorer.name)
    scorer.register()

  scorer.start(sampling_config=ScorerSamplingConfig(sample_rate=1))



