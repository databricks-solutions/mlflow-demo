# Databricks notebook source
# MAGIC %md
# MAGIC # Prompt Optimization
# MAGIC
# MAGIC - Now that we have calibrated a judge, let's leverage that judge to optimize our feedback
# MAGIC - This closes the loop - we are directly integrating SME feedback into our judges & then optimizing our agent with a prompt that is optimized based on the SME-calibrated judge

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow==3.9.0rc0 dspy
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import mlflow
from mlflow.genai.optimize import GepaPromptOptimizer
from mlflow.genai.scorers import Correctness
from mlflow.genai.datasets import create_dataset
import json
from pathlib import Path

CONFIG = json.loads(Path("config/dc_assistant.json").read_text())

# Extract configuration variables
EXPERIMENT_ID = CONFIG["mlflow"]["experiment_id"]
ALIGNED_JUDGE_NAME = CONFIG["judges"]["aligned_judge_name"]
PROMPT_NAME = CONFIG["prompt_registry"]["prompt_name"]
REFLECTION_MODEL = CONFIG["prompt_registry"]["reflection_model"]
OPTIMIZATION_DATASET_NAME = CONFIG["optimization"]["optimization_dataset_name"]
CATALOG = CONFIG["workspace"]["catalog"]
SCHEMA = CONFIG["workspace"]["schema"]

# Set the MLflow experiment
mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# COMMAND ----------

# Load configuration from setup notebook


# Register initial prompt for classifying medical paper sections

optimization_dataset = [
    {
        "inputs": {
            "input": [
                 {"role": "user", "content": "Who are the primary ball carriers for the 2024 Detroit Lions on 3rd and short?"},
          ]
        },
        "expectations": {
            "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_by_down_distance` with arguments for the Detroit Lions, 2024 season, 3rd down, and short distance. The response should list key players like David Montgomery or Jahmyr Gibbs and their involvement and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What are the tendency of the 2024 San Francisco 49ers in a 2 minute drill?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_two_minute_drill` with `team='SF'`, `season=2024`. The response should analyze their play selection (pass vs run) and pace during 2-minute situations and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How effective are screen passes for the 2024 Miami Dolphins?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.screen_play_tendencies` with `team='MIA'`, `season=2024`. The response should provide stats on screen play frequency and success and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What do the 2024 Philadelphia Eagles tend to do on 1st down?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_by_down_distance` with `team='PHI'`, `season=2024`, `down=1`. The response should breakdown run/pass ratios and preferred play types on first down and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "Who gets the ball when the 2024 Dallas Cowboys are in the red zone?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_by_offense_situation` with `team='DAL'`, `season=2024`. The response should identify targets specifically in the red zone context and give tactical recommendations for how the defense should react. If there are any data quality issues related to red zone data that should be explicitly stated to the end user."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What are the redzone tendencies of the Buffalo Bills offense?"}]
        },
        "expectations": {
             "expected_response": f"The agent should assume season 2024. It should call general tendency tools like `{CATALOG}.{SCHEMA}.tendencies_by_down_distance` or `{CATALOG}.{SCHEMA}.tendencies_by_drive_start` to give an overview of the offense and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How do the 2024 Bills use motion?"}]
        },
        "expectations": {
             "expected_response": "The agent should identify and articulate that it doesn't have access to motion data, and offer alternative options of data pulls to make."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How does the 2024 Kansas City Chiefs offense perform against the blitz?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.success_by_pass_rush_and_coverage` with `team='KC'`, `season=2024`. Analyze performance vs pressure and give overall success metrics by different strategies and give tactical recommendations for how the defense should react."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How do the 2024 LA Rams play in the second half?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_by_score_2nd_half` with `team='LA'`, `season=2024`. Analyze if they are conservative or aggressive based on score and give tactical recommendations for how the defense should react.."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What formations does the 2024 Green Bay Packers offense prefer?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_by_offense_formation` with `team='GB'`, `season=2024`. The response should detail the most common formations and their usage rates and give tactical recommendations for defensive adjustments."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "Who gets the ball on 3rd and long for the 2024 Minnesota Vikings?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_by_down_distance` with `team='MIN'`, `season=2024`, `down=3`, and long distance parameters. The response should identify key receivers and their target share and give tactical recommendations for coverage schemes."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What are the 2024 Seattle Seahawks' tendencies when starting a drive in their own territory?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_by_drive_start` with `team='SEA'`, `season=2024`. The response should analyze play-calling patterns based on field position and give tactical recommendations for defensive game planning."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How do the 2023 Tampa Bay Buccaneers attack defenses in 2 minute drills?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_two_minute_drill` with `team='TB'`, `season=2024`. The response should identify primary targets and route concepts used in hurry-up situations and give tactical recommendations for coverage adjustments."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What's the Baltimore Ravens run game strategy on 2nd and short in 2024?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_by_down_distance` with `team='BAL'`, `season=2024`, `down=2`, and short distance. The response should detail rushing personnel and tendency rates and give tactical recommendations for run defense alignment."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "Which formations does the Cincinnati Bengals use most when they're trailing?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.tendencies_by_offense_formation` with `team='CIN'`, `season=2024`. It may also call `{CATALOG}.{SCHEMA}.tendencies_by_score_2nd_half` to filter by trailing scenarios. The response should detail formation preferences when behind and give tactical recommendations, and emphasize that it does not have a perfect tool to answer that strategy"
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What pass rush strategies work best against the 2024 New York Jets offense?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `u{CATALOG}.{SCHEMA}.success_by_pass_rush_and_coverage` with `team='NYJ'`, `season=2024`. The response should detail which pass rush schemes are most effective and give tactical recommendations for defensive coordinator playcalling."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "How does the 2023 Arizona Cardinals offense distribute the ball out of 11 personnel?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.who_got_ball_by_down_distance_and_form` with `team='ARI'`, `season=2024`, and 11 personnel parameters. The response should identify target distribution from that formation and give tactical recommendations for defensive personnel matching."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "Tell me about the 2024 New Orleans Saints screen game effectiveness"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.screen_play_tendencies` with `team='NO'`, `season=2024`. The response should provide frequency, success rate, and preferred screen concepts and give tactical recommendations for screen defense."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "Tell me about the 2024 New Orleans Saints preferences after getting a turnover"}]
        },
        "expectations": {
             "expected_response": f"The agent should call `{CATALOG}.{SCHEMA}.first_play_after_turnover` with `team='NO'`, `season=2024`. The response should provide frequency, success rate, and preferred screen concepts and comment on aggressiveness, and give tactical recommendations for defenses in these situations."
        }
    },
    {
        "inputs": {
             "input": [
                  {"role": "user", "content": "What are the 2024 Washington Commanders 1st down tendencies from different field positions?"}]
        },
        "expectations": {
             "expected_response": f"The agent should call both `{CATALOG}.{SCHEMA}.tendencies_by_down_distance` with `team='WAS'`, `season=2024`, `down=1` AND `{CATALOG}.{SCHEMA}.tendencies_by_drive_start` to correlate first down play calls with field position. The response should provide comprehensive tendency analysis and give tactical recommendations for situational defense."
        }
    }
]

