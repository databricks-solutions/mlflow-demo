# Databricks notebook source
# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow==3.9.0rc0 dspy
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC #Pull the Traces with Feedback
# MAGIC
# MAGIC We need the feedback you put in during the review app to align judges. 
# MAGIC
# MAGIC First we will set up a list of traces with your feedback

# COMMAND ----------

import json
from pathlib import Path
import mlflow
from mlflow.genai.datasets import get_dataset

CONFIG = json.loads(Path("config/dc_assistant.json").read_text())

# Extract configuration variables
EXPERIMENT_ID = CONFIG["mlflow"]["experiment_id"]
DATASET_NAME = CONFIG["evaluation"]["dataset_name"]
JUDGE_MODEL = CONFIG["llm"]["judge_model"]
REFLECTION_MODEL = CONFIG["prompt_registry"]["reflection_model"]

# Set the MLflow experiment
mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# COMMAND ----------

traces_for_alignment = mlflow.search_traces(
    experiment_ids=[EXPERIMENT_ID],
    # optionally keep your tag filter, but it’s not sufficient by itself
    filter_string="tag.eval = 'complete'",
    return_type="list",
    max_results=35,  # use 100+ if you can
)

valid_traces = []
for trace in traces_for_alignment:
    feedbacks = trace.search_assessments(name="football_analysis_base")
    has_judge = any(f.source.source_type == "LLM_JUDGE" for f in feedbacks)
    has_human = any(f.source.source_type == "HUMAN" for f in feedbacks)
    if has_judge and has_human:
        valid_traces.append(trace)

print("candidate:", len(traces_for_alignment), "valid:", len(valid_traces))


# COMMAND ----------

# MAGIC %md
# MAGIC #Judge Alignment
# MAGIC
# MAGIC In this tutorial, we will demonstrate two Judge Alignment optimizers: SIMBA and MemAlign. 
# MAGIC
# MAGIC ###MemAlign 
# MAGIC is a lightweight, dual-memory framework designed to align LLM judges with human experts by efficiently learning from a small amount of natural language feedback, offering a faster and cheaper alternative to traditional prompt engineering or fine-tuning. The system uses Semantic Memory for general principles and Episodic Memory for specific examples, allowing for rapid adaptation and showing visible improvement with as few as 2-10 examples. This approach delivers competitive or better quality than state-of-the-art prompt optimizers at up to 100x lower latency and 10x lower cost, and it is now the default optimization algorithm in MLflow's align() method in MLflow 3.9+
# MAGIC
# MAGIC ###SIMBA 
# MAGIC (Stochastic Introspective Mini-Batch Ascent) is a DSPy prompt-optimization method that iteratively improves an LLM’s prompts by evaluating changes on mini-batches with a target metric. It uses a stochastic hill-climbing loop that proposes prompt edits (including instruction rewrites and/or few-shot demonstrations) and keeps the variants that score better. Its “introspective” step leverages the LLM to analyze failures and generate corrective guidance, reducing manual prompt tuning for complex tasks. It was the default optimizer for mlflow.align() in MLflow 3.8 or below and can still be used today.

# COMMAND ----------

# MAGIC %md
# MAGIC #Load Judge we want to Align

# COMMAND ----------

# Load the base judge from the evaluation notebook and define configuration parameters
from mlflow.genai.scorers import get_scorer

# SIMBA configuration parameters
LIKERT_MIN = 1.0  # Minimum Likert scale value
LIKERT_MAX = 5.0  # Maximum Likert scale value
SIMBA_BATCH_SIZE = 8  # Number of examples per SIMBA optimization step
SIMBA_MAX_DEMOS = 0  # Maximum few-shot demos (0 recommended for situations where exact matches on responses are not really possible)
SIMBA_VERBOSE = True  # Enable verbose logging for SIMBA optimization

# Load the base football analysis judge from the evaluation notebook
# Reference: https://mlflow.org/docs/latest/api_reference/python_api/mlflow.genai.html#mlflow.genai.scorers.get_scorer
judge_name = CONFIG.get("evaluation", {}).get("judge_name", "football_analysis_base")
football_analysis_judge = get_scorer(name=judge_name)

# Define the aligned judge name (can be customized in config if needed)
ALIGNED_JUDGE_NAME = CONFIG.get("evaluation", {}).get("aligned_judge_name", "football_analysis_judge_align")

