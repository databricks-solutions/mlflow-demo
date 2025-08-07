# Deploy the Lakehouse App.
# For configuration options see README.md and .env.local.

set -e

# Load environment variables from .env.local if it exists.
if [ -f .env.local ]
then
  set -a
  source .env.local
  set +a
fi

# If LHA_SOURCE_CODE_PATH is not set throw an error.
if [ -z "$LHA_SOURCE_CODE_PATH" ]
then
  echo "LHA_SOURCE_CODE_PATH is not set. Please set to the /Workspace/Users/{username}/{lha-name} in .env.local."
  exit 1
fi

if [ -z "$DATABRICKS_APP_NAME" ]
then
  echo "DATABRICKS_APP_NAME is not set. Please set to the name of the app in .env.local."
  exit 1
fi

if [ -z "$DATABRICKS_CONFIG_PROFILE" ]
then
  DATABRICKS_CONFIG_PROFILE="DEFAULT"
fi

mkdir -p client/build

# Generate requirements.txt from pyproject.toml preserving version ranges
uv run python scripts/generate_semver_requirements.py



# Backup current app.yaml and use template
mv app.yaml app.yaml.previous
cp app.yaml.template app.yaml

# Update app.yaml with MLFLOW_EXPERIMENT_ID from .env.local
if [ -n "$MLFLOW_EXPERIMENT_ID" ]; then
  echo "🔧 Setting MLFLOW_EXPERIMENT_ID to $MLFLOW_EXPERIMENT_ID in app.yaml..."
  sed -i.bak "s/value: 'your-experiment-id'/value: '$MLFLOW_EXPERIMENT_ID'/" app.yaml
  rm -f app.yaml.bak
else
  echo "⚠️  MLFLOW_EXPERIMENT_ID not found in environment"
fi

