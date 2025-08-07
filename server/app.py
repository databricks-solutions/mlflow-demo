"""FastAPI app for the Lakehouse Apps + Agents demo."""

import argparse
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import mlflow
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from mlflow_demo.utils.mlflow_helpers import get_mlflow_experiment_id
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from .routes import email, helper

# Configure logging for Databricks Apps monitoring
# Logs written to stdout/stderr will be available in Databricks Apps UI and /logz endpoint
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  handlers=[
    logging.StreamHandler(),  # This ensures logs go to stdout for Databricks Apps monitoring
  ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Manage application lifespan events."""
  # Startup
  logger.info('Starting application...')

  logger.info('Application startup complete')

  yield

  # Shutdown
  logger.info('Application shutting down...')
  logger.info('Application shutdown complete')


app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend to access backend APIs
app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],  # Change this to specific origins in production
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

# We're in dev mode when the server has the reload bit.
IS_DEV = os.getenv('IS_DEV', 'false').lower() == 'true'
# Parse arguments at startup
parser = argparse.ArgumentParser()
# bool
parser.add_argument('--reload', action='store_true')
args, _ = parser.parse_known_args()  # Ignore unknown args
IS_DEV = args.reload

PORT = int(os.getenv('UVICORN_PORT', 8000))
HOST = os.getenv('UVICORN_HOST', '0.0.0.0')

API_PREFIX = '/api'

# Include route modules
app.include_router(email.router)
app.include_router(helper.router)


# Common/shared models
class ExperimentInfo(BaseModel):
  """Experiment info."""

  experiment_id: str
  link: str
  trace_url_template: str
  failed_traces_url: str
  eval_dataset_url: str
  monitoring_url: str


class PreloadedResults(BaseModel):
  """Preloaded evaluation results from setup scripts."""

  low_accuracy_results_url: str | None = None
  regression_results_url: str | None = None
  metrics_result_url: str | None = None
  sample_trace_url: str
  sample_labeling_session_url: str
  sample_review_app_url: str
  sample_labeling_trace_id: str | None = None
  sample_labeling_trace_url: str


def ensure_https_protocol(host: str | None) -> str:
  """Ensure the host URL has HTTPS protocol."""
  if not host:
    return ''

  if host.startswith('https://') or host.startswith('http://'):
    return host

  return f'https://{host}'


# Common/shared endpoints
@app.get(f'{API_PREFIX}/tracing_experiment')
async def experiment():
  """Get the MLFlow experiment info."""
  databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))

  return ExperimentInfo(
    experiment_id=get_mlflow_experiment_id(),
    link=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}?compareRunsMode=TRACES',
    trace_url_template=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/traces?selectedEvaluationId=',
    failed_traces_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/traces?&filter=TAG%3A%3A%3D%3A%3Ayes%3A%3Aeval_example&filter=ASSESSMENT%3A%3A%3D%3A%3Ano%3A%3Aaccuracy',
    eval_dataset_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/datasets',
    monitoring_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/evaluation-monitoring',
  )


@app.get(f'{API_PREFIX}/preloaded-results')
async def get_preloaded_results() -> PreloadedResults:
  """Get preloaded evaluation results from setup scripts."""
  databricks_host = ensure_https_protocol(os.getenv('DATABRICKS_HOST'))
  return PreloadedResults(
    low_accuracy_results_url=os.getenv('LOW_ACCURACY_RESULTS_URL'),
    regression_results_url=os.getenv('REGRESSION_RESULTS_URL'),
    metrics_result_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/traces?selectedEvaluationId={os.getenv("SAMPLE_TRACE_ID")}',
    sample_trace_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/traces?selectedEvaluationId={os.getenv("SAMPLE_TRACE_ID")}',
    sample_labeling_session_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/labeling-sessions?selectedLabelingSessionId={os.getenv("SAMPLE_LABELING_SESSION_ID")}',
    sample_review_app_url=os.getenv('SAMPLE_REVIEW_APP_URL'),
    sample_labeling_trace_id=os.getenv('SAMPLE_LABELING_TRACE_ID'),
    sample_labeling_trace_url=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}/traces?selectedEvaluationId={os.getenv("SAMPLE_LABELING_TRACE_ID")}',
  )


@app.get(f'{API_PREFIX}/health')
async def health_check():
  """Health check endpoint for monitoring app status."""
  try:
    # Test MLflow connection
    experiment_id = get_mlflow_experiment_id()

    # Test basic functionality
    health_status = {
      'status': 'healthy',
      'timestamp': mlflow.utils.time_utils.get_current_time_millis(),
      'mlflow_experiment_id': experiment_id,
      'environment': 'production' if not IS_DEV else 'development',
    }

    logger.info('Health check passed - all systems operational')
    return health_status

  except Exception as e:
    logger.error(f'Health check failed: {str(e)}')
    return {
      'status': 'unhealthy',
      'error': str(e),
      'timestamp': mlflow.utils.time_utils.get_current_time_millis(),
    }


# Static file serving and dev proxy
if not IS_DEV:
  # Production: Serve the built React files
  build_path = Path('.') / 'client/build'
  if build_path.exists():
    # Mount static assets first (these should not fallback to index.html)
    app.mount('/assets', StaticFiles(directory=build_path / 'assets'), name='assets')
    
    # Add catch-all route for SPA routing (must come after API routes)
    @app.get('/{full_path:path}')
    async def spa_fallback(full_path: str):
      """Serve index.html for all non-API routes to support SPA routing."""
      # Don't interfere with API routes
      if full_path.startswith('api/'):
        raise HTTPException(status_code=404, detail="API endpoint not found")
      
      index_file = build_path / 'index.html'
      if index_file.exists():
        return FileResponse(index_file)
      else:
        raise HTTPException(status_code=404, detail="Application not built")
        
  else:
    raise RuntimeError(f'Build directory {build_path} not found. Run `bun run build` in client/')


if IS_DEV:

  @app.api_route('/{full_path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'])
  async def proxy_to_dev_server(request: Request, full_path: str):
    """Proxy all non-API requests to the Vite dev server."""
    dev_server_url = f'http://localhost:3000/{full_path}'

    async with httpx.AsyncClient() as client:
      try:
        # Forward request to Vite dev server
        response = await client.request(
          method=request.method,
          url=dev_server_url,
          headers=request.headers.raw,
          content=await request.body(),
        )

        # Return the actual response from Vite dev server
        return Response(
          content=response.content,
          status_code=response.status_code,
          headers=dict(response.headers),
        )
      except httpx.RequestError:
        return Response(
          content='Vite dev server not running.',
          status_code=502,
        )


if __name__ == '__main__':
  uvicorn.run(app, host=HOST, port=PORT)