print(f"Loaded base judge from evaluation notebook: {judge_name}")
print(f"Aligned judge name: {ALIGNED_JUDGE_NAME}")
print(f"SIMBA config: batch_size={SIMBA_BATCH_SIZE}, max_demos={SIMBA_MAX_DEMOS}, Likert range=[{LIKERT_MIN}, {LIKERT_MAX}]")


# COMMAND ----------

# MAGIC %md
# MAGIC #SIMBA Implementation
# MAGIC
# MAGIC Below is a basic Judge Alignment using the default SIMBA implementation from MLflow. 

# COMMAND ----------

# MAGIC %md
# MAGIC #Regular SIMBA Optimization

# COMMAND ----------

import logging
from mlflow.genai.judges.optimizers import SIMBAAlignmentOptimizer
from statistics import mean
from typing import Any, Callable, List

from mlflow.genai.judges.base import AlignmentOptimizer, Judge
from mlflow.entities.trace import Trace

logging.getLogger("mlflow.genai.judges.optimizers.simba").setLevel(logging.DEBUG)

print(f'Initial Judge Text /n {football_analysis_judge.instructions}')

aligned_judge_basic = football_analysis_judge.align(
    traces=valid_traces,
    optimizer=SIMBAAlignmentOptimizer(model=REFLECTION_MODEL),
)

# COMMAND ----------

print("Original instructions:\n", football_analysis_judge.instructions)
print("\nAligned instructions:\n", aligned_judge_basic.instructions)

# COMMAND ----------

from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    ScorerSamplingConfig,
    get_scorer
)

register_align_judge_basic = make_judge(
    name=f"{ALIGNED_JUDGE_NAME}_basic",
    instructions=aligned_judge_basic.instructions,
    feedback_value_type=float,
    # model=JUDGE_MODEL,  # Model used to evaluate (from config)
)

try:
    register_aligned_judge_basic = register_align_judge_basic.register(experiment_id=EXPERIMENT_ID)

except ValueError as e:
    msg = str(e)

    if "has already been registered" in msg:
        # Preferred path per the error message: update existing scorer
        register_aligned_judge = register_align_judge_basic.update(
            experiment_id=EXPERIMENT_ID,
            sampling_config=ScorerSamplingConfig(sample_rate=1)
        )
    else:
        raise

print("Registered aligned judge", register_aligned_judge_basic.name)

# COMMAND ----------

# MAGIC %md
# MAGIC ###Rerun with SIMBA Optimized Judge

# COMMAND ----------

from agent import AGENT
from mlflow.genai import evaluate
from mlflow.genai.datasets import create_dataset, get_dataset
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    get_scorer,
)

# Compile the judges and rerun the evaluation job

football_language = "The response must use language that is appropriate for professional football players and coaches"
football_language_judge = Guidelines(name="football_language", guidelines=football_language)

scorers = [RelevanceToQuery(), football_language_judge, register_aligned_judge_basic]
# Rerun the evaluation after recreating the judge to better calibrate the agent quality

mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# Grab all traces from the original eval dataset
eval_dataset = get_dataset(name=DATASET_NAME)

def extract_question(row_input):
    try:
      messages = row_input['request']['input']
      last_message = messages[-1]
      return last_message['content']
    except Exception as e:
      print(e)

df = eval_dataset.to_df()
eval_dataset_records = [
    {
        "inputs": {
            "input": [
                # Pass the EXTRACTED string, not the whole dictionary object
                {"role": "user", "content": extract_question(row)}
            ]
        }
        # Note: "expected" field is optional
    }
    for row in df['inputs'] 
]

print("Executing Evaluation Job")
results = evaluate(
    data=eval_dataset_records,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=scorers
)

# COMMAND ----------

# MAGIC %md
# MAGIC #MemAlign Optimizer 
# MAGIC
# MAGIC Mlflow's default optimizer

# COMMAND ----------

import logging
import os
import dspy
from mlflow.genai.judges.optimizers import MemAlignOptimizer
from statistics import mean
from typing import Any, Callable, List

from mlflow.genai.judges.base import AlignmentOptimizer, Judge
from mlflow.entities.trace import Trace

# os.environ["OPENAI_API_KEY"] = "" 
dspy.configure(cache=False) 

print(f'Initial Judge Text /n {football_analysis_judge.instructions}')

aligned_judge_memalign = football_analysis_judge.align(
    traces=valid_traces,
    optimizer=MemAlignOptimizer(reflection_lm="databricks:/databricks-claude-opus-4-5", embedding_model="openai/text-embedding-3-large",) #Databricks not supported right now
)

# COMMAND ----------

