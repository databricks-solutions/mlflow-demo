"""Email generation using Databricks Model Serving and MLflow prompt registry.

This module implements a streaming-first architecture for email generation that integrates
with Databricks Model Serving endpoints and MLflow's prompt registry and tracing capabilities.

Architecture Overview:
    - Single source of truth: All email generation logic is implemented in the streaming version
    - Non-streaming API: Internally calls streaming version and collects chunks for
      complete response
    - MLflow Integration: Full tracing support with RETRIEVER, PARSER, and LLM spans
    - Customer Data: Retrieved from JSONL files and converted to MLflow Documents for proper tracing
    - Prompt Management: Uses MLflow prompt registry with versioning and aliasing

Key Components:
    - EmailGenerator: Main class handling both streaming and non-streaming email generation
    - Streaming API: Real-time token-by-token email generation with MLflow tracing
    - Non-streaming API: Synchronous interface that collects streaming results
    - Customer Retrieval: JSONL-based customer data with MLflow Document format
    - Feedback System: MLflow 3.0 feedback API integration for human evaluation

Dependencies:
    - mlflow: For prompt registry, tracing, and feedback collection
    - databricks-sdk: For Model Serving endpoint access via OpenAI-compatible client
    - asyncio: For streaming token generation and event loop management

Example Usage:
    >>> generator = EmailGenerator()
    >>> # Streaming generation
    >>> async for chunk in generator.stream_generate_email_with_retrieval(
    ...     customer_name="EcomSolutions LLC",
    ...     user_input="Keep it brief"
    ... ):
    ...     print(chunk)
    >>>
    >>> # Non-streaming generation
    >>> result = generator.generate_email_with_retrieval(
    ...     customer_name="EcomSolutions LLC",
    ...     user_input="Keep it brief"
    ... )
    >>> print(result['subject_line'], result['body'])
"""

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import mlflow
from databricks.sdk import WorkspaceClient
from mlflow.entities import Document