# Save optimization dataset to MLflow GenAI dataset
print(f"Creating MLflow GenAI dataset: {OPTIMIZATION_DATASET_NAME}")
optimization_dataset_mlflow = create_dataset(
    name=OPTIMIZATION_DATASET_NAME,
)
print(f"Created optimization dataset: {optimization_dataset_mlflow.name}")

# Add records to the dataset
optimization_dataset_mlflow = optimization_dataset_mlflow.merge_records(optimization_dataset)
print(f"Added {len(optimization_dataset)} records to optimization dataset")


# COMMAND ----------

from mlflow.genai.scorers import get_scorer, RelevanceToQuery

# Load aligned judge using config variables (already loaded in previous cell)
aligned_judge = get_scorer(name=f"{ALIGNED_JUDGE_NAME}_memalign", experiment_id=EXPERIMENT_ID)
print(aligned_judge.instructions)

# COMMAND ----------

from agent import AGENT, SYSTEM_PROMPT
import copy
from typing import List, Dict, Any
import warnings
import logging

# Suppress warnings comprehensively
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
logging.getLogger('mlflow.genai.judges.instructions_judge').setLevel(logging.ERROR)

# Load prompt using config variables (already loaded in previous cells)
print(f"Loading prompt: {PROMPT_NAME} - using current production prompt")
system_prompt = mlflow.genai.load_prompt(f"prompts:/{PROMPT_NAME}@production")
print(f"✅ Loaded prompt: {system_prompt.uri}")

# Define objective function to convert Feedback to numerical scores
candidate_counter = {"count": 0, "current_prompt": None, "scores": []}