# Update app.yaml with evaluation result URLs from .env.local
if [ -n "$LOW_ACCURACY_RESULTS_URL" ]; then
  echo "🔧 Setting LOW_ACCURACY_RESULTS_URL in app.yaml..."
  ESCAPED_URL=$(echo "$LOW_ACCURACY_RESULTS_URL" | sed 's/&/\\&/g')
  sed -i.bak "s|value: 'placeholder-low-accuracy-url'|value: '$ESCAPED_URL'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$REGRESSION_RESULTS_URL" ]; then
  echo "🔧 Setting REGRESSION_RESULTS_URL in app.yaml..."
  ESCAPED_URL=$(echo "$REGRESSION_RESULTS_URL" | sed 's/&/\\&/g')
  sed -i.bak "s|value: 'placeholder-regression-url'|value: '$ESCAPED_URL'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$METRICS_RESULT_URL" ]; then
  echo "🔧 Setting METRICS_RESULT_URL in app.yaml..."
  ESCAPED_URL=$(echo "$METRICS_RESULT_URL" | sed 's/&/\\&/g')
  sed -i.bak "s|value: 'placeholder-metrics-url'|value: '$ESCAPED_URL'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$LHA_SOURCE_CODE_PATH" ]; then
  echo "🔧 Setting LHA_SOURCE_CODE_PATH in app.yaml..."
  ESCAPED_PATH=$(echo "$LHA_SOURCE_CODE_PATH" | sed 's/&/\\&/g')
  sed -i.bak "s|value: 'placeholder-lha-source-code-path'|value: '$ESCAPED_PATH'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$LLM_MODEL" ]; then
  echo "🔧 Setting LLM_MODEL to $LLM_MODEL in app.yaml..."
  sed -i.bak "s/value: 'placeholder-llm-model'/value: '$LLM_MODEL'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$UC_CATALOG" ]; then
  echo "🔧 Setting UC_CATALOG to $UC_CATALOG in app.yaml..."
  sed -i.bak "s/value: 'placeholder-uc-catalog'/value: '$UC_CATALOG'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$UC_SCHEMA" ]; then
  echo "🔧 Setting UC_SCHEMA to $UC_SCHEMA in app.yaml..."
  sed -i.bak "s/value: 'placeholder-uc-schema'/value: '$UC_SCHEMA'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$MLFLOW_ENABLE_ASYNC_TRACE_LOGGING" ]; then
  echo "🔧 Setting MLFLOW_ENABLE_ASYNC_TRACE_LOGGING to $MLFLOW_ENABLE_ASYNC_TRACE_LOGGING in app.yaml..."
  sed -i.bak "s/value: 'placeholder-async-logging'/value: '$MLFLOW_ENABLE_ASYNC_TRACE_LOGGING'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$PROMPT_NAME" ]; then
  echo "🔧 Setting PROMPT_NAME to $PROMPT_NAME in app.yaml..."
  sed -i.bak "s/value: 'placeholder-prompt-name'/value: '$PROMPT_NAME'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$SAMPLE_LABELING_SESSION_ID" ]; then
  echo "🔧 Setting SAMPLE_LABELING_SESSION_ID to $SAMPLE_LABELING_SESSION_ID in app.yaml..."
  sed -i.bak "s/value: 'placeholder-sample-labeling-session-id'/value: '$SAMPLE_LABELING_SESSION_ID'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$SAMPLE_REVIEW_APP_URL" ]; then
  echo "🔧 Setting SAMPLE_REVIEW_APP_URL to $SAMPLE_REVIEW_APP_URL in app.yaml..."
  ESCAPED_URL=$(echo "$SAMPLE_REVIEW_APP_URL" | sed 's/&/\\&/g')
  sed -i.bak "s|value: 'placeholder-sample-review-app-url'|value: '$ESCAPED_URL'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$SAMPLE_LABELING_TRACE_ID" ]; then
  echo "🔧 Setting SAMPLE_LABELING_TRACE_ID to $SAMPLE_LABELING_TRACE_ID in app.yaml..."
  sed -i.bak "s/value: 'placeholder-sample-labeling-trace-id'/value: '$SAMPLE_LABELING_TRACE_ID'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$SAMPLE_TRACE_ID" ]; then
  echo "🔧 Setting SAMPLE_TRACE_ID to $SAMPLE_TRACE_ID in app.yaml..."
  sed -i.bak "s/value: 'placeholder-sample-trace-id'/value: '$SAMPLE_TRACE_ID'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$PROMPT_ALIAS" ]; then
  echo "🔧 Setting PROMPT_ALIAS to $PROMPT_ALIAS in app.yaml..."
  sed -i.bak "s/value: 'placeholder-prompt-alias'/value: '$PROMPT_ALIAS'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$REGRESSION_BASELINE_RUN_ID" ]; then
  echo "🔧 Setting REGRESSION_BASELINE_RUN_ID to $REGRESSION_BASELINE_RUN_ID in app.yaml..."
  sed -i.bak "s/value: 'placeholder-regression-baseline-run-id'/value: '$REGRESSION_BASELINE_RUN_ID'/" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$FIX_QUALITY_BASELINE_RUN_ID" ]; then
  echo "🔧 Setting FIX_QUALITY_BASELINE_RUN_ID to $FIX_QUALITY_BASELINE_RUN_ID in app.yaml..."
  sed -i.bak "s/value: 'placeholder-fix-quality-baseline-run-id'/value: '$FIX_QUALITY_BASELINE_RUN_ID'/" app.yaml
  rm -f app.yaml.bak
fi

# Build fastapi client.
uv run python -m scripts.make_fastapi_client

# Build javascript.
pushd client && BROWSER=none npm run build && popd

databricks sync . "$LHA_SOURCE_CODE_PATH" \
  --profile "$DATABRICKS_CONFIG_PROFILE" \
  --exclude "*.gif"

# Generate notebook URLs and save to .env.local
uv run python scripts/generate_notebook_urls.py

# Source .env.local to get the notebook URLs
set -a
source .env.local
set +a

