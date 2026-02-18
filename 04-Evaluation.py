# Databricks notebook source
# MAGIC %md
# MAGIC # AI Evaluation
# MAGIC
# MAGIC - AI Evaluation is the most critical part of getting an agent pilot into production. It gives a quantitative view into agent performance and enables a clear understanding of model performance that build the trust with stakeholders and end users necessary to drive towards production. 
# MAGIC
# MAGIC - We will use built-in judges, custom guideline based judges, and a fully custom prompt based judge to evaluate performance
# MAGIC
# MAGIC - This gives a full view into how the agent is performance, and the trace-level observational detail allows us to drill into specific examples to determine quality

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow==3.9.0rc0 dspy databricks-sdk
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import json
from pathlib import Path
import mlflow

# Load configuration from setup notebook
CONFIG = json.loads(Path("config/dc_assistant.json").read_text())
# Extract configuration variables
EXPERIMENT_ID = CONFIG["mlflow"]["experiment_id"]
DATASET_NAME = CONFIG["evaluation"]["dataset_name"]
LABEL_SCHEMA_NAME = CONFIG["evaluation"]["label_schema_name"]
LABELING_SESSION_NAME = CONFIG["evaluation"]["labeling_session_name"]
ASSIGNED_USERS = CONFIG["evaluation"]["assigned_users"]
JUDGE_MODEL = CONFIG["llm"]["judge_model"]
UC_MODEL_NAME = CONFIG["llm"]["judge_model"]

mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# COMMAND ----------

import os
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

os.environ["DATABRICKS_HOST"] = w.config.host
if w.config.token:
    os.environ["DATABRICKS_TOKEN"] = w.config.token

# COMMAND ----------

# At least 10 unique example questions for evaluation dataset
example_questions = [
    "How does the 2024 Kansas City Chiefs offense approach third-and-long situations?",
    "What are the most common passing concepts used by the 2023 San Francisco 49ers in the red zone?",
    "How does the 2024 Baltimore Ravens offense adjust when facing a blitz-heavy defense?",
    "What tendencies does the 2024 Dallas Cowboys offense show on first down?",
    "Which running plays are most effective for the 2023 Cleveland Browns against a blitz?",
    "How does the 2024 Miami Dolphins offense attack Cover 2 defenses?",
    "What is the typical play sequence for the 2024 Buffalo Bills with under two minutes left in the half?",
    "How does the 2024 Green Bay Packers offense change their approach in the red zone?",
    "Which receivers are most targeted by the 2024 Los Angeles Rams on third down?",
    "How does the 2024 New England Patriots offense exploit man-to-man coverage?",
    "What are the most successful screen pass situations used by the 2024 Minnesota Vikings?",
    "How does the 2023 Seattle Seahawks offense handle aggressive defensive fronts?",
    "What is the run-pass ratio for the 2024 Tennessee Titans in short-yardage situations?",
    "How does the 2024 Philadelphia Eagles offense execute screens?",
    "Which passing plays are most effective for the 2024 Cleveland Browns against a zone defense?",
    "How do the 2023 New York Giants use play-action passes against a man-to-man defense?",
    "What are the most common target on third down and long for the 2024 Pittsburgh Steelers?",
    "How does the 2024 Arizona Cardinals offense handle a cover 2 defense?",
    "Which running plays are most effective for the 2024 Chicago Bears against a blitz?",
    "How does the 2024 Washington Commanders offense use motion?",
    "What are the most successful screen pass situations used by the 2024 Minnesota Vikings?",
    "How does the 2024 Las Vegas Raiders offense adjust their play-calling after a turnover?",
    "What are the favorite passing targets for the 2024 Jacksonville Jaguars on third and short?",
    "How does the 2024 Carolina Panthers run vs. pass on 2nd and short?",
    "What shifts or motions are frequently used by the 2024 New Orleans Saints to confuse defenses?",
    "Which running back does the 2024 Detroit Lions rely on most in redzone situations?",
    "How does the 2023 Tampa Bay Buccaneers offense respond to no blitz situations?",
    "Do the 2024 Eagles try to score quickly after a turnover?"
    "What are the most common red zone plays from the 2024 Houston Texans?",
    "How do the 2023 Chargers handle offense after a turnover?",
    "How does the 2024 Indianapolis Colts offense change formations in the 2nd half?",
    "How do the 2024 Broncos handle the end of halves?",
    "How does the 2024 Chargers offense exploit mismatches against nickel defenses?",
    "How does the 2024 Raiders offense handle 3rd and long situations?",
]