def objective_function(scores: dict) -> float:
    """
    Extract the numerical score from the judge's Feedback object.
    
    The judge returns a Feedback object with feedback.value as a string (e.g., '5').
    We need to convert this to a float for GEPA optimization.
    """
    feedback = scores.get(f"{ALIGNED_JUDGE_NAME}_memalign")
    
    # Extract the float value from the Feedback object
    if feedback and hasattr(feedback, 'feedback') and hasattr(feedback.feedback, 'value'):
        try:
            raw_score = float(feedback.feedback.value)
            
            # Normalize to 0-1 range for GEPA (which assumes 1.0 is perfect)
            normalized_score = raw_score / 5.0
            print(normalized_score)
            
            # Track raw scores for human readability
            candidate_counter["scores"].append(raw_score)
            
            # Print summary when we've completed evaluating all examples for one candidate
            if len(candidate_counter["scores"]) == len(optimization_dataset):
                avg_score = sum(candidate_counter["scores"]) / len(candidate_counter["scores"])
                candidate_counter["count"] += 1
                print(f"\n✅ Candidate #{candidate_counter['count']} Average Score: {avg_score:.2f}/5.0")
                candidate_counter["scores"] = []  # Reset for next candidate
            
            return normalized_score
        except (ValueError, TypeError) as e:
            logging.warning(f"Could not convert feedback value to float: {e}")
            return 0.6  # Default to middle score (3.0/5.0)
    
    # Fallback
    return 0.6

# Define predict_fn following the exact pattern from MLflow docs
last_prompt_hash = {"hash": None}

def predict_fn(input):
    """Predict function that uses the agent with the MLflow prompt."""
    # Load the current prompt version (will be optimized during the process)
    prompt = mlflow.genai.load_prompt(system_prompt.uri)
    
    # Use prompt.format() to ensure MLflow tracks usage
    system_content = prompt.format()
    
    # Check if the prompt has changed
    current_hash = hash(system_content)
    if last_prompt_hash["hash"] != current_hash:
        last_prompt_hash["hash"] = current_hash
        print(f"\n🆕 NEW PROMPT CANDIDATE DETECTED!")
        print(f"📝 Prompt (first 10000 chars): {system_content[:10000]}...")
        print(f"📏 Full length: {len(system_content)} characters\n")
    
    # Extract the user message from the input list
    user_message = input[0]['content']
    
    # Create input messages as a simple list of dicts
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_message}
    ]
    
    # Call the agent with the input dict structure
    response = AGENT.predict({"input": messages})
    # Return the text output
    return response

# Optimize the prompt
result = mlflow.genai.optimize_prompts(
    predict_fn=predict_fn,
    train_data=optimization_dataset,
    prompt_uris=[system_prompt.uri],
    optimizer=GepaPromptOptimizer(
        reflection_model=REFLECTION_MODEL, 
        display_progress_bar=True,
    ),
    scorers=[aligned_judge],
    aggregation=objective_function,
)

# Use the optimized prompt
optimized_prompt = result.optimized_prompts[0]
print(f"\n" + "="*80)
print("OPTIMIZATION COMPLETE")
print("="*80)
print(f"\nOptimized template:\n{optimized_prompt.template}")
print(f"\nInitial score: {result.initial_eval_score if hasattr(result, 'initial_eval_score') else 'N/A'}")
print(f"Final score: {result.final_eval_score if hasattr(result, 'final_eval_score') else 'N/A'}")
prod_var = 'prod' if result.final_eval_score > result.initial_eval_score else 'no_action'

# COMMAND ----------

print(optimized_prompt.template)

# COMMAND ----------

# Register this new version as production in prompt registry

system_prompt = mlflow.genai.register_prompt(
    name=PROMPT_NAME,
    template=optimized_prompt.template,
    commit_message=f"Post optimize_prompts optimizatio using {ALIGNED_JUDGE_NAME}",
    tags={"finalscore": str(result.final_eval_score), "optimization": "GEPA", "judge": ALIGNED_JUDGE_NAME},
    )

print(system_prompt)

# COMMAND ----------

# MAGIC %md
# MAGIC # Optional - Execute Another Evaluation Job to compare performance
# MAGIC
# MAGIC - The GEPA optimization process validates that the new prompt exceed the performance of the prior prompt
# MAGIC - if you have multiple judges or a separate evaluation set, you can rerun evaluation jobs with the old prompt, and the prompt produced by GEPA
# MAGIC - The concept in general is to only promote a new version of the prompt if it exceeds performance of the prior prompt
# MAGIC - In this example - we will just promote the prompt to the production alias based on superior performance in the GEPA/prompt optimization step
# MAGIC - After registering the new prompt - redeploy the endpoint by creating a new version of the endpoint, and re-deploy to production (I think?)

# COMMAND ----------

def prompt_promotion(prompt_name, prod_gate, new_prompt):
  if prod_gate == 'prod':
    mlflow.genai.set_prompt_alias(
        name=f"{PROMPT_NAME}",
        alias="production",
        version=new_prompt.version
    )
    print(f"Registered {prompt_name} as production version {new_prompt.version}")
  else:
    print("No improvement in prompt score, production alias not updated")

prompt_promotion(PROMPT_NAME, prod_var, system_prompt)
