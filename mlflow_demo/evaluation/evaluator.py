"""MLflow evaluation logic for email generation."""

import os

import mlflow
from mlflow.genai.judges import is_grounded, meets_guidelines
from mlflow.genai.scorers import Guidelines, scorer

from mlflow_demo.utils.mlflow_helpers import generate_evaluation_links

# Prompt registry configuration
DEV_PROMPT_ALIAS = 'development'


def validate_env_vars():
  """Validate required environment variables are set."""
  PROMPT_NAME = os.getenv('PROMPT_NAME')
  PROMPT_ALIAS = os.getenv('PROMPT_ALIAS')
  if not PROMPT_NAME or not PROMPT_ALIAS:
    raise Exception('PROMPT_NAME and PROMPT_ALIAS environment variables must be set')
  return PROMPT_NAME, PROMPT_ALIAS


REGRESSION_DATASET_NAME = 'regression_set'
FIX_DATASET_NAME = 'low_accuracy'

UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Tone of voice Guideline - Ensure professional tone
tone = Guidelines(name='tone', guidelines="""The response maintains a professional tone.""")


# Accuracy Guideline - Verify all facts come from provided data
@scorer
def accuracy(trace):
  """Custom accuracy scorer that evaluates only the email body content.

  Excluding the subject line to avoid false negatives on creative/generic subjects.

  This demonstrates how to wrap the proven Guidelines judge with custom data extraction.
  """
  import json

  # Extract the original request
  outputs = json.loads(trace.data.response)
  email_body = outputs.get('email_body')
  user_input = outputs.get('user_input')
  input_facts = trace.search_spans(span_type='RETRIEVER')[0].outputs

  accuracy_guideline = """The email_body correctly references all factual information from the provided_info based on these rules:
- All factual information must be directly sourced from the provided data with NO fabrication
- Names, dates, numbers, and company details must be 100% accurate with no errors
- Meeting discussions must be summarized with the exact same sentiment and priority as presented in the data
- Support ticket information must include correct ticket IDs, status, and resolution details when available
- All product usage statistics must be presented with the same metrics provided in the data
- No references to CloudFlow features, services, or offerings unless specifically mentioned in the customer data
- AUTOMATIC FAIL if any information is mentioned that is not explicitly provided in the data
- It is OK if the email_body follows the user_input request to omit certain facts, as long as no fabricated facts are introduced."""

  # Use the proven Guidelines judge with our extracted email body
  return meets_guidelines(
    guidelines=accuracy_guideline,
    context={'provided_info': input_facts, 'email': email_body, 'user_input': user_input},
  )


# Personalization Guideline - Ensure emails are tailored to specific customers
@scorer
def personalized(trace):
  """Custom personalization scorer that evaluates only the email body content.

  Excluding the subject line to avoid false negatives on creative/generic subjects.

  This demonstrates how to wrap the proven Guidelines judge with custom data extraction.
  """
  import json

  # Extract the original request
  outputs = json.loads(trace.data.response)
  email_body = outputs.get('email_body')
  user_input = outputs.get('user_input')
  input_facts = trace.search_spans(span_type='RETRIEVER')[0].outputs

  personalized_guideline = """The email_body demonstrates clear personalization based on the provided_info based on these rules:
- Email must begin by referencing the most recent meeting/interaction
- Immediately next, the email must address the customer's MOST pressing concern as evidenced in the data
- Content structure must be customized based on the account's health status (critical issues first for "Fair" or "Poor" accounts)
- Industry-specific language must be used that reflects the customer's sector
- Recommendations must ONLY reference features that are:
  a) Listed as "least_used_features" in the data, AND
  b) Directly related to the "potential_opportunity" field
- Relationship history must be acknowledged (new vs. mature relationship)
- Deal stage must influence communication approach (implementation vs. renewal vs. growth)
- AUTOMATIC FAIL if recommendations could be copied to another customer in a different situation"""

  # Use the proven Guidelines judge with our extracted email body
  return meets_guidelines(
    guidelines=personalized_guideline,
    context={'provided_info': input_facts, 'email': email_body, 'user_input': user_input},
  )


# Relevance Guideline - Prioritize content by urgency
@scorer
def relevance(trace):
  """Custom relevance scorer that evaluates only the email body content.

  Excluding the subject line to avoid false negatives on creative/generic subjects.

  This demonstrates how to wrap the proven Guidelines judge with custom data extraction.
  """
  import json

  # Extract the original request
  outputs = json.loads(trace.data.response)
  email_body = outputs.get('email_body')
  user_input = outputs.get('user_input')
  input_facts = trace.search_spans(span_type='RETRIEVER')[0].outputs

  relevance_guideline = """The email_body prioritizes content that matters to the recipient in the provided_info based on these rules:
- Critical support tickets (status="Open (Critical)") must be addressed after the greeting, reference to the most recent interaction, any pleasantries, and references to closed tickets
- Time-sensitive action items must be addressed before general updates
- Content must be ordered by descending urgency as defined by:
  1. Critical support issues
  2. Action items explicitly stated in most recent meeting
  3. Upcoming renewal if within 30 days
  4. Recently resolved issues
  5. Usage trends and recommendations
- No more than ONE feature recommendation for accounts with open critical issues
- No mentions of company news, product releases, or success stories not directly requested by the customer
- No calls to action unrelated to the immediate needs in the data
- AUTOMATIC FAIL if the email requests a meeting without being tied to a specific action item or opportunity in the data"""

  # Use the proven Guidelines judge with our extracted email body
  return meets_guidelines(
    guidelines=relevance_guideline,
    context={'provided_info': input_facts, 'email': email_body, 'user_input': user_input},
  )


# Groundedness Guideline - Ensure emails are grounded in provided facts
@scorer
def email_is_grounded(trace):
  """Custom groundedness scorer that evaluates only the email body content.

  Excluding the subject line to avoid false negatives on creative/generic subjects.

  This demonstrates how to wrap the proven is_grounded judge with custom data extraction.
  """
  import json

  # Extract the original request
  outputs = json.loads(trace.data.response)
  email_body = outputs.get('email_body')
  user_input = outputs.get('user_input')
  input_facts = trace.search_spans(span_type='RETRIEVER')[0].outputs

  if user_input is None or len(user_input) == 0:
    request = 'Generate an email based on the provided context.'
  else:
    request = (
      "Generate an email based on the provided context, considering the user's request: "
      + user_input
    )

  # Use the proven is_grounded judge with our extracted email body
  return is_grounded(request=request, response=email_body, context=input_facts)


# Convenience list of all scorers for easy use in evaluation
SCORERS = [tone, accuracy, personalized, relevance, email_is_grounded]


def run_evaluation():
  """Run evaluation on recent traces."""
  # A Scorer operates on a MLflow Trace, so let's retrieve a few Traces:
  print('\n🔍 Loading recent traces from our email demo app...')

  # Load recent traces for evaluation
  traces = mlflow.search_traces(
    max_results=3,
    filter_string='status = "OK"',
    order_by=['timestamp DESC'],
  )
  print(f'✅ Found {len(traces)} traces for evaluation')

  # Now, let's run evaluation using this scorer
  eval_results = mlflow.genai.evaluate(data=traces, scorers=SCORERS)

  print('\n📊 Evaluation completed!')
  print(f'🆔 Run ID: {eval_results._run_id}')

  # Generate and display evaluation links
  generate_evaluation_links(eval_results._run_id)

  return eval_results