class EmailGenerator:
  r"""Email generator using Databricks Model Serving and MLflow prompt registry.

  This class implements a streaming-first architecture where all email generation logic
  is centralized in the streaming implementation. The non-streaming API internally calls
  the streaming version and aggregates results for a complete response.

  The class integrates deeply with MLflow for:
  - Prompt registry management with versioning
  - Comprehensive tracing with proper span types (RETRIEVER, PARSER, LLM)
  - User feedback collection using MLflow 3.0 API
  - Automatic model version tracking

  Configuration:
      All configuration can be provided via constructor parameters or environment variables:
      - LLM_MODEL: Databricks Model Serving endpoint name
      - PROMPT_NAME: Name of prompt in MLflow prompt registry
      - PROMPT_ALIAS: Alias/version of prompt to use (e.g., 'production', 'staging')
      - UC_CATALOG: Unity Catalog name where prompts are stored
      - UC_SCHEMA: Schema within the catalog where prompts are stored

  Architecture Benefits:
      - Single maintenance point: All generation logic in streaming implementation
      - Consistent tracing: Same MLflow spans for both streaming and non-streaming
      - Real-time capabilities: Token-by-token streaming for responsive UX
      - Backwards compatibility: Non-streaming API maintains existing interfaces

  Example:
      >>> # Basic setup with environment variables
      >>> generator = EmailGenerator()
      >>>
      >>> # Custom configuration
      >>> generator = EmailGenerator(
      ...     model="my-llm-endpoint",
      ...     prompt_name="email_prompt",
      ...     prompt_alias="production",
      ...     uc_catalog="my_catalog",
      ...     uc_schema="prompts"
      ... )
      >>>
      >>> # Generate email (non-streaming)
      >>> result = generator.generate_email_with_retrieval(
      ...     customer_name="Acme Corp",
      ...     user_input="Focus on ROI metrics"
      ... )
      >>> print(f"Subject: {result['subject_line']}")
      >>> print(f"Trace ID: {result['trace_id']}")
      >>>
      >>> # Stream email generation
      >>> async for chunk in generator.stream_generate_email_with_retrieval(
      ...     customer_name="Acme Corp",
      ...     user_input="Focus on ROI metrics"
      ... ):
      ...     if chunk['type'] == 'token':
      ...         print(chunk['content'], end='')
      ...     elif chunk['type'] == 'done':
      ...         print(f"\nTrace ID: {chunk['trace_id']}")
  """

  def __init__(
    self,
    prompt_alias: Optional[str] = None,
    model: Optional[str] = None,
    uc_catalog: Optional[str] = None,
    uc_schema: Optional[str] = None,
    prompt_name: Optional[str] = None,
  ):
    """Initialize EmailGenerator with configuration.

    Sets up the email generator with Databricks Model Serving and MLflow integration.
    Configuration can be provided via parameters or environment variables. The generator
    will validate all required settings and establish connections to necessary services.

    Args:
        prompt_alias: Prompt alias/version to use (e.g., 'production', 'staging').
                     Defaults to PROMPT_ALIAS environment variable.
        model: Databricks Model Serving endpoint name for LLM inference.
               Defaults to LLM_MODEL environment variable.
        uc_catalog: Unity Catalog name where prompts are stored.
                   Defaults to UC_CATALOG environment variable.
        uc_schema: Unity Catalog schema containing the prompts.
                  Defaults to UC_SCHEMA environment variable.
        prompt_name: Name of the prompt template in MLflow prompt registry.
                    Defaults to PROMPT_NAME environment variable.

    Raises:
        ValueError: If LLM_MODEL is not provided via parameter or environment variable.
        Exception: If any of the required prompt registry parameters are missing.

    Example:
        >>> # Using environment variables (recommended for production)
        >>> generator = EmailGenerator()
        >>>
        >>> # Custom configuration
        >>> generator = EmailGenerator(
        ...     model="llm-endpoint-prod",
        ...     prompt_name="sales_email_v2",
        ...     prompt_alias="production",
        ...     uc_catalog="ml_catalog",
        ...     uc_schema="prompts"
        ... )
    """
    # Load configuration from environment variables with overrides
    self.prompt_alias = prompt_alias or os.getenv('PROMPT_ALIAS')
    self.model = model or os.getenv('LLM_MODEL')
    self.uc_catalog = uc_catalog or os.environ.get('UC_CATALOG')
    self.uc_schema = uc_schema or os.environ.get('UC_SCHEMA')
    self.prompt_name = prompt_name or os.getenv('PROMPT_NAME')
    self.prompt = None

    # Validate required configuration
    if not self.model:
      raise ValueError('LLM_MODEL environment variable is not set and no model provided')
    if not self.prompt_name or not self.prompt_alias or not self.uc_catalog or not self.uc_schema:
      raise Exception(
        'PROMPT_NAME, PROMPT_ALIAS, UC_CATALOG, and UC_SCHEMA environment variables',
        ' must be set or provided',
      )

    # Enable automatic tracing for OpenAI LLM calls
    mlflow.openai.autolog()

    # Initialize OpenAI client
    w = WorkspaceClient()  # Auto-configures from environment or ~/.databrickscfg
    self.openai_client = w.serving_endpoints.get_open_ai_client()

    # Load prompt
    self._load_prompt()

  def _load_prompt(self):
    """Load prompt from MLflow prompt registry and set the active model version.

    Retrieves the prompt template from MLflow's prompt registry using the configured
    catalog, schema, prompt name, and alias. Also sets the active MLflow model to
    track the specific prompt version being used for tracing purposes.

    The prompt URI format follows MLflow conventions:
    prompts:/{catalog}.{schema}.{prompt_name}@{alias}

    Side Effects:
        - Sets self.prompt to the loaded MLflow prompt object
        - Calls mlflow.set_active_model() to establish model version for tracing

    Raises:
        MLflowException: If prompt cannot be found or loaded from registry
    """
    # Load prompt from registry using the prompts:// URI format
    # Format: prompts:/{catalog}.{schema}.{prompt_name}@{alias}
    prompt_uri = (
      f'prompts:/{self.uc_catalog}.{self.uc_schema}.{self.prompt_name}@{self.prompt_alias}'
    )
    self.prompt = mlflow.genai.load_prompt(prompt_uri)

    # Set the active MLflow model to track the specific prompt version in traces
    # This enables tracking which prompt version was used for each generation
    mlflow.set_active_model(name=f'{self.prompt_name}@{self.prompt_alias}@v{self.prompt.version}')

  @mlflow.trace(span_type='PARSER')
  def _create_messages(self, customer_documents: List[Document], user_input: Optional[str] = None):
    """Create the messages array for the OpenAI API call.

    Formats customer data and user instructions into the message structure expected
    by the OpenAI chat completions API. The system message contains the prompt template
    while the user message contains formatted customer data and optional instructions.

    Args:
        customer_documents: List of MLflow Documents containing customer information,
                          each with page_content (markdown) and metadata (type, customer_name).
        user_input: Optional user instructions to append to the customer information.
                   If None or empty, no additional instructions are added.

    Returns:
        List[Dict[str, str]]: OpenAI messages format with 'role' and 'content' keys.
                             Contains system message (prompt) and user message
                             (data + instructions).

    Note:
        This method is traced as a PARSER span in MLflow, allowing evaluation of
        how customer data is formatted and presented to the LLM.
    """
    # Convert MLflow Documents to formatted string for LLM consumption
    # Each document section gets a clear heading and markdown content
    customer_info = '\n\n'.join(
      [
        f'{doc.metadata["type"].replace("_", " ").title()}:\n{doc.page_content}'
        for doc in customer_documents
      ]
    )

    # Append user instructions if provided for email customization
    if user_input:
      customer_info += f'\n\nUser Instructions:\n{user_input}'

    # Return OpenAI chat format: system message (prompt) + user message (data)
    return [
      {'role': 'system', 'content': self.prompt.template if self.prompt else ''},
      {'role': 'user', 'content': customer_info},
    ]

  @mlflow.trace(span_type='RETRIEVER')
  def _retrieve_customer_data(self, customer_name: str) -> List[Document]:
    """Retrieve customer data from JSONL file with MLflow tracing.

    Loads customer data from the JSONL file and converts it to MLflow Document format
    for proper tracing and evaluation. Each top-level section of customer data becomes
    a separate document with markdown formatting, enabling MLflow's built-in retrieval
    evaluation metrics to work correctly.

    Args:
        customer_name: Name of the customer/company to retrieve data for.
                      Must match the 'account.name' field in the JSONL data.

    Returns:
        List[Document]: MLflow Documents containing customer information.
                       Each document represents one section (account, support_tickets, etc.)
                       with markdown-formatted content and metadata.

    Raises:
        FileNotFoundError: If the customer data JSONL file cannot be found.
        ValueError: If the specified customer name is not found in the data.

    Note:
        - Traced as RETRIEVER span for MLflow evaluation compatibility
        - Data path: mlflow_demo/data/input_data.jsonl (relative to this file)
        - Each document gets unique ID: {customer_name}_{section_key}
        - Metadata includes 'type' (section name) and 'customer_name'
    """
    # Load customer data from JSONL file
    customers = []
    data_path = Path(__file__).parent.parent / 'data' / 'input_data.jsonl'

    try:
      with open(data_path, 'r') as f:
        for line in f:
          customers.append(json.loads(line))
    except FileNotFoundError:
      raise FileNotFoundError(f'Customer data file not found at {data_path}')

    # Search for the customer
    customer_data = None
    for customer in customers:
      if customer['account']['name'] == customer_name:
        customer_data = customer
        break

    if not customer_data:
      raise ValueError(f"Customer '{customer_name}' not found in data file")

    # Create MLflow Documents for proper retriever span output
    # Put each top-level key into a separate document with markdown formatting
    documents = []
    for key, value in customer_data.items():
      markdown_content = self._format_json_as_markdown(key, value)
      documents.append(
        Document(
          id=f'{customer_name}_{key}',
          page_content=markdown_content,
          metadata={'type': key, 'customer_name': customer_name},
        )
      )

    return documents

  def _format_json_as_markdown(self, section_name: str, data: dict) -> str:
    """Format JSON data as readable markdown.

    Converts nested JSON/dictionary data into well-formatted markdown with proper
    headings, bullet points, and indentation. This makes the customer data more
    readable for the LLM while preserving the hierarchical structure.

    Args:
        section_name: Name of the data section (e.g., 'account', 'support_tickets').
                     Will be converted to title case for the main heading.
        data: Dictionary containing the customer data to format.
              Supports nested dictionaries, lists, and primitive values.

    Returns:
        str: Markdown-formatted string with hierarchical structure.
             Includes main heading, subheadings, and properly indented content.

    Example:
        >>> data = {'account': {'name': 'Acme Corp', 'tier': 'Enterprise'}}
        >>> result = self._format_json_as_markdown('account', data)
        >>> print(result)
        # Account

        **Name:** Acme Corp

        **Tier:** Enterprise
    """
    # Convert section name to title case
    title = section_name.replace('_', ' ').title()
    markdown = f'# {title}\n\n'

    def format_value(value, indent_level=0):
      """Recursively format values with proper indentation.

      Handles different data types (dict, list, primitives) and applies appropriate
      markdown formatting with proper indentation levels for nested structures.

      Args:
          value: The value to format (can be dict, list, or primitive type).
          indent_level: Current indentation level (0-based, each level = 2 spaces).

      Returns:
          str: Formatted markdown string for the value.
      """
      indent = '  ' * indent_level

      if isinstance(value, dict):
        result = ''
        for k, v in value.items():
          key_name = k.replace('_', ' ').title()
          if isinstance(v, (dict, list)):
            result += f'{indent}**{key_name}:**\n'
            result += format_value(v, indent_level + 1)
            result += '\n'
          else:
            result += f'{indent}**{key_name}:** {v}\n\n'
        return result
      elif isinstance(value, list):
        result = ''
        for i, item in enumerate(value):
          if isinstance(item, dict):
            result += f'{indent}- Item {i + 1}:\n'
            result += format_value(item, indent_level + 1)
          else:
            result += f'{indent}- {item}\n'
        return result
      else:
        return f'{indent}{value}\n'

    markdown += format_value(data)
    return markdown.strip()

  @mlflow.trace(span_type='PARSER')
  def _clean_json_response(self, response_content: str) -> str:
    """Clean JSON response by removing markdown code block markers.

    Many LLMs wrap JSON responses in markdown code blocks (```json ... ```).
    This method strips those markers to get clean JSON for parsing.

    Args:
        response_content: Raw LLM response that may contain markdown formatting.

    Returns:
        str: Cleaned string with markdown code block markers removed.
             Whitespace is also stripped from the result.

    Note:
        Traced as PARSER span to monitor response cleaning in MLflow.
    """
    clean_string = response_content
    if response_content.startswith('```json\n') and response_content.endswith('\n```'):
      clean_string = response_content[len('```json\n') : -len('\n```')]
    elif response_content.startswith('```') and response_content.endswith('```'):
      clean_string = response_content[3:-3]

    return clean_string.strip()

  @staticmethod
  def _get_current_trace_id():
    """Get the current trace ID from MLflow.

    Retrieves the trace ID from the currently active MLflow span, which is used
    to link user feedback to specific email generation runs.

    Returns:
        str | None: The current trace ID if an active span exists, None otherwise.
    """
    active_span = mlflow.get_current_active_span()
    return active_span.trace_id if active_span else None

  def generate_email_with_retrieval(
    self, customer_name: str, user_input: Optional[str] = None
  ) -> Dict[str, Any]:
    """Generate email with customer data retrieval step by collecting streaming chunks.

    This is the non-streaming API that internally calls the streaming implementation
    and collects all chunks to return a complete email. This approach ensures there's
    only one source of generation logic while maintaining backwards compatibility.

    The method handles async/sync bridging by detecting if an event loop is already
    running (FastAPI context) and uses thread-based execution when necessary.

    Args:
        customer_name: Name of the customer to generate email for.
                      Must exist in the customer data JSONL file.
        user_input: Optional user instructions to customize the email generation.
                   If None or empty, uses default generation without specific instructions.

    Returns:
        Dict[str, Any]: Complete email with the following keys:
            - subject_line: Generated email subject
            - body: Full email body content
            - trace_id: MLflow trace ID for feedback linking

    Raises:
        ValueError: If customer name is not found in data.
        FileNotFoundError: If customer data file is missing.
        RuntimeError: If async execution fails.

    Note:
        - Uses streaming implementation internally for consistency
        - Handles event loop scenarios (FastAPI vs standalone execution)
        - Creates MLflow span with proper inputs/outputs for tracing
        - Thread-safe execution when called from async contexts
    """
    import asyncio

    # Collect all chunks from streaming version
    chunks = []

    async def collect_chunks():
      """Async helper to collect all streaming chunks into a list."""
      async for chunk in self.stream_generate_email_with_retrieval(customer_name, user_input):
        chunks.append(chunk)

    # Handle different event loop scenarios (FastAPI vs standalone execution)
    try:
      # Check if we're already in an event loop (e.g., FastAPI request context)
      asyncio.get_running_loop()
      # If we are, we need to run the async code in a separate thread with its own loop
      # This prevents "asyncio.run() cannot be called from a running event loop" errors
      import concurrent.futures

      def run_in_thread():
        """Execute the async collection in a new thread with its own event loop."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
          return new_loop.run_until_complete(collect_chunks())
        finally:
          new_loop.close()

      # Execute the async code in a thread pool to avoid event loop conflicts
      with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_thread)
        future.result()  # Wait for completion and propagate any exceptions

    except RuntimeError:
      # No event loop running (standalone execution), safe to use asyncio.run()
      asyncio.run(collect_chunks())

    # Use the existing static reducer to convert streaming chunks to final result
    # This ensures consistent processing logic between streaming and non-streaming APIs
    reduced_result = self._stream_email_reducer_static(chunks)

    # Convert reducer output to the format expected by the non-streaming API
    result = {
      'subject_line': reduced_result.get('email_subject', ''),
      'body': reduced_result.get('email_body', ''),
      'trace_id': reduced_result.get('trace_id'),
    }

    return result

  @staticmethod
  def _stream_email_reducer_static(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Reduce streaming email chunks into summary for MLflow trace output.

    This static method processes the list of chunks generated during streaming
    to create a summary compatible with MLflow tracing and the non-streaming API.
    It handles token aggregation, JSON parsing, and error recovery.

    Args:
        chunks: List of streaming chunks with the following structure:
               - {'type': 'token', 'content': str}: Individual tokens from LLM
               - {'type': 'done', 'trace_id': str}: Completion marker with trace ID
               - {'type': 'error', 'error': str}: Error information

    Returns:
        Dict[str, Any]: Processed result with keys:
            - email_subject: Extracted subject line from email JSON
            - email_body: Full email body content
            - trace_id: MLflow trace ID (if available)

    Note:
        - Aggregates all 'token' chunks into complete email content
        - Parses JSON and handles markdown code block cleaning
        - Gracefully handles parsing errors with fallback messages
        - Used by MLflow's output_reducer for streaming trace summaries
    """
    import json

    email_content = ''
    trace_id = None
    error_message = None

    # Collect all token content and trace info
    for chunk in chunks:
      chunk_type = chunk.get('type')
      if chunk_type == 'token':
        email_content += chunk.get('content', '')
      elif chunk_type == 'done':
        trace_id = chunk.get('trace_id')
      elif chunk_type == 'error':
        error_message = chunk.get('error')

    # Parse the email JSON to extract subject and body (same as non-streaming function)
    try:
      # Clean JSON response (inline version of _clean_json_response)
      clean_string = email_content.strip()
      if clean_string.startswith('```json\n') and clean_string.endswith('\n```'):
        clean_string = clean_string[len('```json\n') : -len('\n```')]
      elif clean_string.startswith('```') and clean_string.endswith('```'):
        clean_string = clean_string[3:-3]
      clean_string = clean_string.strip()

      email_json = json.loads(clean_string)

      # Return full email body
      body = email_json.get('body', '')

      result = {'email_subject': email_json.get('subject_line'), 'email_body': body}

      if trace_id:
        result['trace_id'] = trace_id

      return result

    except (json.JSONDecodeError, KeyError) as e:
      # Handle parsing errors gracefully
      result = {
        'email_subject': 'Email generation failed',
        'email_body': f'Failed to parse email: {str(e)}',
      }

      if trace_id:
        result['trace_id'] = trace_id
      else:
        result['trace_id'] = EmailGenerator._get_current_trace_id()
      if error_message:
        result['email_body'] = error_message

      return result

  @mlflow.trace(output_reducer=lambda chunks: EmailGenerator._stream_email_reducer_static(chunks))
  async def stream_generate_email_with_retrieval(
    self, customer_name: str, user_input: Optional[str] = None
  ) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream email generation with customer data retrieval step.

    This is the primary email generation implementation that all other methods use.
    It streams tokens in real-time while maintaining full MLflow tracing capabilities.
    The streaming approach enables responsive UX and efficient resource usage.

    Args:
        customer_name: Name of the customer to generate email for.
                      Must exist in the customer data JSONL file.
        user_input: Optional user instructions to customize email generation.
                   If None or empty, uses default generation behavior.

    Yields:
        Dict[str, Any]: Streaming chunks with the following types:
            - {'type': 'token', 'content': str}: Individual tokens as they're generated
            - {'type': 'done', 'trace_id': str}: Generation complete with trace ID
            - {'type': 'error', 'error': str}: Error information if generation fails

    Raises:
        ValueError: If customer name is not found in data.
        FileNotFoundError: If customer data file is missing.

    Note:
        - Uses MLflow output_reducer to create trace summaries from streaming chunks
        - Loads prompt and retrieves customer data before starting generation
        - Delegates actual streaming to _stream_generate_email method
        - Primary implementation used by both streaming and non-streaming APIs
    """
    # Load the prompt and set the active MLflow model
    self._load_prompt()

    # Retrieve customer data using MLflow RETRIEVER span
    customer_data = self._retrieve_customer_data(customer_name)

    # Stream the email generation
    async for chunk in self._stream_generate_email(customer_data, customer_name, user_input):
      yield chunk

  @mlflow.trace
  async def _stream_generate_email(
    self, customer_data: List[Document], customer_name: str, user_input: Optional[str] = None
  ) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream email generation token by token.

    Core streaming implementation that communicates with the Databricks Model Serving
    endpoint to generate email content token by token. Handles response parsing,
    MLflow trace updates, and completion detection.

    Args:
        customer_data: List of MLflow Documents containing formatted customer information.
                      Each document has page_content (markdown) and metadata.
        customer_name: Customer name for trace metadata and error messages.
        user_input: Optional user instructions for trace tagging and customization.

    Yields:
        Dict[str, Any]: Streaming chunks:
            - {'type': 'token', 'content': str}: Individual tokens from the LLM
            - {'type': 'done', 'trace_id': str}: Successful completion with trace ID
            - {'type': 'error', 'error': str}: JSON parsing or other errors

    Side Effects:
        - Updates MLflow trace with tags (user_instructions: yes/no)
        - Sets trace request_preview and response_preview for better visibility
        - Accumulates full response text for final JSON parsing

    Note:
        - Streams tokens immediately as they arrive from the model
        - Parses complete response at the end to extract structured email data
        - Uses _clean_json_response to handle LLM markdown formatting
        - Traced as LLM span in MLflow for performance and cost monitoring
    """
    # Create streaming response using Databricks Model Serving OpenAI-compatible client
    # This enables real-time token generation while maintaining MLflow tracing
    response = self.openai_client.chat.completions.create(
      model=self.model,
      messages=self._create_messages(customer_data, user_input),
      stream=True,  # Enable streaming for real-time token delivery
    )

    # Collect the full response while streaming for final JSON parsing
    # We need the complete response to extract structured email data
    full_response = ''

    # Stream tokens in real-time while building complete response
    for chunk in response:
      # Check if chunk contains actual content (OpenAI streaming format)
      if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
        token = chunk.choices[0].delta.content
        full_response += token  # Accumulate for final parsing
        yield {'type': 'token', 'content': token}  # Stream immediately to client

    # Parse the complete response to extract structured email data
    # This happens after all tokens have been streamed to ensure we have complete JSON
    try:
      # Clean and parse the accumulated response
      clean_string = self._clean_json_response(full_response)
      email_json = json.loads(clean_string)

      # Update MLflow trace with metadata for evaluation and monitoring
      if user_input is None or len(user_input or '') == 0:
        user_instructions = 'No instructions provided'
        mlflow.update_current_trace(tags={'user_instructions': 'no'})
      else:
        user_instructions = user_input
        mlflow.update_current_trace(tags={'user_instructions': 'yes'})

      # Set trace previews for better visibility in MLflow UI
      mlflow.update_current_trace(
        request_preview=(f'Customer: {customer_name}; User Instructions: {user_instructions}'),
        response_preview=email_json['body'],  # Show email body for quick review
      )

      # Signal successful completion with trace ID for feedback linking
      yield {'type': 'done', 'trace_id': EmailGenerator._get_current_trace_id()}

    except json.JSONDecodeError as e:
      # Handle JSON parsing errors gracefully - LLM may not return valid JSON
      yield {
        'type': 'error',
        'error': f'Failed to parse email JSON: {str(e)}',
      }

  def log_feedback(
    self,
    trace_id: str,
    value: bool,
    comment: Optional[str] = None,
    user_name: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Log user feedback using MLflow 3.0 feedback API.

    Associates human feedback with a specific email generation trace for evaluation
    and model improvement. This enables tracking of email quality over time and
    correlation with model performance metrics.

    Args:
        trace_id: MLflow trace ID to attach feedback to. Obtained from email
                 generation response (both streaming and non-streaming).
        value: Boolean feedback value. True for positive (thumbs up),
              False for negative (thumbs down).
        comment: Optional text comment providing additional feedback context.
                Useful for qualitative analysis and improvement insights.
        user_name: Optional identifier for the feedback provider.
                  Defaults to 'user' if not specified.

    Returns:
        Dict[str, Any]: Result with keys:
            - success: Boolean indicating if feedback was logged successfully
            - message: Human-readable status message

    Example:
        >>> result = generator.log_feedback(
        ...     trace_id="tr-abc123",
        ...     value=True,
        ...     comment="Great email, very professional tone",
        ...     user_name="sales_rep_1"
        ... )
        >>> print(result['success'])  # True if successful

    Note:
        - Uses MLflow 3.0 feedback API (mlflow.log_feedback)
        - Feedback is stored with HUMAN assessment source type
        - Failed submissions return error details in the message field
        - Feedback can be used for model evaluation and quality monitoring
    """
    try:
      # Log feedback using mlflow.log_feedback (MLflow 3 API)
      mlflow.log_feedback(
        trace_id=trace_id,
        name='user_feedback',
        value=value,
        rationale=comment if comment else None,
        source=mlflow.entities.AssessmentSource(
          source_type='HUMAN',
          source_id=user_name or 'user',
        ),
      )

      return {'success': True, 'message': 'Feedback submitted successfully'}

    except Exception as e:
      return {'success': False, 'message': f'Error submitting feedback: {str(e)}'}
