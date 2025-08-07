# Databricks notebook source
# MAGIC %pip install -U -r "/Workspace/Users/eric.peter@databricks.com/mlflow-genai-email-demo/requirements.txt"
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from openai import OpenAI

# Enable MLflow's autologging to instrument your application with Tracing
# mlflow.openai.autolog()

# Connect to a Databricks LLM via OpenAI using the same credentials as MLflow
# Alternatively, you can use your own OpenAI credentials here
mlflow_creds = mlflow.utils.databricks_utils.get_databricks_host_creds()
client_local = OpenAI(
    api_key=mlflow_creds.token,
    base_url=f"{mlflow_creds.host}/serving-endpoints"
)

model = 'databricks-claude-3-7-sonnet'

def call_llm(query, customer_data):
  mlflow.openai.autolog(disable=True)
  response = client_local.chat.completions.create(
      model=model,  # This example uses a Databricks hosted LLM - you can replace this with any AI Gateway or Model Serving endpoint. If you provide your own OpenAI credentials, replace with a valid OpenAI model e.g., gpt-4o, etc.
      messages=[
        {
          "role": "system",
          "content": f"You are an expert sales person.  When you follow instructions, you are aware that the instruction will be used in context of data that looks like this {json.dumps(customer_data)}.",
        },
        {
          "role": "user",
          "content": query,
        },
      ],
    )
  return response.choices[0].message.content

def gen_instruction(customer_data):
  return call_llm("Generate an 1 - 2 sentence instruction to an LLM for generating an email you need to send to a customer.  Return just the instruction and nothing else.", customer_data)

