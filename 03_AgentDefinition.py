# Databricks notebook source
# MAGIC %md
# MAGIC #Tool-calling Agent
# MAGIC
# MAGIC This is an auto-generated notebook created by an AI playground export. In this notebook, you will:
# MAGIC - Author a tool-calling [MLflow's `ResponsesAgent`](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html#mlflow.pyfunc.ResponsesAgent) that uses the OpenAI client
# MAGIC - Manually test the agent's output
# MAGIC - Evaluate the agent with Mosaic AI Agent Evaluation
# MAGIC - Log and deploy the agent
# MAGIC
# MAGIC This notebook should be run on serverless or a cluster with DBR<17.
# MAGIC
# MAGIC  **_NOTE:_**  This notebook uses the OpenAI SDK, but AI Agent Framework is compatible with any agent authoring framework, including LlamaIndex or LangGraph. To learn more, see the [Authoring Agents](https://docs.databricks.com/generative-ai/agent-framework/author-agent) Databricks documentation.
# MAGIC
# MAGIC ## Prerequisites
# MAGIC
# MAGIC - Address all `TODO`s in this notebook.

# COMMAND ----------

# MAGIC %pip install -U -qqqq backoff databricks-openai uv databricks-agents mlflow==3.9.0rc0
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# Load configuration from setup notebook
import json
from pathlib import Path
import mlflow
CONFIG = json.loads(Path("config/dc_assistant.json").read_text())

# Extract configuration variables
PROMPT_NAME = CONFIG["prompt_registry"]["prompt_name"]
LLM_ENDPOINT_NAME = CONFIG["llm"]["endpoint_name"]
UC_MODEL_NAME = CONFIG["model"]["uc_model_name"]
MODEL_NAME = CONFIG["model"]["model_name"]
UC_TOOL_NAMES = CONFIG["tools"]["uc_tool_names"]
CATALOG = CONFIG["workspace"]["catalog"]
SCHEMA = CONFIG["workspace"]["schema"]



# COMMAND ----------

EXPERIMENT_ID = CONFIG["mlflow"]["experiment_id"]
mlflow.set_experiment(experiment_id=EXPERIMENT_ID)
system_prompt = mlflow.genai.register_prompt(
    name=PROMPT_NAME,
    template="You are an assistant that helps Defensive NFL coaches prepare for facing a specific offense. Your role is to interpret user input, and leverage your available tools to better understand how offenses will approach certain situations. Answer users questions, and use your tools to extrapolate and provide additional relevant information as well. If no season is provided, assume 2024. For queries with a redzone parameter, ALWAYS pass FALSE for the redzone parameter unless the user explicitly asks about the redzone. Always answer the question, then ask any follow ups",
    )

