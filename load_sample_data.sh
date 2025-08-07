#!/bin/bash

# Load sample data for the MLflow evaluation demo
# This script runs the setup Python scripts to load prompts, traces, evaluations, and monitoring

set -e

echo "📊 Loading Sample Data"
echo "This script will load prompts, sample traces, evaluations, and monitoring setup"
echo ""

# Load environment variables from .env.local if it exists
if [ -f .env.local ]
then
  set -a
  source .env.local
  set +a
  echo "✅ Loaded environment variables from .env.local"
else
  echo "❌ .env.local file not found. Please run ./setup.sh first."
  exit 1
fi

# Check for required environment variables
if [ -z "$UC_CATALOG" ]
then
  echo "❌ UC_CATALOG is not set. Please run ./setup.sh to configure environment variables."
  exit 1
fi

if [ -z "$UC_SCHEMA" ]
then
  echo "❌ UC_SCHEMA is not set. Please run ./setup.sh to configure environment variables."
  exit 1
fi

if [ -z "$MLFLOW_EXPERIMENT_ID" ]
then
  echo "❌ MLFLOW_EXPERIMENT_ID is not set. Please run ./setup.sh to configure environment variables."
  exit 1
fi

# Set default profile if not specified
if [ -z "$DATABRICKS_CONFIG_PROFILE" ]
then
  DATABRICKS_CONFIG_PROFILE="DEFAULT"
fi

echo ""
echo "📋 Configuration:"
echo "  UC_CATALOG: $UC_CATALOG"
echo "  UC_SCHEMA: $UC_SCHEMA"
echo "  MLFLOW_EXPERIMENT_ID: $MLFLOW_EXPERIMENT_ID"
echo "  DATABRICKS_CONFIG_PROFILE: $DATABRICKS_CONFIG_PROFILE"
echo ""

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Change to setup directory
if [ ! -d "setup" ]; then
    echo "❌ setup directory not found. Please run this script from the project root."
    exit 1
fi

echo "🐍 Running sample data loading scripts with uv..."
echo ""

cd setup

# 1. Load prompts
echo "1️⃣ Loading prompts..."
if uv run python 1_load_prompts.py; then
    echo "✅ Prompts loaded successfully"
else
    echo "❌ Failed to load prompts"
    exit 1
fi
echo ""

# 2. Load sample traces
echo "2️⃣ Loading sample traces..."
if uv run python 2_load_sample_traces.py; then
    echo "✅ Sample traces loaded successfully"
else
    echo "❌ Failed to load sample traces"
    exit 1
fi
echo ""

# 3. Run evaluations for sample traces
echo "3️⃣ Running evaluations for sample traces..."
if uv run python 3_run_evals_for_sample_traces.py; then
    echo "✅ Evaluations completed successfully"
else
    echo "❌ Failed to run evaluations"
    exit 1
fi
echo ""

# 4. Setup monitoring
echo "4️⃣ Setting up monitoring..."
if uv run python 4_setup_monitoring.py; then
    echo "✅ Monitoring setup completed successfully"
else
    echo "❌ Failed to setup monitoring"
    exit 1
fi
echo ""

# 5. Setup labeling session
echo "5️⃣ Setting up labeling session..."
if uv run python 5_setup_labeling_session.py; then
    echo "✅ Labeling session setup completed successfully"
else
    echo "❌ Failed to setup labeling session"
    exit 1
fi
echo ""

# Return to project root
cd ..

echo "🎉 Sample data loading completed successfully!"
echo ""
echo "📋 Summary of what was loaded:"
echo "  ✅ Prompts registered in Unity Catalog"
echo "  ✅ Sample traces created in MLflow experiment"
echo "  ✅ Evaluations run on sample traces"
echo "  ✅ Monitoring configured for the experiment"
echo "  ✅ Labeling session prepared for human feedback"
echo ""
echo "🚀 Next steps:"
echo "  1. Run './watch.sh' to start development servers"
echo "  2. Open http://localhost:8000 to see your app"
echo "  3. Deploy the app to Databricks with './deploy.sh'"
