import React, { useState } from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { useQueryExperiment } from "@/queries/useQueryTracing";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, Mail, Plus, UserCheck, BarChart3 } from "lucide-react";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { NotebookReference } from "@/components/notebook-reference";

const introContent = `
# Human Review: Expert Feedback for GenAI Quality

App developers are most often not domain experts in the business use case, and therefore, need help from domain experts to understand what is a low vs high quality response. MLflow's labeling capabilities enable domain experts to systematically review and label GenAI application traces with ground truth, providing invaluable insights to tune your automated quality metrics and understand how your application should respond.

Key benefits:
- **Expert validation** - Domain experts can review traces and provide structured feedback on quality dimensions
- **Systematic labeling** - Create consistent labeling schemas that capture business-critical quality aspects
- **Quality improvement loop** - Convert expert feedback into training data for LLM judges and evaluation benchmarks

MLflow's Review App provides a pre-built UI, designed for business users, that anyone in your company can use, even if they don't have access to your Databricks workspace.

![human-feedback-overview](https://i.imgur.com/7LNlgDP.gif)
`;

const createLabelingSchemasCode = `import mlflow
from mlflow.genai import label_schemas
from datetime import datetime
import uuid

# Define labeling schemas for email quality assessment
schema_configs = {
    'accuracy': {
        'title': 'Are all facts accurate?',
        'instruction': 'Check that all information comes from customer data with no fabrication or errors.',
        'options': ['yes', 'no']  # Note: In practice, yes/no with detailed instructions
    },
    'personalized': {
        'title': 'Is this email personalized?',
        'instruction': "Evaluate if the email is tailored to this customer's specific situation and cannot be reused for others.",
        'options': ['yes', 'no']
    },
    'relevance': {
        'title': 'Is the email relevant to this customer?',
        'instruction': 'Check if urgent issues are prioritized first and content follows proper importance order.',
        'options': ['yes', 'no']
    }
}

# Create label schemas
created_schemas = {}
for schema_name, config in schema_configs.items():
    try:
        schema = label_schemas.create_label_schema(
            name=schema_name,
            type='feedback',
            title=config['title'],
            input=label_schemas.InputCategorical(options=config['options']),
            instruction=config['instruction'],
            enable_comment=True,
            overwrite=True
        )
        created_schemas[schema_name] = schema
        print(f'✅ Created schema: {schema_name}')

    except Exception as e:
        print(f'⚠️  Error creating schema {schema_name}: {e}')

# Create labeling session with timestamp for uniqueness
schema_names = [schema.name for schema in created_schemas.values()]
session_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}-email_quality_review'

session = mlflow.genai.create_labeling_session(
    name=session_name,
    assigned_users=[],  # Empty list allows any authenticated user
    label_schemas=schema_names
)

print(f'✅ Created labeling session: {session_name}')

# Add a specific trace to the labeling session
# Tag the trace for easy identification
unique_tag = str(uuid.uuid4())
mlflow.set_trace_tag(trace_id_for_review, 'tmp_labeling_session_id', unique_tag)

# Find and add the trace
traces_to_label = mlflow.search_traces(
    filter_string=f'tags.tmp_labeling_session_id = "{unique_tag}"',
    max_results=1
)

if len(traces_to_label) > 0:
    session.add_traces(traces_to_label)
    print(f'✅ Added trace to labeling session')

# Access the Review App
print(f'📱 Review App URL: {session.url}')
print(f'📊 MLflow UI URL: {mlflow_ui_url}')`;

export function HumanReview() {
  const { data: experiment, isLoading: experimentIsLoading } =
    useQueryExperiment();

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <NotebookReference
        notebookPath="mlflow_demo/notebooks/4_human_review.ipynb"
        notebookName="4_human_review"
        description="Set up labeling sessions and collect structured expert feedback for quality improvement"
      />
    </div>
  );

  const { data: preloadedResultsData, isLoading: isPreloadedResultsLoading } =
    useQueryPreloadedResults();
  const preloadedLabelingSessionUrl =
    preloadedResultsData?.sample_labeling_session_url;
  const preloadedReviewAppUrl = preloadedResultsData?.sample_review_app_url;
  const preloadedLabelingTraceUrl =
    preloadedResultsData?.sample_labeling_trace_url;

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="Let's explore the complete human review workflow. This demo shows pre-configured labeling sessions so you can experience the Review App interface immediately. For hands-on creation of your own sessions, see the interactive notebook." />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Step 1: View the trace for labeling
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <MarkdownContent content="This trace has been added to the labeling session and is ready for expert review. Click below to view the trace details in MLflow." />
            <Button
              variant="open_mlflow_ui"
              size="lg"
              disabled={isPreloadedResultsLoading || !preloadedLabelingTraceUrl}
              onClick={() =>
                preloadedLabelingTraceUrl &&
                window.open(preloadedLabelingTraceUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View trace in MLflow UI
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Step 2: View the labeling session
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <MarkdownContent content="The trace from Step 1, along with two others, has already been added to a labeling session through the MLflow Traces tab. In practice, you would need to add traces to labeling sessions yourself, but we've pre-configured this for the demo. Click below to view the labeling session and see all traces ready for expert review." />
            <Button
              variant="open_mlflow_ui"
              size="lg"
              disabled={
                isPreloadedResultsLoading || !preloadedLabelingSessionUrl
              }
              onClick={() =>
                preloadedLabelingSessionUrl &&
                window.open(preloadedLabelingSessionUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View the Labeling Session
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5" />
              Step 3: Label the trace in the Review App
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <Button
              variant="open_mlflow_ui"
              size="lg"
              disabled={isPreloadedResultsLoading || !preloadedReviewAppUrl}
              onClick={() =>
                preloadedReviewAppUrl &&
                window.open(preloadedReviewAppUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Label in the Review App
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Step 4: View the labels in the MLflow UI
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">
            <Button
              variant="open_mlflow_ui"
              size="lg"
              disabled={
                isPreloadedResultsLoading || !preloadedLabelingSessionUrl
              }
              onClick={() =>
                preloadedLabelingSessionUrl &&
                window.open(preloadedLabelingSessionUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View labels in the MLflow UI
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Human Review"
      description="Collect expert feedback to improve GenAI quality through structured labeling"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
