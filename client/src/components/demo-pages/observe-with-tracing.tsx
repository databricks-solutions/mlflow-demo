import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { EmailGenerator } from "@/components/email-generator/EmailGenerator";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { NotebookReference } from "@/components/notebook-reference";

const introContent = `
# MLflow Tracing for GenAI Applications

MLflow Tracing provides comprehensive observability for your GenAI applications, allowing you to:

- **Debug** issues by inspecting inputs, outputs, and intermediate steps
- **Collect** user feedback to improve your models
- **Optimize** latency by identifying bottlenecks

Implementing MLflow Tracing only requires *a single line of code*.  You can attach end user feedback from your UI to the corresponding trace so you can quickly debug user-reported issues.

![tracing-demo](https://i.imgur.com/tNYUHdC.gif)
`;

const simpleTracingCode = `
  import mlflow
  import json
  from typing import Dict, Any
  from openai import OpenAI

+ # 🔍 TRACING: Enable automatic tracing of OpenAI SDK calls
+ mlflow.openai.autolog()  # [AUTO-TRACE] Traces all OpenAI calls

  # Import our EmailGenerator class which uses MLflow Tracing
  from mlflow_demo.agent.email_generator import EmailGenerator

  # Initialize the EmailGenerator with environment configuration
  email_generator = EmailGenerator()

  # The EmailGenerator class uses @mlflow.trace decorator
  # Here's a simplified version showing the key tracing implementation:
+ # 🔍 TRACING: Add decorator to trace your function
+ @mlflow.trace  # [MANUAL-TRACE] Captures inputs, outputs, and timing
  def generate_email(customer_data: dict) -> Dict[str, Any]:
      """Generate email with MLflow tracing enabled."""
      # Set application version for tracking
      set_app_version()

      # Create messages for the LLM
      messages = _create_messages(customer_data)

      # Call OpenAI (automatically traced by mlflow.openai.autolog())
      response = openai_client.chat.completions.create(
          model=LLM_MODEL,
          messages=messages,
      )

      # Process the response
      response_content = response.choices[0].message.content
      clean_string = _clean_json_response(response_content)
      email_json = json.loads(clean_string)

+     # 🔍 TRACING: Get trace ID to link feedback
+     email_json['trace_id'] = _get_current_trace_id()  # [TRACE-ID]

      return email_json

  # Usage example - Now uses customer name and user input instead of full customer data
  customer_name = sample_customer["account"]["name"]
  user_input = sample_customer.get("user_input")
  result = email_generator.generate_email_with_retrieval(customer_name, user_input)
  print(f'Email generated with trace_id: {result.get("trace_id")}')`;

const userFeedbackCode = `\`\`\`diff
  import mlflow
  from enum import Enum
  from typing import Optional, Dict, Any
  from pydantic import BaseModel

  # The EmailGenerator class provides a log_feedback method
  class EmailGenerator:
+     # 🔍 FEEDBACK: Add method to log user feedback to traces
      def log_feedback(
          self,
          trace_id: str,
          value: bool,
          comment: str = None,
          user_name: str = None,
      ) -> Dict[str, Any]:
          """Log user feedback using MLflow 3 API.

          Args:
              trace_id: The trace ID to attach feedback to
              value: True for positive feedback, False for negative
              comment: Optional feedback comment
              user_name: Optional user name

          Returns:
              Dict containing success status and message
          """
          try:
-             # Log feedback using mlflow.log_feedback (MLflow 3 API)
+             # 🔍 FEEDBACK: Use mlflow.log_feedback to attach feedback to trace
+             mlflow.log_feedback(  # [FEEDBACK-API] Links feedback to specific trace
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

  # Usage example - Submit positive feedback
+ # 🔍 FEEDBACK: Call log_feedback with trace_id from generation
  positive_feedback = email_generator.log_feedback(
      trace_id=current_trace_id,  # Use trace_id from email generation
      value=True,  # True = positive feedback
      comment='Great email! The tone was perfect and it mentioned the product launch as requested.',
      user_name=customer['sales_rep']['name'],
  )

  print(f'Feedback submitted: {positive_feedback["message"]}')

  # Submit negative feedback
  negative_feedback = email_generator.log_feedback(
      trace_id=second_trace_id,
      value=False,  # False = negative feedback
      comment="The email was too generic and didn't capture our company's specific needs.",
      user_name=customer['sales_rep']['name'],
  )

  # Backend API implementation (FastAPI endpoint):
  @router.post('/feedback', response_model=FeedbackResponse)
  async def submit_feedback(feedback: FeedbackRequest):
      """Submit user feedback linked to trace."""
      try:
-         # Log feedback using mlflow.log_feedback
+         # 🔍 FEEDBACK: Backend also uses mlflow.log_feedback
          mlflow.log_feedback(
              trace_id=feedback.trace_id,
              name='user_feedback',
              value=feedback.rating == 'up',  # Convert to boolean
              rationale=feedback.comment,
              source=mlflow.entities.AssessmentSource(
                  source_type='HUMAN',
                  source_id=feedback.sales_rep_name or 'user',
              ),
          )

          return FeedbackResponse(
              success=True,
              message='Feedback submitted successfully'
          )

      except Exception as e:
          return FeedbackResponse(
              success=False,
              message=f'Error submitting feedback: {str(e)}'
          )
\`\`\``;