print("Original instructions:\n", football_analysis_judge.instructions)
print("\nAligned instructions:\n", aligned_judge_memalign.instructions)

# COMMAND ----------

from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    ScorerSamplingConfig,
    get_scorer
)

register_align_judge_memalign = make_judge(
    name=f"{ALIGNED_JUDGE_NAME}_memalign",
    instructions=aligned_judge_memalign.instructions,
    feedback_value_type=float,
    # model=JUDGE_MODEL,  # Model used to evaluate (from config)
)

try:
    register_aligned_judge_memalign = register_align_judge_memalign.register(experiment_id=EXPERIMENT_ID)
    print("Registered aligned judge", register_aligned_judge_memalign.name)

except ValueError as e:
    msg = str(e)

    if "has already been registered" in msg:
        # Preferred path per the error message: update existing scorer
        register_aligned_judge = register_align_judge_memalign.update(
            experiment_id=EXPERIMENT_ID,
            sampling_config=ScorerSamplingConfig(sample_rate=1)
        )
    else:
        raise



# COMMAND ----------

# MAGIC %md
# MAGIC ###Run the MemAlign Aligned Judge

# COMMAND ----------

from agent import AGENT
from mlflow.genai import evaluate
from mlflow.genai.datasets import create_dataset, get_dataset
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    get_scorer,
)

# Compile the judges and rerun the evaluation job

football_language = "The response must use language that is appropriate for professional football players and coaches"
football_language_judge = Guidelines(name="football_language", guidelines=football_language)

scorers = [RelevanceToQuery(), football_language_judge, register_align_judge_memalign]
# Rerun the evaluation after recreating the judge to better calibrate the agent quality

mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# Grab all traces from the original eval dataset
eval_dataset = get_dataset(name=DATASET_NAME)

def extract_question(row_input):
    try:
      messages = row_input['request']['input']
      last_message = messages[-1]
      return last_message['content']
    except Exception as e:
      print(e)

df = eval_dataset.to_df()
eval_dataset_records = [
    {
        "inputs": {
            "input": [
                # Pass the EXTRACTED string, not the whole dictionary object
                {"role": "user", "content": extract_question(row)}
            ]
        }
        # Note: "expected" field is optional
    }
    for row in df['inputs'] 
]

print("Executing Evaluation Job")
results = evaluate(
    data=eval_dataset_records,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=scorers
)

# COMMAND ----------

# MAGIC %md
# MAGIC #Likert SIMBA Optimizer
# MAGIC
# MAGIC MLflow allows you to build or create a new optimizer using `AlignmentOptimizer`. To demonstrate this, we have created a Likert-aware SIMBA optimizer below to improve its optimization 

# COMMAND ----------

# Likert-aware SIMBA optimizer: single-cell implementation

import logging
from statistics import mean
from typing import Any, Callable, List

from mlflow.genai.judges.base import AlignmentOptimizer, Judge
from mlflow.entities.trace import Trace
from mlflow.genai.judges.optimizers import SIMBAAlignmentOptimizer as _BaseSIMBA

# Use configuration parameters for Likert scale
def _to_float_maybe(x: Any) -> float | None:
    try:
        return float(x)
    except Exception:
        return None

def likert_agreement_metric(example: Any, prediction: Any) -> float:
    """
    Likert agreement metric:
        score = 1 - |llm - human| / (LIKERT_MAX - LIKERT_MIN)

    Reads from:
      - Human label: example._store["result"]
      - LLM/judge score: prediction._store["result"]
    """
    logger = logging.getLogger("dspy.teleprompt.simba")

    human = None
    llm = None

    # Primary: read from example._store / prediction._store
    ex_store = getattr(example, "_store", None)
    if isinstance(ex_store, dict) and "result" in ex_store:
        human = _to_float_maybe(ex_store["result"])

    pred_store = getattr(prediction, "_store", None)
    if isinstance(pred_store, dict) and "result" in pred_store:
        llm = _to_float_maybe(pred_store["result"])

    # Fallbacks
    if human is None:
        for key in ("human_score", "human_value", "label", "target", "score", "y"):
            if hasattr(example, key):
                human = _to_float_maybe(getattr(example, key))
                if human is not None:
                    break
            if isinstance(example, dict) and key in example:
                human = _to_float_maybe(example[key])
                if human is not None:
                    break

    if llm is None:
        if isinstance(prediction, dict):
            for k in ("llm_score", "value", "score", "rating", "label", "y_hat"):
                if k in prediction:
                    llm = _to_float_maybe(prediction[k])
                    if llm is not None:
                        break
        if llm is None:
            llm = _to_float_maybe(prediction)

    if human is None or llm is None:
        logger.info(
            "LIKERT: missing scores (human=%r, llm=%r) -> 0.0",
            human,
            llm,
        )
        return 0.0

    # Clamp to configured Likert range
    human = max(LIKERT_MIN, min(LIKERT_MAX, human))
    llm = max(LIKERT_MIN, min(LIKERT_MAX, llm))

    score = max(0.0, 1.0 - abs(llm - human) / (LIKERT_MAX - LIKERT_MIN))
    return score