eval_dataset_records = [
    {
        "inputs": {
            "input": [
                {"role": "user", "content": question}
            ]
        }
        # Note: "expected" field is optional - can be added later via labeling session
    }
    for question in example_questions
]

print(f"Prepared {len(eval_dataset_records)} evaluation examples")
print(f"Sample structure: inputs={eval_dataset_records[0]['inputs']}")

# COMMAND ----------

from mlflow.genai import make_judge
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    ScorerSamplingConfig,
    get_scorer
)
from agent import AGENT

# Only execute this if the judge hasn't been created yet

football_language = "The response must use language that is appropriate for professional football players and coaches"
football_language_judge = Guidelines(name="football_language", guidelines=football_language)

football_analysis_judge = make_judge(
    name="football_analysis_base",
    instructions=(
        "Evaluate if the response in {{ outputs }} appropriately analyzes the available data and provides an actionable recommendation "
        "the question in {{ inputs }}. The response should be accurate, contextually relevant, and give a strategic advantage to the  "
        "person making the request. "
        "Your grading criteria should be: "
        " 1: Completely unacceptable. Incorrect data interpretation or no recommendations"
        " 2: Mostly unacceptable. Irrelevant or spurious feedback or weak recommendations provided with minimal strategic advantage"
        " 3: Somewhat acceptable. Relevant feedback provided with some strategic advantage"
        " 4: Mostly acceptable. Relevant feedback provided with strong strategic advantage"
        " 5 Completely acceptable. Relevant feedback provided with excellent strategic advantage"
    ),
    feedback_value_type=int,
    # model=JUDGE_MODEL,  # Model used to evaluate (from config)
)

scorers_list = [RelevanceToQuery(), football_analysis_judge, football_language_judge]

# Register judge to experiment

try:
    registered_base_judge = football_analysis_judge.register(
        experiment_id=EXPERIMENT_ID
    )

except ValueError as e:
    msg = str(e)

    if "has already been registered" in msg:
        # Preferred path per the error message: update existing scorer
        registered_base_judge = football_analysis_judge.update(
            experiment_id=EXPERIMENT_ID,
            sampling_config=ScorerSamplingConfig(sample_rate=1)
        )
    else:
        raise


# COMMAND ----------

from agent import AGENT
from mlflow.genai import evaluate

results = evaluate(
    data=eval_dataset_records,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=scorers_list
)

# COMMAND ----------

# Grab the trace_id for all observations that have state of OK and apply the tag of eval: data
ok_trace_ids = results.result_df.loc[results.result_df["state"] == "OK", "trace_id"]
print(f'Number of traces with OK status: {len(ok_trace_ids)}')

for trace_id in ok_trace_ids:
    mlflow.set_trace_tag(trace_id=trace_id, key="eval", value="complete")

# COMMAND ----------

from mlflow.genai.datasets import create_dataset, get_dataset, delete_dataset
from mlflow.exceptions import MlflowException

# Step 1: Create an empty evaluation dataset
# The dataset will be created in Unity Catalog at the specified schema
try:
    delete_dataset(name=DATASET_NAME)
except Exception as e:
    print(f"Caught exception: {type(e).__name__}: {e}")

try:
    eval_dataset = get_dataset(name=DATASET_NAME)
except:
    eval_dataset = create_dataset(
        name=DATASET_NAME,
    )

print(f" Configured evaluation dataset: {eval_dataset.name}")

# Step 3: Grab all traces with tag "eval: data" and add them to the dataset
print("\nSearching for traces with tag 'eval: complete'...")
traces_with_tag = mlflow.search_traces(
    locations=[EXPERIMENT_ID],
    filter_string="tag.eval = 'complete'",
    return_type="pandas"
)

print(f"Found {len(traces_with_tag)} traces with tag 'eval: complete'")

# Convert dataset to align with inputs needed for merge_traces()

if 'inputs' not in traces_with_tag.columns and 'request' in traces_with_tag.columns:
    print("Renaming 'request' column to 'inputs'...")
    traces_with_tag = traces_with_tag.rename(columns={'request': 'inputs'})

