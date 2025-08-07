import asyncio
import json
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import dotenv

# Load environment variables from .env.local in project root
dotenv.load_dotenv(project_root / '.env.local')

import mlflow

# Key environment variables
PROMPT_NAME = os.getenv('PROMPT_NAME')
PROMPT_ALIAS = os.getenv('PROMPT_ALIAS')
if not PROMPT_NAME or not PROMPT_ALIAS:
  raise Exception('PROMPT_NAME and PROMPT_ALIAS environment variables must be set')
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# example commands
# traces = mlflow.search_traces(return_type='list')
# print(traces)

# Load sample input data
customers = []
with open('./input_data.jsonl', 'r', encoding='utf-8') as f:
  for line_num, line in enumerate(f, 1):
    try:
      customers.append(json.loads(line.strip()))
    except json.JSONDecodeError as e:
      print(f'Error parsing JSON on line {line_num}: {e}')

# Call the email generation app
from mlflow_demo.agent.email_generator import EmailGenerator

# non streaming version
generator = EmailGenerator()
customer_name = customers[0]["account"]["name"]
user_input = customers[0].get("user_input")
print(generator.generate_email_with_retrieval(customer_name, user_input))

# streaming version
async def test_streaming():
  generator = EmailGenerator()
  customer_name = customers[0]["account"]["name"]
  user_input = customers[0].get("user_input")
  async for chunk in generator.stream_generate_email_with_retrieval(customer_name, user_input):
      # Format as Server-Sent Event
      if chunk['type'] == 'token':
        print(chunk["content"])
      elif chunk['type'] == 'done':
        print(chunk["trace_id"])
      elif chunk['type'] == 'error':
        print(chunk["error"])

asyncio.run(test_streaming())
