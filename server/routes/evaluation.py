"""Evaluation routes for running MLflow LLM judge evaluations."""

import json
import logging
import os
from typing import Optional

import mlflow
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from mlflow_demo.utils.mlflow_helpers import get_mlflow_experiment_id
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/evaluation', tags=['evaluation'])

# 10 representative coaching questions for live demo evaluation
EVAL_QUESTIONS = [
  'How does the 2024 Kansas City Chiefs offense approach third-and-long situations?',
  'What are the most common passing concepts used by the 2023 San Francisco 49ers in the red zone?',
  'How does the 2024 Baltimore Ravens offense adjust when facing a blitz-heavy defense?',
  'What tendencies does the 2024 Dallas Cowboys offense show on first down?',
  'Which running plays are most effective for the 2023 Cleveland Browns against a blitz?',
  'How does the 2024 Miami Dolphins offense attack Cover 2 defenses?',
  'What is the typical play sequence for the 2024 Buffalo Bills with under two minutes left in the half?',
  'How does the 2024 Green Bay Packers offense change their approach in the red zone?',
  'Which receivers are most targeted by the 2024 Los Angeles Rams on third down?',
  'How does the 2024 New England Patriots offense exploit man-to-man coverage?',
]


class RunEvalRequest(BaseModel):
  """Request to run evaluation with selected scorers."""

  builtin_judges: list[str] = []
  custom_guidelines: list[dict] = []


class RunSessionEvalRequest(BaseModel):
  """Request to run session-level evaluation with selected scorers."""

  session_judges: list[str] = []