# 2. Conditionally rename 'response' -> 'outputs'
if 'outputs' not in traces_with_tag.columns and 'response' in traces_with_tag.columns:
    print("Renaming 'response' column to 'outputs'...")
    traces_with_tag = traces_with_tag.rename(columns={'response': 'outputs'})

eval_dataset = eval_dataset.merge_records(traces_with_tag)

# COMMAND ----------

from mlflow.genai import create_labeling_session, get_review_app
from mlflow.genai import label_schemas

# Step 4a: Create label schemas for collecting feedback
# Label schemas define the questions/format for domain experts to provide feedback
# Create a custom schema that matches the football_analysis_judge criteria (1-5 scale)
# Reference: https://mlflow.org/docs/latest/api_reference/_modules/mlflow/genai/label_schemas.html#create_label_schema

# Create football analysis feedback schema matching the judge's 1-5 scale
LABEL_SCHEMA_NAME = "football_analysis_base"
football_analysis_schema = label_schemas.create_label_schema(
    name=LABEL_SCHEMA_NAME,
    type="feedback",
    title=LABEL_SCHEMA_NAME,
    input=label_schemas.InputCategorical(
        options=["1", "2", "3", "4", "5"]   # these will be stored as strings
    ),
    instruction=(
        "Evaluate if the response appropriately analyzes the available data and provides an actionable recommendation "
        "for the question. The response should be accurate, contextually relevant, and give a strategic advantage to the "
        "person making the request. "
        "\n\n Your grading criteria should be: "
        "\n 1: Completely unacceptable. Incorrect data interpretation or no recommendations"
        "\n 2: Mostly unacceptable. Irrelevant or spurious feedback or weak recommendations provided with minimal strategic advantage"
        "\n 3: Somewhat acceptable. Relevant feedback provided with some strategic advantage"
        "\n 4: Mostly acceptable. Relevant feedback provided with strong strategic advantage"
        "\n 5: Completely acceptable. Relevant feedback provided with excellent strategic advantage"
    ),
    enable_comment=True,  # Allow additional comments/feedback
    overwrite=True,
)

# Create a labeling session with label schemas
# The experiment is automatically inferred from the current active MLflow experiment
# Include the agent so it can generate responses for domain experts to review and label
UC_MODEL_NAME = CONFIG["model"]["uc_model_name"]
AGENT_NAME = f"agents_{UC_MODEL_NAME.replace('.', '-')}"
MODEL_NAME = UC_MODEL_NAME.split('.')[-1]
review_app = get_review_app(experiment_id=EXPERIMENT_ID)

# Add the agent to the review app
# The model_serving_endpoint is the UC model name (e.g., "users.wesley_pasfield.dc_assistant")
# This is the endpoint where the agent is deployed
review_app = review_app.add_agent(
    agent_name=MODEL_NAME,
    model_serving_endpoint=AGENT_NAME,  # UC model name is the serving endpoint
    overwrite=True,  # Overwrite if agent already exists
)

# COMMAND ----------

# Create the labeling session & add the traces for evaluation

labeling_session = create_labeling_session(
    name=f'{LABELING_SESSION_NAME}_sme',
    assigned_users=ASSIGNED_USERS,
    #agent=UC_MODEL_NAME,  # Use the deployed agent to generate responses for labeling
    label_schemas=[LABEL_SCHEMA_NAME],  # Required: define what feedback to collect
)
# Add the dataset to the labeling session
labeling_session = labeling_session.add_dataset(
    dataset_name=DATASET_NAME
)
print(f"Created labeling session: {labeling_session.name}")
print(f"Labeling session ID: {labeling_session.labeling_session_id}")
print(f"Assigned users: {labeling_session.assigned_users}")
print(f"Labeling session URL: {labeling_session.url}")

# COMMAND ----------

# MAGIC %md
# MAGIC # Once the Labeling Sessions are done move to judge alignment

# COMMAND ----------

traces_for_alignment = mlflow.search_traces(
    locations=[EXPERIMENT_ID], 
    filter_string="tag.eval = 'complete'",  # Filter by the tag added during evaluation
    # return_type="list",
    max_results=32
    )

# COMMAND ----------

traces_for_alignment['assessments'][0]

# COMMAND ----------