const advancedTracingCode = `\`\`\`diff
  from mlflow.entities import SpanType
  from typing import List, Dict, Any

- # Basic function with no tracing
- def _create_messages(customer_data: dict) -> List[Dict[str, str]]:
+ # 🔍 ADVANCED: Add custom attributes and naming to traces
+ @mlflow.trace(
+     name="email-message-creation",  # [CUSTOM-NAME] Better than function name
+     span_type=SpanType.LLM,  # [SPAN-TYPE] Categorize the span
+     attributes={"component": "message_builder", "model": LLM_MODEL}  # [ATTRIBUTES]
+ )
+ def _create_messages(customer_data: dict) -> List[Dict[str, str]]:
      """Create chat messages with detailed tracing."""
      company_name = customer_data.get("company_name", "Unknown")

      system_prompt = f"Generate a personalized email for {company_name}..."
      user_prompt = f"Customer details: {json.dumps(customer_data)}"

      return [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": user_prompt}
      ]

  # Using span context manager for detailed processing steps
  @mlflow.trace
  def generate_email_advanced(customer_data: dict) -> Dict[str, Any]:
      """Generate email with detailed span tracking."""
      set_app_version()

-     # Process messages without tracking
-     messages = _create_messages(customer_data)
+     # 🔍 ADVANCED: Use span context manager for sub-operations
+     with mlflow.start_span(name="message-preparation") as span:  # [SPAN-CONTEXT]
+         span.set_inputs({"customer_data": customer_data})  # [SET-INPUTS]
+         messages = _create_messages(customer_data)
+         span.set_outputs({"message_count": len(messages)})  # [SET-OUTPUTS]

      # OpenAI call (auto-traced by mlflow.openai.autolog())
      response = openai_client.chat.completions.create(
          model=LLM_MODEL,
          messages=messages,
      )

-     # Process response without tracking
-     response_content = response.choices[0].message.content
-     clean_string = _clean_json_response(response_content)
-     email_json = json.loads(clean_string)
+     # 🔍 ADVANCED: Track response processing as separate span
+     with mlflow.start_span(name="response-processing") as span:
+         span.set_inputs({"raw_response": response.choices[0].message.content})
+
+         response_content = response.choices[0].message.content
+         clean_string = _clean_json_response(response_content)
+         email_json = json.loads(clean_string)
+         email_json['trace_id'] = _get_current_trace_id()
+
+         span.set_outputs({"processed_email": email_json})

      return email_json
\`\`\``;

export function TracingDemo() {
  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="Step 1: Instrument with tracing"
        variant="simple"
        // defaultOpen
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/"
      >
        <div className="space-y-4">
          <MarkdownContent
            content={`MLflow supports automatic tracing of 20+ popular GenAI SDKs - from OpenAI to LangChain. Automatic tracing can be supplemented with manual tracing to capture your application's specific logic.

The diff below shows exactly what to add (green lines with + symbols):`}
          />
          <CodeSnippet
            code={simpleTracingCode}
            title=""
            filename="email_generator.py"
            language="diff"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Step 2: Attach user feedback to the trace"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/"
      >
        <div className="space-y-4">
          <MarkdownContent
            content={`MLflow enables you to attach user feedback directly to traces, creating a powerful feedback loop for quality improvement.

The diff below shows the key additions for feedback logging:`}
          />
          <CodeSnippet
            code={userFeedbackCode}
            title=""
            filename="email_generator.py"
            language="diff"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Advanced: Manual Tracing"
        variant="advanced"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/tracing/app-instrumentation/manual-tracing/"
      >
        <div className="space-y-4">
          <MarkdownContent
            content={`For more granular observability, MLflow provides advanced tracing capabilities to capture detailed execution flow.

The diff below shows how to add advanced tracing features:`}
          />
          <CodeSnippet
            code={advancedTracingCode}
            title="Advanced Tracing Features - What to Add"
            filename="email_generator.py"
            language="diff"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/1_observe_with_traces.ipynb"
        notebookName="1_observe_with_traces"
        description=""
      />
    </div>
  );

  const { data: preloadedResultsData, isLoading: isPreloadedResultsLoading } =
    useQueryPreloadedResults();
  const preloadedTraceUrl = preloadedResultsData?.sample_trace_url;

  const demoSection = (
    <div className="space-y-8">
      {/* Step 1: View Pre-generated Example */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-600 rounded-full font-semibold text-sm">
            1
          </div>
          <h3 className="text-lg font-semibold">
            View a pre-generated example
          </h3>
        </div>

        <div className="ml-11 space-y-3">
          <p className="text-muted-foreground">
            Start by viewing a pre-generated example to see how traces capture
            email generation and user feedback.
          </p>

          <div className="p-4 bg-muted/30 rounded-lg border">
            <Button
              variant="open_mlflow_ui"
              size="lg"
              disabled={isPreloadedResultsLoading || !preloadedTraceUrl}
              onClick={() =>
                preloadedTraceUrl && window.open(preloadedTraceUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View sample trace
            </Button>
          </div>
        </div>
      </div>

      {/* Step 2: Try Interactive Demo */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-8 h-8 bg-green-100 text-green-600 rounded-full font-semibold text-sm">
            2
          </div>
          <h3 className="text-lg font-semibold">Try the interactive demo</h3>
        </div>

        <div className="ml-11 space-y-4">
          <p className="text-muted-foreground">
            Generate your own email and provide feedback. Then view the
            resulting MLflow trace with your feedback attached.
          </p>

          <EmailGenerator />
        </div>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Observability with Tracing"
      description="Implement MLflow Tracing for observability and debugging"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