def write_feeedback(query):
  mlflow.openai.autolog(disable=True)
  output = "fake cloudflow features in email"
  inputs = [{'judge_name': 'accuracy', 'judge_rule': 'The response correctly references all factual information from the provided_info based on these rules:\n- All factual information must be directly sourced from the provided data with NO fabrication\n- Names, dates, numbers, and company details must be 100% accurate with no errors\n- Meeting discussions must be summarized with the exact same sentiment and priority as presented in the data\n- Support ticket information must include correct ticket IDs, status, and resolution details when available\n- All product usage statistics must be presented with the same metrics provided in the data\n- No references to CloudFlow features, services, or offerings unless specifically mentioned in the customer data\n- AUTOMATIC FAIL if any information is mentioned that is not explicitly provided in the data', 'judge_score': 'no', 'judge_rationale': "The response correctly references the following factual information from the provided data: - The company name 'EcoFuture Services' and the main contact 'Kevin Brown'. - The consultation date 'June 25th' and the challenges discussed during the meeting. - The high-priority login issue with ticket ID 'TK-0045' and its status as 'Open'. - The 20% decrease in active users over the last month. - The mention of scheduling a training session and discussing tailored solutions, which were action items from the meeting.  However, the response mentions 'CloudFlow features' such as the 'Reporting feature' and 'system access', which were not explicitly mentioned in the provided data. This violates the guideline that no references to CloudFlow features, services, or offerings should be made unless specifically mentioned in the customer data.  Therefore, the result is 'no'."}, {'judge_name': 'personalized', 'judge_rule': 'The response demonstrates clear personalization based on the provided_info based on these rules:\n- Email must begin by referencing the most recent meeting/interaction\n- Immediatly next, the email must address the customer\'s MOST pressing concern as evidenced in the data\n- Content structure must be customized based on the account\'s health status (critical issues first for "Fair" or "Poor" accounts)\n- Industry-specific language must be used that reflects the customer\'s sector\n- Recommendations must ONLY reference features that are:\n  a) Listed as "least_used_features" in the data, AND\n  b) Directly related to the "potential_opportunity" field\n- Relationship history must be acknowledged (new vs. mature relationship)\n- Deal stage must influence communication approach (implementation vs. renewal vs. growth)\n- AUTOMATIC FAIL if recommendations could be copied to another customer in a different situation', 'judge_score': 'no', 'judge_rationale': "The response begins by referencing the most recent meeting/interaction from June 25th, which satisfies the first guideline. Next, it addresses the customer's most pressing concern, the high-priority login issues (ticket TK-0045), which aligns with the second guideline. The content structure is customized based on the account's health status, addressing critical issues first, which meets the third guideline. However, the response does not use industry-specific language reflecting the customer's sector, which is environmental services, thus failing the fourth guideline. The recommendations reference the Reporting feature, which is listed as a least-used feature and is related to the potential opportunity of improved user training and support, satisfying the fifth guideline. The relationship history is acknowledged by mentioning the consultation and the challenges discussed, meeting the sixth guideline. The deal stage is considered as the response aims to improve the customer's experience and address issues before the next renewal, satisfying the seventh guideline. The recommendations are specific to the customer's situation and cannot be copied to another customer in a different situation, meeting the eighth guideline. Therefore, the response does not fully satisfy all the guidelines."}, {'judge_name': 'relevance', 'judge_rule': 'The response prioritizes content that matters to the recipient in the provided_info based on these rules:\n- Critical support tickets (status="Open (Critical)") must be addressed after the greeting, reference to the most recent interaction, any pleasantrys, and references to closed tickets\n    - it is ok if they name is slightly different as long as it is clearly the same issue as in the provided_info\n- Time-sensitive action items must be addressed before general updates\n- Content must be ordered by descending urgency as defined by:\n  1. Critical support issues\n  2. Action items explicitly stated in most recent meeting\n  3. Upcoming renewal if within 30 days\n  4. Recently resolved issues\n  5. Usage trends and recommendations\n- No more than ONE feature recommendation for accounts with open critical issues\n- No mentions of company news, product releases, or success stories not directly requested by the customer\n- No calls to action unrelated to the immediate needs in the data\n- AUTOMATIC FAIL if the email requests a meeting without being tied to a specific action item or opportunity in the data', 'judge_score': 'yes', 'judge_rationale': 'The response addresses the critical support ticket (TK-0045) immediately after the greeting and pleasantries, which is correct. It then addresses the time-sensitive action items from the most recent meeting, such as scheduling a training session and discussing tailored solutions. There is no mention of the upcoming renewal, which is not within 30 days, so this is acceptable. The response includes a single feature recommendation related to the Reporting feature, which is appropriate given the open critical issue. There are no mentions of company news, product releases, or success stories, and all calls to action are related to the immediate needs in the data. The email requests a meeting tied to specific action items (user training session and tailored solutions), which is acceptable. Therefore, all guidelines are satisfied.'}]

  response = client_local.chat.completions.create(
      model=model,  # This example uses a Databricks hosted LLM - you can replace this with any AI Gateway or Model Serving endpoint. If you provide your own OpenAI credentials, replace with a valid OpenAI model e.g., gpt-4o, etc.
      messages=[
        {
          "role": "system",
          "content": f"""You are an expert at synthesizing llm judge feedback into short brief statements that a busy user might write.  They should be unstructured comments and not sentences.  The user's feedback must be based on the llm judge feedback.

          Example:
          Input: {json.dumps(inputs)}
          Your response: {output}
          """,
        },
        {
          "role": "user",
          "content": query,
        },
      ],
    )
  return response.choices[0].message.content

# COMMAND ----------

import os
import yaml
import json

yaml_path = "/Workspace/Users/eric.peter@databricks.com/mlflow-genai-email-demo/app.yaml"

with open(yaml_path, 'r') as yaml_file:
    yaml_content = yaml.safe_load(yaml_file)

print(yaml_content['env'])

for item in yaml_content['env']:
  os.environ[item['name']] = item['value']

# Key environment variables
PROMPT_NAME = os.getenv('PROMPT_NAME')
PROMPT_ALIAS = os.getenv('PROMPT_ALIAS')
if not PROMPT_NAME or not PROMPT_ALIAS:
  raise Exception('PROMPT_NAME and PROMPT_ALIAS environment variables must be set')
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# COMMAND ----------

import mlflow
mlflow.set_experiment(experiment_id=os.environ['MLFLOW_EXPERIMENT_ID'])

# COMMAND ----------