class LikertSIMBAAlignmentOptimizer(AlignmentOptimizer):
    """Unified optimizer: injects Likert metric, batch size, max_demos, and optional verbose logging.

    Uses configuration parameters from the config cell above.
    """

    def __init__(
        self,
        model: str,
        batch_size: int = 10,
        max_demos: int = 0,
        metric_fn: Callable[[Any, Any], float] = None,
        verbose: bool = False,
    ):
        self.model = model
        self.batch_size = batch_size
        self.max_demos = max_demos
        self.metric_fn = metric_fn
        self.verbose = verbose

    # ---- Internal helpers for verbose logging ----
    class _BatchScoreAggregator:
        def __init__(self):
            self.all_batches: List[List[float]] = []
            self.current: List[float] = []
            self.batch_idx: int = 0

        def start_batch(self):
            if self.current:
                self._log_current_summary()
                self.all_batches.append(self.current)
            self.current = []
            self.batch_idx += 1

        def add(self, score: float):
            if isinstance(score, (int, float)):
                self.current.append(float(score))

        def end(self):
            if self.current:
                self._log_current_summary()
                self.all_batches.append(self.current)
                self.current = []
            all_flat = [s for batch in self.all_batches for s in batch]
            if all_flat:
                best = max(all_flat)
                batches_n = len(self.all_batches)
                logging.getLogger("dspy.teleprompt.simba").info(
                    "Scores after %d batches: %s, Best: %s",
                    batches_n,
                    [round(mean(b), 3) if b else 0.0 for b in self.all_batches],
                    round(best, 3),
                )

        def _log_current_summary(self):
            lg = logging.getLogger("dspy.teleprompt.simba")
            if not self.current:
                return
            mx = max(self.current)
            mn = min(self.current)
            avg = mean(self.current)
            lg.info(
                "Processing bucket #%d, with max score %s, max-to-min gap %s, and max-to-avg gap %s.",
                self.batch_idx if self.batch_idx else 1,
                round(mx, 3),
                round(mx - mn, 3),
                round(mx - avg, 3),
            )

    class _SIMBABatchLogHandler(logging.Handler):
        def __init__(self, aggregator: "LikertSIMBAAlignmentOptimizer._BatchScoreAggregator"):
            super().__init__()
            self.aggregator = aggregator

        def emit(self, record: logging.LogRecord):
            msg = record.getMessage()
            if "Starting batch" in msg and "of" in msg:
                self.aggregator.start_batch()

    def _wrap_metric_for_logging(self, metric_fn: Callable[[Any, Any], float]):
        aggregator = self._BatchScoreAggregator()

        def logged_metric(example, prediction):  
            score = metric_fn(example, prediction)
            aggregator.add(score)
            return score

        batch_handler = self._SIMBABatchLogHandler(aggregator)
        simba_logger = logging.getLogger("dspy.teleprompt.simba")
        simba_utils_logger = logging.getLogger("dspy.teleprompt.simba_utils")
        simba_logger.setLevel(logging.INFO)
        simba_utils_logger.setLevel(logging.INFO)
        if all(not isinstance(h, LikertSIMBAAlignmentOptimizer._SIMBABatchLogHandler) for h in simba_logger.handlers):
            simba_logger.addHandler(batch_handler)
        return logged_metric, aggregator, simba_logger, batch_handler

    def align(self, judge: Judge, traces: list[Trace]) -> Judge:
        import dspy.teleprompt.simba as dsimba

        # Choose metric function
        metric_fn = self.metric_fn if self.metric_fn is not None else likert_agreement_metric
        logging.getLogger("dspy.teleprompt.simba").info(
            "Using SIMBA metric_fn=%s",
            getattr(metric_fn, "__name__", repr(metric_fn)),
        )
        
        # Optionally wrap metric for verbose logging
        aggregator = None
        simba_logger = None
        batch_handler = None
        if self.verbose:
            metric_fn, aggregator, simba_logger, batch_handler = self._wrap_metric_for_logging(metric_fn)

        # Patch DSPy SIMBA init to inject our parameters
        original_init = dsimba.SIMBA.__init__
        batch_size = self.batch_size
        max_demos = self.max_demos

        def patched_init(self_, *args, **kwargs): 
            # Force our settings
            logging.getLogger("dspy.teleprompt.simba").info(
                "Patched SIMBA.__init__: forcing metric_fn=%s, bsize=%s, max_demos=%s",
                getattr(metric_fn, "__name__", repr(metric_fn)),
                batch_size,
                max_demos,
            )

            kwargs["metric"] = metric_fn
            kwargs["bsize"] = batch_size
            kwargs["max_demos"] = max_demos

            return original_init(self_, *args, **kwargs)

        dsimba.SIMBA.__init__ = patched_init
        try:
            base = _BaseSIMBA(model=self.model)
            result = base.align(judge=judge, traces=traces)
        finally:
            dsimba.SIMBA.__init__ = original_init
            if aggregator is not None:
                aggregator.end()
            if simba_logger is not None and batch_handler is not None:
                try:
                    simba_logger.removeHandler(batch_handler)
                except Exception:
                    pass
        return result