mlflow.genai.set_prompt_alias(
    name=f"{PROMPT_NAME}",
    alias="production",
    version=1 # Update version accordingly
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define the agent in code
# MAGIC Below we define our agent code in a single cell, enabling us to easily write it to a local Python file for subsequent logging and deployment using the `%%writefile` magic command.
# MAGIC
# MAGIC For more examples of tools to add to your agent, see [docs](https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html).

# COMMAND ----------

import os
# Test authentication by making a simple API call
try:
    # Verify the service principal exists and credentials work
    from databricks.sdk import WorkspaceClient
    test_client = WorkspaceClient(
        host=os.environ.get("DATABRICKS_HOST"),
        client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
        client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
    )
    # Try to get current user info to verify auth works
    current_user = test_client.current_user.me()
    print(f"✅ Authentication successful! Authenticated as: {current_user.user_name if hasattr(current_user, 'user_name') else 'service principal'}")
except Exception as e:
    print(f"❌ Authentication test failed: {e}")
    print("   Please verify:")
    print("   1. The oauth-client-id secret contains the APPLICATION ID (UUID), not the display name")
    print("   2. The oauth-client-secret secret contains a valid, current secret value")
    print("   3. The service principal has the required permissions")
    raise

# COMMAND ----------

# MAGIC %%writefile agent.py
# MAGIC import json
# MAGIC import os
# MAGIC from pathlib import Path
# MAGIC from typing import Any, Callable, Generator, Optional
# MAGIC from uuid import uuid4
# MAGIC import warnings
# MAGIC
# MAGIC import backoff
# MAGIC import mlflow
# MAGIC import openai
# MAGIC from databricks.sdk import WorkspaceClient
# MAGIC from databricks_openai import UCFunctionToolkit, VectorSearchRetrieverTool
# MAGIC from mlflow.entities import SpanType
# MAGIC from mlflow.pyfunc import ResponsesAgent
# MAGIC from mlflow.types.responses import (
# MAGIC     ResponsesAgentRequest,
# MAGIC     ResponsesAgentResponse,
# MAGIC     ResponsesAgentStreamEvent,
# MAGIC     output_to_responses_items_stream,
# MAGIC     to_chat_completions_input,
# MAGIC )
# MAGIC from openai import OpenAI
# MAGIC from pydantic import BaseModel
# MAGIC from unitycatalog.ai.core.base import get_uc_function_client
# MAGIC
# MAGIC def get_dbutils():
# MAGIC     try:
# MAGIC         from pyspark.dbutils import DBUtils
# MAGIC         from pyspark.sql import SparkSession
# MAGIC         spark = SparkSession.builder.getOrCreate()
# MAGIC         dbutils = DBUtils(spark)
# MAGIC         return dbutils
# MAGIC     except (ImportError, Exception):
# MAGIC         # Spark not available (e.g., MLflow validation environment)
# MAGIC         try:
# MAGIC             import IPython
# MAGIC             ipython = IPython.get_ipython()
# MAGIC             if ipython and "dbutils" in ipython.user_ns:
# MAGIC                 return ipython.user_ns["dbutils"]
# MAGIC         except (ImportError, AttributeError, RuntimeError):
# MAGIC             pass
# MAGIC     return None  # dbutils not available
# MAGIC     
# MAGIC dbutils = get_dbutils()
# MAGIC
# MAGIC # ============================================================================
# MAGIC # Load shared configuration generated by 00_setup.ipynb
# MAGIC # ============================================================================
# MAGIC _CONFIG_PATH = Path("config/dc_assistant.json")
# MAGIC if _CONFIG_PATH.exists():
# MAGIC     CONFIG = json.loads(_CONFIG_PATH.read_text())
# MAGIC else:
# MAGIC     config_env = os.getenv("DC_ASSISTANT_CONFIG_JSON")
# MAGIC     if not config_env:
# MAGIC         raise FileNotFoundError(
# MAGIC             "config/dc_assistant.json not found and DC_ASSISTANT_CONFIG_JSON env var is not set"
# MAGIC         )
# MAGIC     CONFIG = json.loads(config_env)
# MAGIC
# MAGIC PROMPT_NAME = CONFIG["prompt_registry"]["prompt_name"]
# MAGIC LLM_ENDPOINT_NAME = CONFIG["llm"]["endpoint_name"]
# MAGIC UC_TOOL_NAMES = CONFIG["tools"]["uc_tool_names"]
# MAGIC SECRET_SCOPE_NAME = CONFIG["prompt_registry_auth"]["secret_scope_name"]
# MAGIC CLIENT_ID_KEY = CONFIG["prompt_registry_auth"]["oauth_client_id_key"]
# MAGIC CLIENT_SECRET_KEY = CONFIG["prompt_registry_auth"]["oauth_client_secret_key"]
# MAGIC SECRET_SCOPE_NAME = CONFIG["prompt_registry_auth"]["secret_scope_name"]
# MAGIC DATABRICKS_HOST = CONFIG["prompt_registry_auth"]["databricks_host"]
# MAGIC
# MAGIC ############################################
# MAGIC # Configure manual authentication for Prompt Registry access
# MAGIC # Prompt Registry requires manual authentication when used with deployed agents
# MAGIC # See: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#manual-authentication
# MAGIC ############################################
# MAGIC # Configure authentication for Prompt Registry access
# MAGIC # These environment variables can be injected at deployment time. When they are
# MAGIC # missing (e.g., local notebook runs), fall back to the workspace secrets.
# MAGIC if DATABRICKS_HOST and not os.getenv("DATABRICKS_HOST"):
# MAGIC     # Remove trailing slash if present (can cause auth issues)
# MAGIC     host = DATABRICKS_HOST.rstrip("/")
# MAGIC     os.environ["DATABRICKS_HOST"] = host
# MAGIC
# MAGIC if "DATABRICKS_CLIENT_ID" not in os.environ:
# MAGIC     client_id = dbutils.secrets.get(scope=SECRET_SCOPE_NAME, key=CLIENT_ID_KEY)
# MAGIC     os.environ["DATABRICKS_CLIENT_ID"] = client_id.strip()
# MAGIC
# MAGIC if "DATABRICKS_CLIENT_SECRET" not in os.environ:
# MAGIC     client_secret = dbutils.secrets.get(scope=SECRET_SCOPE_NAME, key=CLIENT_SECRET_KEY)
# MAGIC     os.environ["DATABRICKS_CLIENT_SECRET"] = client_secret.strip()
# MAGIC
# MAGIC WORKSPACE_CLIENT = WorkspaceClient(
# MAGIC     host=os.environ.get("DATABRICKS_HOST"),
# MAGIC     client_id=os.environ.get("DATABRICKS_CLIENT_ID"),
# MAGIC     client_secret=os.environ.get("DATABRICKS_CLIENT_SECRET"),
# MAGIC     token=os.environ.get("DATABRICKS_TOKEN"),
# MAGIC )
# MAGIC
# MAGIC # Configure MLflow to use Unity Catalog registry
# MAGIC # This ensures MLflow's internal client uses the correct registry and authentication
# MAGIC mlflow.set_registry_uri("databricks-uc")
# MAGIC
# MAGIC ############################################
# MAGIC # Define your LLM endpoint and system prompt
# MAGIC ############################################
# MAGIC PROMPT_URI_AGENT = f"prompts:/{PROMPT_NAME}@production"
# MAGIC SYSTEM_PROMPT = mlflow.genai.load_prompt(PROMPT_URI_AGENT)
# MAGIC
# MAGIC ###############################################################################
# MAGIC ## Define tools for your agent, enabling it to retrieve data or take actions
# MAGIC ## beyond text generation
# MAGIC ## To create and see usage examples of more tools, see
# MAGIC ## https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html
# MAGIC ###############################################################################
# MAGIC class ToolInfo(BaseModel):
# MAGIC     """
# MAGIC     Class representing a tool for the agent.
# MAGIC     - "name" (str): The name of the tool.
# MAGIC     - "spec" (dict): JSON description of the tool (matches OpenAI Responses format)
# MAGIC     - "exec_fn" (Callable): Function that implements the tool logic
# MAGIC     """
# MAGIC
# MAGIC     name: str
# MAGIC     spec: dict
# MAGIC     exec_fn: Callable
# MAGIC
# MAGIC
# MAGIC def create_tool_info(tool_spec, exec_fn_param: Optional[Callable] = None):
# MAGIC     tool_spec["function"].pop("strict", None)
# MAGIC     tool_name = tool_spec["function"]["name"]
# MAGIC     udf_name = tool_name.replace("__", ".")
# MAGIC
# MAGIC     # Define a wrapper that accepts kwargs for the UC tool call,
# MAGIC     # then passes them to the UC tool execution client
# MAGIC     def exec_fn(**kwargs):
# MAGIC         function_result = uc_function_client.execute_function(udf_name, kwargs)
# MAGIC         if function_result.error is not None:
# MAGIC             return function_result.error
# MAGIC         else:
# MAGIC             return function_result.value
# MAGIC     return ToolInfo(name=tool_name, spec=tool_spec, exec_fn=exec_fn_param or exec_fn)
# MAGIC
# MAGIC
# MAGIC TOOL_INFOS = []
# MAGIC
# MAGIC uc_toolkit = UCFunctionToolkit(function_names=UC_TOOL_NAMES)
# MAGIC uc_function_client = get_uc_function_client()
# MAGIC for tool_spec in uc_toolkit.tools:
# MAGIC     TOOL_INFOS.append(create_tool_info(tool_spec))
# MAGIC
# MAGIC
# MAGIC # Use Databricks vector search indexes as tools
# MAGIC # See [docs](https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html) for details
# MAGIC
# MAGIC # # (Optional) Use Databricks vector search indexes as tools
# MAGIC # # See https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html
# MAGIC
# MAGIC
# MAGIC def _safe_parse_tool_arguments(raw_args: Any) -> dict:
# MAGIC     """Parse tool call arguments robustly.
# MAGIC     - Accepts dict (returns as-is) or JSON string.
# MAGIC     - Tolerates concatenated JSON objects (e.g., '}{') by selecting the last object.
# MAGIC     """
# MAGIC     if isinstance(raw_args, dict):
# MAGIC         return raw_args
# MAGIC     if not isinstance(raw_args, str):
# MAGIC         return {}
# MAGIC     s = raw_args.strip()
# MAGIC     try:
# MAGIC         return json.loads(s)
# MAGIC     except json.JSONDecodeError:
# MAGIC         # Try to handle concatenated JSON objects like: '{...}{...}'
# MAGIC         if "}{" in s:
# MAGIC             # Try last object first
# MAGIC             try:
# MAGIC                 return json.loads("{" + s.split("}{")[-1])
# MAGIC             except Exception:
# MAGIC                 pass
# MAGIC             # Try as a list of objects and take the last one
# MAGIC             try:
# MAGIC                 arr = json.loads("[" + s.replace("}{", "},{") + "]")
# MAGIC                 if isinstance(arr, list) and arr:
# MAGIC                     return arr[-1]
# MAGIC             except Exception:
# MAGIC                 pass
# MAGIC         # As a fallback, attempt to extract the first balanced JSON object
# MAGIC         depth = 0
# MAGIC         end = -1
# MAGIC         for i, ch in enumerate(s):
# MAGIC             if ch == '{':
# MAGIC                 depth += 1
# MAGIC             elif ch == '}':
# MAGIC                 depth -= 1
# MAGIC                 if depth == 0:
# MAGIC                     end = i + 1
# MAGIC                     break
# MAGIC         if end > 0:
# MAGIC             try:
# MAGIC                 return json.loads(s[:end])
# MAGIC             except Exception:
# MAGIC                 pass
# MAGIC         # Give up and raise a clean error message
# MAGIC         raise json.JSONDecodeError("Unable to parse tool arguments", s, 0)
# MAGIC
# MAGIC
# MAGIC class ToolCallingAgent(ResponsesAgent):
# MAGIC     """
# MAGIC     Class representing a tool-calling Agent
# MAGIC     """
# MAGIC
# MAGIC     def __init__(
# MAGIC         self,
# MAGIC         llm_endpoint: str,
# MAGIC         tools: list[ToolInfo],
# MAGIC         workspace_client: Optional[WorkspaceClient] = None,
# MAGIC     ):
# MAGIC         """Initializes the ToolCallingAgent with tools."""
# MAGIC         self.llm_endpoint = llm_endpoint
# MAGIC         self.workspace_client = workspace_client or WorkspaceClient()
# MAGIC         self.model_serving_client: OpenAI = (
# MAGIC             self.workspace_client.serving_endpoints.get_open_ai_client()
# MAGIC         )
# MAGIC         self._tools_dict = {tool.name: tool for tool in tools}
# MAGIC
# MAGIC     def get_tool_specs(self) -> list[dict]:
# MAGIC         """Returns tool specifications in the format OpenAI expects."""
# MAGIC         return [tool_info.spec for tool_info in self._tools_dict.values()]
# MAGIC
# MAGIC     @mlflow.trace(span_type=SpanType.TOOL)
# MAGIC     def execute_tool(self, tool_name: str, args: dict) -> Any:
# MAGIC         """Executes the specified tool with the given arguments."""
# MAGIC         return self._tools_dict[tool_name].exec_fn(**args)
# MAGIC
# MAGIC     def call_llm(self, messages: list[dict[str, Any]]) -> Generator[dict[str, Any], None, None]:
# MAGIC         with warnings.catch_warnings():
# MAGIC             warnings.filterwarnings("ignore", message="PydanticSerializationUnexpectedValue")
# MAGIC             for chunk in self.model_serving_client.chat.completions.create(
# MAGIC                 model=self.llm_endpoint,
# MAGIC                 messages=to_chat_completions_input(messages),
# MAGIC                 tools=self.get_tool_specs(),
# MAGIC                 stream=True,
# MAGIC             ):
# MAGIC                 chunk_dict = chunk.to_dict()
# MAGIC                 if len(chunk_dict.get("choices", [])) > 0:
# MAGIC                     yield chunk_dict
# MAGIC
# MAGIC     def handle_tool_call(
# MAGIC         self,
# MAGIC         tool_call: dict[str, Any],
# MAGIC         messages: list[dict[str, Any]],
# MAGIC     ) -> ResponsesAgentStreamEvent:
# MAGIC         """
# MAGIC         Execute tool calls, add them to the running message history, and return a ResponsesStreamEvent w/ tool output
# MAGIC         """
# MAGIC         raw_args = tool_call.get("arguments", {})
# MAGIC         args = _safe_parse_tool_arguments(raw_args)
# MAGIC         result = str(self.execute_tool(tool_name=tool_call["name"], args=args))
# MAGIC
# MAGIC         tool_call_output = self.create_function_call_output_item(tool_call["call_id"], result)
# MAGIC         messages.append(tool_call_output)
# MAGIC         return ResponsesAgentStreamEvent(type="response.output_item.done", item=tool_call_output)
# MAGIC
# MAGIC     def call_and_run_tools(
# MAGIC         self,
# MAGIC         messages: list[dict[str, Any]],
# MAGIC         max_iter: int = 20,
# MAGIC     ) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         for _ in range(max_iter):
# MAGIC             last_msg = messages[-1]
# MAGIC             if last_msg.get("role", None) == "assistant":
# MAGIC                 return
# MAGIC             elif last_msg.get("type", None) == "function_call":
# MAGIC                 yield self.handle_tool_call(last_msg, messages)
# MAGIC             else:
# MAGIC                 yield from output_to_responses_items_stream(
# MAGIC                     chunks=self.call_llm(messages), aggregator=messages
# MAGIC                 )
# MAGIC
# MAGIC         yield ResponsesAgentStreamEvent(
# MAGIC             type="response.output_item.done",
# MAGIC             item=self.create_text_output_item("Max iterations reached. Stopping.", str(uuid4())),
# MAGIC         )
# MAGIC
# MAGIC     def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
# MAGIC         outputs = [
# MAGIC             event.item
# MAGIC             for event in self.predict_stream(request)
# MAGIC             if event.type == "response.output_item.done"
# MAGIC         ]
# MAGIC         return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)
# MAGIC
# MAGIC     def predict_stream(
# MAGIC         self, request: ResponsesAgentRequest
# MAGIC     ) -> Generator[ResponsesAgentStreamEvent, None, None]:
# MAGIC         messages = to_chat_completions_input([i.model_dump() for i in request.input])
# MAGIC         if SYSTEM_PROMPT:
# MAGIC             messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT.format()})
# MAGIC         yield from self.call_and_run_tools(messages=messages)
# MAGIC
# MAGIC
# MAGIC # Log the model using MLflow
# MAGIC mlflow.openai.autolog()
# MAGIC AGENT = ToolCallingAgent(
# MAGIC     llm_endpoint=LLM_ENDPOINT_NAME, tools=TOOL_INFOS, workspace_client=WORKSPACE_CLIENT
# MAGIC )
# MAGIC mlflow.models.set_model(AGENT)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test the agent
# MAGIC
# MAGIC Interact with the agent to test its output. Since we manually traced methods within `ResponsesAgent`, you can view the trace for each step the agent takes, with any LLM calls made via the OpenAI SDK automatically traced by autologging.
# MAGIC
# MAGIC Replace this placeholder input with an appropriate domain-specific example for your agent.

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC # Test the agent
# MAGIC - Reload some of the config features and experiment as well after restarting Python

# COMMAND ----------

from agent import AGENT
import mlflow
import json
from pathlib import Path

CONFIG = json.loads(Path("config/dc_assistant.json").read_text())
EXPERIMENT_ID = CONFIG["mlflow"]["experiment_id"]
mlflow.set_experiment(experiment_id=EXPERIMENT_ID)

AGENT.predict({"input": [{"role": "user", "content": "What do the raiders do after turnovers?"}]})

# COMMAND ----------

for chunk in AGENT.predict_stream(
    {"input": [{"role": "user", "content": "What do the 2024 Titans like to do in the red zone?"}]}
):
    print(chunk.model_dump(exclude_none=True))

# COMMAND ----------

# MAGIC %md
# MAGIC ### Log the `agent` as an MLflow model
# MAGIC Determine Databricks resources to specify for automatic auth passthrough at deployment time
# MAGIC - **TODO**: If your Unity Catalog Function queries a [vector search index](https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html) or leverages [external functions](https://docs.databricks.com/generative-ai/agent-framework/external-connection-tools.html), you need to include the dependent vector search index and UC connection objects, respectively, as resources. See [docs](https://docs.databricks.com/generative-ai/agent-framework/log-agent.html#specify-resources-for-automatic-authentication-passthrough) for more details.
# MAGIC
# MAGIC Log the agent as code from the `agent.py` file. See [MLflow - Models from Code](https://mlflow.org/docs/latest/models.html#models-from-code).

# COMMAND ----------

# Determine Databricks resources to specify for automatic auth passthrough at deployment time
import mlflow
import os
from agent import UC_TOOL_NAMES, LLM_ENDPOINT_NAME
from mlflow.models.resources import DatabricksFunction, DatabricksServingEndpoint
from pkg_resources import get_distribution

# PROMPT_NAME loaded from config above
# Note: Prompt Registry requires manual authentication (see agent.py and deployment cell)

resources = [DatabricksServingEndpoint(endpoint_name=LLM_ENDPOINT_NAME)]
for tool_name in UC_TOOL_NAMES:
    # TODO: If the UC function includes dependencies like external connection or vector search, please include them manually.
    # See the TODO in the markdown above for more information.    
    resources.append(DatabricksFunction(function_name=tool_name))

input_example = {
    "input": [
        {
            "role": "user",
            "content": "We are playing the 2024 Green Bay Packers - When do they run screens?"
        }
    ]
}

os.environ["UV_PRERELEASE"] = "allow"

with mlflow.start_run():
    logged_agent_info = mlflow.pyfunc.log_model(
        name="agent",
        python_model="agent.py",
        input_example=input_example,
        pip_requirements=[
            "databricks-openai",
            "backoff",
            f"databricks-connect=={get_distribution('databricks-connect').version}",
            "mlflow==3.9.0rc0",
        ],
        resources=resources,
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Perform pre-deployment validation of the agent
# MAGIC Before registering and deploying the agent, we perform pre-deployment checks via the [mlflow.models.predict()](https://mlflow.org/docs/latest/python_api/mlflow.models.html#mlflow.models.predict) API. See [documentation](https://docs.databricks.com/machine-learning/model-serving/model-serving-debug.html#validate-inputs) for details

# COMMAND ----------

mlflow.models.predict(
    model_uri=f"runs:/{logged_agent_info.run_id}/agent",
    input_data={"input": [{"role": "user", "content": "How do the 2024 Chiefs handle the last two minutes of the half"}]},
    env_manager="uv",
    extra_envs={"UV_PRERELEASE": "allow"},
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Register the model to Unity Catalog
# MAGIC
# MAGIC Update the `catalog`, `schema`, and `model_name` below to register the MLflow model to Unity Catalog.

# COMMAND ----------

import os 
mlflow.set_registry_uri("databricks-uc")

UC_MODEL_NAME = CONFIG["model"]["uc_model_name"]

# Temporarily clear OAuth credentials so MLflow uses user authentication for model registration
# The service principal doesn't need CREATE MODEL VERSION permissions - model registration
# happens in notebooks using user credentials, not in deployed agents
original_client_id = os.environ.pop("DATABRICKS_CLIENT_ID", None)
original_client_secret = os.environ.pop("DATABRICKS_CLIENT_SECRET", None)

try:
    # register the model to UC (will use user's default authentication)
    uc_registered_model_info = mlflow.register_model(
        model_uri=logged_agent_info.model_uri, name=UC_MODEL_NAME
    )
finally:
    # Restore OAuth credentials for agent use
    if original_client_id:
        os.environ["DATABRICKS_CLIENT_ID"] = original_client_id
    if original_client_secret:
        os.environ["DATABRICKS_CLIENT_SECRET"] = original_client_secret

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deploy the agent

# COMMAND ----------

from databricks import agents
import json
import os
from pathlib import Path

# Load configuration from 00_setup.ipynb
CONFIG = json.loads(Path("config/dc_assistant.json").read_text())
UC_MODEL_NAME = CONFIG["model"]["uc_model_name"]

# Configure manual authentication for Prompt Registry access
# Prompt Registry requires manual authentication when used with deployed agents
# See: https://docs.databricks.com/aws/en/generative-ai/agent-framework/agent-authentication#manual-authentication
auth_config = CONFIG["prompt_registry_auth"]
DATABRICKS_HOST = auth_config["databricks_host"]
SECRET_SCOPE_NAME = auth_config["secret_scope_name"]
USE_OAUTH = auth_config["use_oauth"]

# Always package the generated config so the deployed agent can load it
config_payload = Path("config/dc_assistant.json").read_text()
environment_vars = {"DC_ASSISTANT_CONFIG_JSON": config_payload}

# Build authentication environment variables if DATABRICKS_HOST is configured
if DATABRICKS_HOST:
    if USE_OAUTH:
        # OAuth authentication
        OAUTH_CLIENT_ID_KEY = auth_config["oauth_client_id_key"]
        OAUTH_CLIENT_SECRET_KEY = auth_config["oauth_client_secret_key"]
        environment_vars.update(
            {
                "DATABRICKS_HOST": DATABRICKS_HOST,
                "DATABRICKS_CLIENT_ID": f"{{{{secrets/{SECRET_SCOPE_NAME}/{OAUTH_CLIENT_ID_KEY}}}}}",
                "DATABRICKS_CLIENT_SECRET": f"{{{{secrets/{SECRET_SCOPE_NAME}/{OAUTH_CLIENT_SECRET_KEY}}}}}",
            }
        )
        print(f" Using OAuth authentication (scope: {SECRET_SCOPE_NAME})")
    else:
        # PAT authentication
        PAT_KEY = auth_config["pat_key"]
        environment_vars.update(
            {
                "DATABRICKS_HOST": DATABRICKS_HOST,
                "DATABRICKS_TOKEN": f"{{{{secrets/{SECRET_SCOPE_NAME}/{PAT_KEY}}}}}",
            }
        )
        print(f" Using PAT authentication (scope: {SECRET_SCOPE_NAME})")
else:
    print("   WARNING: DATABRICKS_HOST not configured in 00_setup.ipynb")
    print("   Prompt Registry will not be accessible in deployed agent")
    print("   Update DATABRICKS_HOST in 00_setup.ipynb and ensure secrets are configured")

# Deploy the agent
agents.deploy(
    UC_MODEL_NAME,
    uc_registered_model_info.version,
    environment_vars=environment_vars,
    tags={"endpointSource": "playground", "RemoveAfter": "2026-12-30"},
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next steps - Evaluation!
# MAGIC
# MAGIC We'll execute both an automated evaluation with an LLM as a judge, as well as create a labeling session for SMEs to review traces manually. We'll use both outputs to further calibrate a custom LLM judge for this specific use case