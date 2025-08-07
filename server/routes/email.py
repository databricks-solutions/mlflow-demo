"""Email generation routes."""

import asyncio
import json
import os
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from mlflow_demo.agent.email_generator import EmailGenerator
from pydantic import BaseModel

router = APIRouter(prefix='/api', tags=['email'])


# Load customer data from input_data.jsonl
def load_customer_data():
  """Load customer data from JSONL file."""
  customers = []
  try:
    # Load from mlflow_demo/data directory
    data_path = Path(__file__).parent.parent.parent / 'mlflow_demo' / 'data' / 'input_data.jsonl'
    if data_path.exists():
      with open(data_path, 'r') as f:
        for line in f:
          customers.append(json.loads(line))
    else:
      # Try alternative path if run from different directory
      with open('mlflow_demo/data/input_data.jsonl', 'r') as f:
        for line in f:
          customers.append(json.loads(line))
  except FileNotFoundError:
    print('Warning: input_data.jsonl not found in mlflow_demo/data/')
  return customers


CUSTOMER_DATA = load_customer_data()

# Initialize email generator with default configuration
email_generator = EmailGenerator()


# Email generation models
class EmailRequestWithRetrieval(BaseModel):
  """Request for email generation with customer retrieval."""

  customer_name: str
  user_input: Optional[str] = None


class EmailOutput(BaseModel):
  """Email generation output."""

  subject_line: str
  body: str
  trace_id: Optional[str] = None


class FeedbackRating(str, Enum):
  """Feedback rating enum."""

  THUMBS_UP = 'up'
  THUMBS_DOWN = 'down'


class FeedbackRequest(BaseModel):
  """Feedback request model."""

  trace_id: str
  rating: FeedbackRating
  comment: Optional[str] = None
  sales_rep_name: Optional[str] = None


class FeedbackResponse(BaseModel):
  """Feedback response model."""

  success: bool
  message: str


# Email generation endpoints
@router.get('/companies')
async def get_companies():
  """Get list of all company names."""
  companies = [{'name': customer['account']['name']} for customer in CUSTOMER_DATA]
  return sorted(companies, key=lambda x: x['name'])


@router.get('/customer/{company_name}')
async def get_customer_by_name(company_name: str):
  """Get customer data by company name from loaded data."""
  # Search for the customer in the already loaded data
  for customer in CUSTOMER_DATA:
    if customer['account']['name'] == company_name:
      return customer

  # Customer not found
  raise HTTPException(status_code=404, detail=f"Customer '{company_name}' not found")


@router.post('/generate-email-with-retrieval/', response_model=EmailOutput)
async def api_generate_email_with_retrieval(request_data: EmailRequestWithRetrieval):
  """Generate email with customer data retrieval."""
  try:
    email_json = email_generator.generate_email_with_retrieval(
      customer_name=request_data.customer_name, user_input=request_data.user_input
    )
    if (
      not isinstance(email_json, dict)
      or 'subject_line' not in email_json
      or 'body' not in email_json
    ):
      raise ValueError(
        "LLM output is not in the expected format (missing 'subject_line' or 'body')"
      )
    return EmailOutput(**email_json)
  except Exception as e:
    error_msg = str(e)
    if 'OpenAI client not available' in error_msg:
      status_code = 503
    elif 'Failed to parse LLM output' in error_msg:
      status_code = 500
    elif 'not found' in error_msg:
      status_code = 404
    else:
      status_code = 500
    raise HTTPException(status_code=status_code, detail=error_msg)


PROMPT_NAME = os.getenv('PROMPT_NAME')
PROMPT_ALIAS = os.getenv('PROMPT_ALIAS')
if not PROMPT_NAME or not PROMPT_ALIAS:
  raise Exception('PROMPT_NAME and PROMPT_ALIAS environment variables must be set')
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')


@router.post('/generate-email-stream-with-retrieval/')
async def api_generate_email_stream_with_retrieval(request_data: EmailRequestWithRetrieval):
  """Stream email generation with customer data retrieval."""

  async def generate():
    try:
      # Stream tokens from the LLM with retrieval
      async for chunk in email_generator.stream_generate_email_with_retrieval(
        customer_name=request_data.customer_name, user_input=request_data.user_input
      ):
        # Format as Server-Sent Event
        if chunk['type'] == 'token':
          yield f'data: {json.dumps({"type": "token", "content": chunk["content"]})}\n\n'
        elif chunk['type'] == 'done':
          yield f'data: {json.dumps({"type": "done", "trace_id": chunk["trace_id"]})}\n\n'
        elif chunk['type'] == 'error':
          yield f'data: {json.dumps({"type": "error", "error": chunk["error"]})}\n\n'

        # Small delay to ensure smooth streaming
        await asyncio.sleep(0.01)
    except Exception as e:
      yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'
    finally:
      # Send done event to close the stream
      yield f'data: {json.dumps({"type": "done"})}\n\n'

  return StreamingResponse(
    generate(),
    media_type='text/event-stream',
    headers={
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',  # Disable Nginx buffering
    },
  )


@router.post('/feedback', response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
  """Submit user feedback linked to trace."""
  # Convert rating to boolean value
  is_positive = feedback.rating == FeedbackRating.THUMBS_UP

  result = email_generator.log_feedback(
    trace_id=feedback.trace_id,
    value=is_positive,
    comment=feedback.comment,
    user_name=feedback.sales_rep_name,
  )
  return FeedbackResponse(success=result['success'], message=result['message'])