print("Likert SIMBA optimizer loaded successfully")


# COMMAND ----------

# MAGIC %md
# MAGIC ###Run Optimization with LikertSIMBAOptimizer
# MAGIC
# MAGIC This will take a few minutes

# COMMAND ----------

logging.getLogger("mlflow.genai.judges.optimizers.simba").setLevel(logging.DEBUG)

print(f'Initial Judge Text /n {football_analysis_judge.instructions}')

likert_optimizer = LikertSIMBAAlignmentOptimizer(
    model=REFLECTION_MODEL,
    batch_size=6,
    max_demos=0,
    verbose=True
)

aligned_judge = football_analysis_judge.align(
    traces=valid_traces,
    optimizer=likert_optimizer,
)

# COMMAND ----------

print("Original instructions:\n", football_analysis_judge.instructions)
print("\nAligned instructions:\n", aligned_judge.instructions)

# COMMAND ----------

from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    ScorerSamplingConfig,
    get_scorer
)

mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

register_align_judge = make_judge(
    name=f"{ALIGNED_JUDGE_NAME}_likert",
    instructions=aligned_judge.instructions,
    feedback_value_type=float,
    # model=JUDGE_MODEL,  # Model used to evaluate (from config)
)

try:
    register_aligned_judge = register_align_judge.register(experiment_id=EXPERIMENT_ID)

except ValueError as e:
    msg = str(e)

    if "has already been registered" in msg:
        # Preferred path per the error message: update existing scorer
        register_aligned_judge = register_align_judge.update(
            experiment_id=EXPERIMENT_ID,
            sampling_config=ScorerSamplingConfig(sample_rate=1)
        )
    else:
        raise

print("Registered aligned judge", register_align_judge.name)

# COMMAND ----------

print(register_aligned_judge.instructions)

# COMMAND ----------

# MAGIC %md
# MAGIC ###Rerun with Likert SIMBA Optimizer

# COMMAND ----------

from agent import AGENT
from mlflow.genai import evaluate
from mlflow.genai.datasets import create_dataset, get_dataset
from mlflow.genai.scorers import (
    Guidelines,
    RelevanceToQuery,
    get_scorer,
)

# Compile the judges and rerun the evaluation job

football_language = "The response must use language that is appropriate for professional football players and coaches"
football_language_judge = Guidelines(name="football_language", guidelines=football_language)

scorers = [RelevanceToQuery(), football_language_judge, register_aligned_judge]
# Rerun the evaluation after recreating the judge to better calibrate the agent quality

mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

# Grab all traces from the original eval dataset
eval_dataset = get_dataset(name=DATASET_NAME)

def extract_question(row_input):
    try:
      messages = row_input['request']['input']
      last_message = messages[-1]
      return last_message['content']
    except Exception as e:
      print(e)

df = eval_dataset.to_df()
eval_dataset_records = [
    {
        "inputs": {
            "input": [
                # Pass the EXTRACTED string, not the whole dictionary object
                {"role": "user", "content": extract_question(row)}
            ]
        }
        # Note: "expected" field is optional
    }
    for row in df['inputs'] 
]

print("Executing Evaluation Job")
results = evaluate(
    data=eval_dataset_records,
    predict_fn=lambda input: AGENT.predict({"input": input}),
    scorers=scorers
)

# COMMAND ----------