import json
customers = []
with open("input_data.jsonl", 'r', encoding='utf-8') as f:
  for line_num, line in enumerate(f, 1):
    try:
      customer_data = json.loads(line.strip())
      customers.append(customer_data)
    except json.JSONDecodeError as e:
      print(f'Error parsing JSON on line {line_num}: {e}')

# COMMAND ----------

import sys
sys.path.insert(0, "/Workspace/Users/eric.peter@databricks.com/mlflow-genai-email-demo/")

# COMMAND ----------

from mlflow.genai import judges
from server.routes.run_eval import (
  guidelines
)

def is_trace_good(trace_id):
  trace = mlflow.get_trace(trace_id)
  root_span = trace.data.spans[0]
  # print(root_span.inputs)
  # print(type(root_span.outputs))
  num_passed = 0
  feedbacks = []
  for name, guideline_rule in guidelines.items():
    result = judges.meets_guidelines(guidelines=guideline_rule, context={"request": json.dumps(root_span.inputs), "response": json.dumps(root_span.outputs)})
    # print(result.)
    if result.feedback.value == 'yes':
      num_passed += 1
    feedbacks.append({"judge_name": name, "judge_rule": guideline_rule, "judge_score": str(result.feedback.value), "judge_rationale": result.rationale})

  if num_passed == 3:
    return (True, feedbacks)
  else:
    return (False, feedbacks)

result, feedbacks = is_trace_good("tr-a5efee364ebac2391bb8453079a21e8f")
print(write_feeedback(json.dumps(feedbacks)))
print(feedbacks)

# COMMAND ----------

import random

# Randomly select a number between 1 and 10
num_rows = random.randint(1, 10)

# Sample the array
sampled_customers = random.sample(customers, num_rows)

print(sampled_customers)

# COMMAND ----------

from mlflow_demo.agent.email_generator import EmailGenerator

print(f"generating for {len(sampled_customers)}")
for customer_data in sampled_customers:
  print("---- Generating... -----")
  # 30% chance to include instructions
  if random.random() < 0.3:
      # Your code here
      instruction = gen_instruction(customer_data)
      customer_data['user_input'] = instruction

  mlflow.openai.autolog(disable=False)

  generator = EmailGenerator()
  customer_name = customer_data["account"]["name"]
  user_input = customer_data.get("user_input")
  response = generator.generate_email_with_retrieval(customer_name, user_input)

  trace_id = response['trace_id']
  print(trace_id)

  rating, feedbacks = is_trace_good(trace_id)

  # 20% get feedback
  if random.random() < 0.2:

    rating, feedbacks = is_trace_good(trace_id)
    user_comment = write_feeedback(json.dumps(feedbacks))
    print(f"leaving feedback: {rating} {user_comment}")

    mlflow.log_feedback(
        trace_id=trace_id,
        name='user_feedback',
        value=rating,
        rationale=user_comment,
        source=mlflow.entities.AssessmentSource(
          source_type='HUMAN',
          source_id="first.last@company.com",
        ),
      )
  # break




# COMMAND ----------

# MAGIC %md
# MAGIC doesnt work bc notebook doesnt do oauth

# COMMAND ----------

# from databricks import sdk
# import requests
# import time

# url = "https://mlflow-genai-email-demo-2556758628403379.aws.databricksapps.com/api/generate-email/"
# w = sdk.WorkspaceClient()




# def gen_email(customer_data):
#   start_time = time.time()
#   # Create a dictionary to use as the body of the request
#   body = {
#       "customer_info": customer_data,
#   }

#   headers = w.config.authenticate()
#   print(headers)
#   resp = requests.post(url, headers=headers, json=body)
#   latency = (time.time() - start_time) * 1000  # Convert to milliseconds
#   print(f"Status={resp.status_code}, Body={resp.json()}, Latency={latency:.2f}ms")
#   print(resp)
#   return resp

#   # resp = requests.post(url, headers=headers)
#   # latency = (time.time() - start_time) * 1000  # Convert to milliseconds
#   # print(f"Status={resp.status_code}, Body={resp.json()}, Latency={latency:.2f}ms")