# Substitute notebook URLs in app.yaml
if [ -n "$NOTEBOOK_URL_1_observe_with_traces" ]; then
  echo "🔧 Setting NOTEBOOK_URL_1_observe_with_traces to $NOTEBOOK_URL_1_observe_with_traces in app.yaml..."
  sed -i.bak "s|value: 'placeholder-notebook-url-1'|value: '$NOTEBOOK_URL_1_observe_with_traces'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$NOTEBOOK_URL_2_create_quality_metrics" ]; then
  echo "🔧 Setting NOTEBOOK_URL_2_create_quality_metrics to $NOTEBOOK_URL_2_create_quality_metrics in app.yaml..."
  sed -i.bak "s|value: 'placeholder-notebook-url-2'|value: '$NOTEBOOK_URL_2_create_quality_metrics'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$NOTEBOOK_URL_3_find_fix_quality_issues" ]; then
  echo "🔧 Setting NOTEBOOK_URL_3_find_fix_quality_issues to $NOTEBOOK_URL_3_find_fix_quality_issues in app.yaml..."
  sed -i.bak "s|value: 'placeholder-notebook-url-3'|value: '$NOTEBOOK_URL_3_find_fix_quality_issues'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$NOTEBOOK_URL_4_human_review" ]; then
  echo "🔧 Setting NOTEBOOK_URL_4_human_review to $NOTEBOOK_URL_4_human_review in app.yaml..."
  sed -i.bak "s|value: 'placeholder-notebook-url-4'|value: '$NOTEBOOK_URL_4_human_review'|" app.yaml
  rm -f app.yaml.bak
fi

if [ -n "$NOTEBOOK_URL_5_production_monitoring" ]; then
  echo "🔧 Setting NOTEBOOK_URL_5_production_monitoring to $NOTEBOOK_URL_5_production_monitoring in app.yaml..."
  sed -i.bak "s|value: 'placeholder-notebook-url-5'|value: '$NOTEBOOK_URL_5_production_monitoring'|" app.yaml
  rm -f app.yaml.bak
fi

databricks sync . "$LHA_SOURCE_CODE_PATH" \
  --profile "$DATABRICKS_CONFIG_PROFILE" \
  --exclude "*.gif"

databricks apps deploy $DATABRICKS_APP_NAME \
  --source-code-path "$LHA_SOURCE_CODE_PATH"\
  --profile "$DATABRICKS_CONFIG_PROFILE"

echo ""
echo "🎉 Deployment completed!"
echo ""

# Get app status and URL
echo "📊 Checking app status..."
APP_STATUS=$(databricks apps list --profile "$DATABRICKS_CONFIG_PROFILE" | grep "$DATABRICKS_APP_NAME" || echo "")

if [ -n "$APP_STATUS" ]; then
  echo "✅ App found in Databricks Apps list"
  echo "$APP_STATUS"
  echo ""

  # Wait a moment for app to start up
  echo "⏳ Waiting for app to start up..."
  sleep 10

  # Attempt to get app URL and test health endpoint
  echo "🔍 Testing app health..."

  # Note: You'll need to replace this with your actual app URL pattern
  # This is a placeholder that would need to be customized based on your Databricks setup
  echo "📋 Post-deployment checklist:"
  echo ""
  echo "🔗 App Access:"
  echo "  • Navigate to Compute → Apps in your Databricks workspace"
  echo "  • Click on '$DATABRICKS_APP_NAME' to access your app"
  echo "  • Test the chat interface to verify agent functionality"
  echo ""
  echo "📊 Monitoring Setup:"
  echo "  • App Logs: Click 'Logs' tab in your app overview"
  echo "  • Direct Log Access: Add /logz to your app URL"
  echo "  • Health Check: Add /api/health to your app URL"
  echo "  • MLflow Traces: Check experiment ID $MLFLOW_EXPERIMENT_ID"
  echo ""
  echo "🧪 Verification Steps:"
  echo "  1. Send a test message in the chat interface"
  echo "  2. Verify logs appear in the Logs tab"
  echo "  3. Check MLflow experiment for new traces"
  echo "  4. Test thumbs up/down feedback functionality"
  echo ""
  echo "🚨 Troubleshooting:"
  echo "  • If app won't start: Check Environment tab for errors"
  echo "  • If no logs: Verify app writes to stdout/stderr"
  echo "  • If MLflow issues: Check MLFLOW_EXPERIMENT_ID in Environment"
  echo ""
else
  echo "⚠️  App not found in apps list - deployment may have failed"
  echo ""
  echo "🔧 Debugging steps:"
  echo "  1. Run: databricks apps list --profile $DATABRICKS_CONFIG_PROFILE"
  echo "  2. Check your .env.local file for correct DATABRICKS_APP_NAME"
  echo "  3. Verify workspace permissions for app deployment"
  echo "  4. Check app.yaml configuration file"
fi