@router.post('/run')
async def run_evaluation(request: RunEvalRequest):
  """Run mlflow.genai.evaluate() with selected scorers, streaming progress via SSE."""

  async def generate():
    from mlflow.genai.scorers import Guidelines

    try:
      # Set experiment
      mlflow.set_experiment(experiment_id=get_mlflow_experiment_id())

      # Build scorers list
      scorers = []

      # Add built-in judges
      from mlflow.genai import scorers as mlflow_scorers

      # Map frontend checkbox names to actual scorer classes
      builtin_map = {
        'RelevanceToQuery': mlflow_scorers.RelevanceToQuery,
        'Safety': mlflow_scorers.Safety,
        'ToolCallCorrectness': mlflow_scorers.ToolCallCorrectness,
        'ToolCallEfficiency': mlflow_scorers.ToolCallEfficiency,
      }

      logger.info(f'Requested built-in judges: {request.builtin_judges}')
      logger.info(f'Available builtin_map keys: {list(builtin_map.keys())}')

      for name in request.builtin_judges:
        if name in builtin_map:
          scorers.append(builtin_map[name]())
          logger.info(f'Added built-in scorer: {name}')
        else:
          logger.warning(f'Built-in scorer not found: {name}')

      # Add custom guidelines judges (always included)
      logger.info(f'Requested custom guidelines: {[g.get("name") for g in request.custom_guidelines]}')
      for g in request.custom_guidelines:
        if g.get('name') and g.get('guideline'):
          scorers.append(Guidelines(name=g['name'], guidelines=g['guideline']))
          logger.info(f'Added custom guideline scorer: {g["name"]}')

      total_questions = len(EVAL_QUESTIONS)
      total_scorers = len(scorers)
      logger.info(f'Total scorers built: {total_scorers} ({[type(s).__name__ for s in scorers]})')

      yield f'data: {json.dumps({"type": "start", "total_questions": total_questions, "total_scorers": total_scorers})}\n\n'

      logger.info(
        f'Starting evaluation: {total_questions} questions, {total_scorers} scorers'
      )

      # Build evaluation data - match notebook pattern
      # 'input' key matches predict_fn parameter name
      from mlflow_demo.agent import AGENT

      eval_data = [
        {'inputs': {'input': [{'role': 'user', 'content': q}]}}
        for q in EVAL_QUESTIONS
      ]

      def predict_fn(input):
        AGENT.start_new_session()
        return AGENT.predict({'input': input})

      # Send progress updates as we go
      # We'll run the actual evaluation and stream progress
      yield f'data: {json.dumps({"type": "progress", "step": "loading", "message": "Loading agent and scorers...", "percent": 5})}\n\n'

      yield f'data: {json.dumps({"type": "progress", "step": "running", "message": f"Running {total_scorers} scorers against {total_questions} questions...", "percent": 15})}\n\n'

      # Run mlflow.genai.evaluate()
      from datetime import datetime

      with mlflow.start_run(
        run_name=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_dc_eval'
      ) as run:
        results = mlflow.genai.evaluate(
          data=eval_data,
          predict_fn=predict_fn,
          scorers=scorers,
        )
        run_id = run.info.run_id

      yield f'data: {json.dumps({"type": "progress", "step": "finalizing", "message": "Finalizing results...", "percent": 90})}\n\n'

      # Extract summary metrics
      metrics_summary = {}
      if hasattr(results, 'metrics') and results.metrics:
        metrics_summary = {
          k: v for k, v in results.metrics.items() if isinstance(v, (int, float))
        }

      yield f'data: {json.dumps({"type": "done", "run_id": run_id, "metrics": metrics_summary, "percent": 100})}\n\n'

      logger.info(f'Evaluation complete. Run ID: {run_id}')

    except Exception as e:
      logger.error(f'Evaluation error: {e}')
      yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'

  return StreamingResponse(
    generate(),
    media_type='text/event-stream',
    headers={
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  )


# Dataset name for session-level evaluation traces
SESSION_EVAL_DATASET = 'short_eval_session_set'


@router.post('/run-session')
async def run_session_evaluation(request: RunSessionEvalRequest):
  """Run session-level evaluation on pre-collected multi-turn traces via SSE."""

  async def generate():
    try:
      from mlflow.genai import scorers as mlflow_scorers
      from datetime import datetime

      exp_id = get_mlflow_experiment_id()
      mlflow.set_experiment(experiment_id=exp_id)

      # Map frontend names to session-level scorer classes
      session_scorer_map = {
        'ConversationCompleteness': mlflow_scorers.ConversationCompleteness,
        'ConversationalRoleAdherence': mlflow_scorers.ConversationalRoleAdherence,
        'ConversationalSafety': mlflow_scorers.ConversationalSafety,
        'ConversationalToolCallEfficiency': mlflow_scorers.ConversationalToolCallEfficiency,
        'KnowledgeRetention': mlflow_scorers.KnowledgeRetention,
        'UserFrustration': mlflow_scorers.UserFrustration,
      }

      # Build scorers
      scorers = []
      for name in request.session_judges:
        if name in session_scorer_map:
          scorers.append(session_scorer_map[name]())
          logger.info(f'Added session scorer: {name}')
        else:
          logger.warning(f'Session scorer not found: {name}')

      total_scorers = len(scorers)
      logger.info(f'Session evaluation: {total_scorers} scorers')

      yield f'data: {json.dumps({"type": "start", "total_scorers": total_scorers})}\n\n'

      # Load trace IDs from the evaluation dataset
      catalog = os.environ.get('UC_CATALOG', '')
      schema = os.environ.get('UC_SCHEMA', '')
      dataset_name = f'{catalog}.{schema}.{SESSION_EVAL_DATASET}'

      logger.info(f'Loading dataset: {dataset_name}')
      ds = mlflow.genai.datasets.get_dataset(name=dataset_name)
      df = ds.to_df()

      trace_ids = set()
      for _, row in df.iterrows():
        source = row.get('source', {})
        if isinstance(source, dict) and 'trace' in source:
          trace_ids.add(source['trace']['trace_id'])

      logger.info(f'Dataset contains {len(trace_ids)} trace IDs')

      yield f'data: {json.dumps({"type": "progress", "message": f"Loaded {len(trace_ids)} traces from dataset"})}\n\n'

      # Load actual trace objects with session metadata
      filter_str = 'metadata.`mlflow.trace.session` != ""'
      all_traces = mlflow.search_traces(
        locations=[exp_id],
        filter_string=filter_str,
        return_type='list',
        max_results=100,
      )

      # Filter to only traces in our dataset
      dataset_traces = [t for t in all_traces if t.info.request_id in trace_ids]
      logger.info(f'Matched {len(dataset_traces)} traces from experiment')

      if not dataset_traces:
        yield f'data: {json.dumps({"type": "error", "error": "No matching traces found in experiment"})}\n\n'
        return

      # Count sessions
      sessions = set()
      for t in dataset_traces:
        sid = t.info.request_metadata.get('mlflow.trace.session', '')
        if sid:
          sessions.add(sid)

      yield f'data: {json.dumps({"type": "progress", "message": f"Evaluating {len(sessions)} sessions ({len(dataset_traces)} traces) with {total_scorers} scorers..."})}\n\n'

      # Run mlflow.genai.evaluate with session-level scorers
      with mlflow.start_run(
        run_name=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_session_eval'
      ) as run:
        results = mlflow.genai.evaluate(
          data=dataset_traces,
          scorers=scorers,
        )
        run_id = run.info.run_id

      # Extract summary metrics
      metrics_summary = {}
      if hasattr(results, 'metrics') and results.metrics:
        metrics_summary = {
          k: v for k, v in results.metrics.items() if isinstance(v, (int, float))
        }

      yield f'data: {json.dumps({"type": "done", "run_id": run_id, "metrics": metrics_summary, "sessions": len(sessions), "traces": len(dataset_traces)})}\n\n'

      logger.info(f'Session evaluation complete. Run ID: {run_id}')

    except Exception as e:
      logger.error(f'Session evaluation error: {e}')
      yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'

  return StreamingResponse(
    generate(),
    media_type='text/event-stream',
    headers={
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  )
