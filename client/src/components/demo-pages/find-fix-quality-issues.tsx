import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink, Plus, UserCheck, BarChart3 } from "lucide-react";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { NotebookReference } from "@/components/notebook-reference";

const introContent = `
# Collect Ground Truth Labels from Domain Experts

## Why Ground Truth Labels Matter

**The key to high-quality GenAI applications is curating a verified evaluation dataset through domain expert feedback.**

You've created baseline LLM judges, but how do you know they're aligned with actual coaching expertise? App developers typically aren't domain experts in NFL defensive strategy, so **collecting structured feedback from SMEs (coaching staff) is critical** for two reasons:

1. **Curate a verified evaluation dataset**: Build a ground truth dataset of traces labeled by experts that becomes the gold standard for measuring quality
2. **Optimize judges to human preferences**: Expert feedback directly improves LLM judges in the next step—judges learn to match coaching staff judgment rather than generic LLM preferences

Without this systematic feedback collection, you're left with ad-hoc quality assessment: scattered Excel spreadsheets, Microsoft Teams messages with opinions, and no clear path to improving your system. **This doesn't scale**.

## MLflow's Managed Solution: SME Review & Labeling Sessions

**The game-changer**: MLflow now provides a **managed UI for SME review and labeling sessions** that gives domain experts a built-in interface to provide feedback—**and it automatically streams back into Databricks**. No more manual data collection, no more Excel files floating around, no more hunting for feedback in chat threads.

### What MLflow Labeling Sessions Provide:

1. **Structured Feedback Collection** - Define exactly what you want to measure (yes/no, ratings, categorical choices, free-text) with customizable schemas aligned to your quality dimensions
2. **Built-in Review App UI** - A polished, non-technical interface designed specifically for SMEs to review GenAI traces—**no Databricks workspace access required**, just share a URL. Labels flow directly into MLflow, linked to the original traces and immediately available for analysis and judge optimization.

This creates a **continuous improvement cycle**: **Traces → Labeling Sessions → Expert Review → Judge Alignment → Prompt Optimization → Improved Quality**

### The Self-Optimizing Architecture

This SME labeling step enables the self-optimizing system. Expert labels validate your judges, create verified datasets for judge alignment, and enable automatic prompt optimization—**without systematic SME feedback collection, you can't optimize**. MLflow makes this seamless.

<div style="text-align: center; margin: 30px 0;">
  <img src="/sme-labeling-optimize.png" alt="SME Labeling in the Optimize Loop" style="max-width: 700px; width: 100%; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);" />
</div>
`;

const createLabelingSchemasCode = `import mlflow
from mlflow.genai import label_schemas
from datetime import datetime

# Define labeling schemas tailored to DC Assistant quality assessment
# These schemas align with our custom LLM judges for consistency
schema_configs = {
    'football_language': {
        'title': 'Does the analysis use correct football terminology?',
        'instruction': '''Evaluate whether the response uses appropriate NFL terminology and coaching language:
        - Correct formation names (I-formation, shotgun, pistol, etc.)
        - Accurate personnel packages (11 = 1 RB, 1 TE, 3 WR; 12 = 1 RB, 2 TE, 2 WR, etc.)
        - Standard coverage/blitz terminology (Cover 2, Cover 3, A-gap pressure, etc.)
        - Proper down-and-distance notation (e.g., "3rd and 6", "2nd and long")

        PASS: All terminology is accurate and appropriate for coaching staff
        FAIL: Contains incorrect terminology or suggests lack of football knowledge''',
        'options': ['pass', 'fail']
    },
    'data_grounded': {
        'title': 'Is the analysis grounded in actual data?',
        'instruction': '''Check whether recommendations are based on real play-by-play data:
        - Analysis references specific percentages or frequency metrics from data
        - Tendencies are supported by actual statistics from tool call results
        - No hallucinated data that wasn't present in the query results

        PASS: All claims are backed by data shown in the trace
        FAIL: Contains unsupported claims or hallucinated statistics''',
        'options': ['pass', 'fail']
    },
    'strategic_soundness': {
        'title': 'Are the defensive recommendations strategically sound?',
        'instruction': '''Assess whether the defensive strategy makes sense for game planning:
        - Recommendations address the specific situation (down-and-distance, personnel, etc.)
        - Counter-strategies are appropriate for the opponent tendencies shown
        - Advice is actionable and specific (not generic coaching platitudes)
        - Key matchups and adjustments are relevant

        Rate from 1 (poor strategy) to 5 (excellent strategy)''',
        'options': ['1', '2', '3', '4', '5']
    },
    'overall_quality': {
        'title': 'Would you trust this analysis for actual game preparation?',
        'instruction': '''As a coaching professional, rate whether this analysis would be useful for preparing a game plan.

        1 = Not usable - contains errors or unhelpful advice
        3 = Acceptable - correct but not particularly insightful
        5 = Excellent - actionable insights that would inform game planning''',
        'options': ['1', '2', '3', '4', '5']
    }
}

# Create label schemas
created_schemas = {}
for schema_name, config in schema_configs.items():
    try:
        # Determine input type based on options
        if all(opt.isdigit() for opt in config['options']):
            input_schema = label_schemas.InputCategorical(
                options=config['options'],
                allow_multiple=False
            )
        else:
            input_schema = label_schemas.InputCategorical(
                options=config['options']
            )

        schema = label_schemas.create_label_schema(
            name=schema_name,
            type='feedback',
            title=config['title'],
            input=input_schema,
            instruction=config['instruction'],
            enable_comment=True,  # Allow reviewers to add contextual notes
            overwrite=True
        )
        created_schemas[schema_name] = schema
        print(f'✅ Created schema: {schema_name}')

    except Exception as e:
        print(f'⚠️  Error creating schema {schema_name}: {e}')

print(f"\\n✅ Created {len(created_schemas)} labeling schemas for DC Assistant review")`

const createLabelingSessionCode = `import mlflow
from datetime import datetime
import uuid

# Create labeling session with descriptive name
schema_names = [schema.name for schema in created_schemas.values()]
session_name = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}-dc_assistant_quality_review'

session = mlflow.genai.create_labeling_session(
    name=session_name,
    assigned_users=[],  # Empty list allows any authenticated user to label
    label_schemas=schema_names
)

print(f'✅ Created labeling session: {session_name}')

# Add production traces that need expert review
# Target traces where LLM judges had low confidence or disagreement
traces_for_review = mlflow.search_traces(
    filter_string="""
        attributes.status = "OK"
        AND tags.sample_data = "yes"
        AND (
            attributes.mlflow.feedback.football_language_score < 0.7
            OR attributes.mlflow.feedback.football_analysis_score < 0.7
        )
    """,
    max_results=20,
    order_by=['attributes.timestamp_ms DESC']
)

# Add traces to the labeling session
if len(traces_for_review) > 0:
    session.add_traces(traces_for_review)
    print(f'✅ Added {len(traces_for_review)} traces to labeling session for expert review')
else:
    print('⚠️  No traces found matching criteria')

# Generate Review App URL for coaching staff
print(f'\\n📱 Share this Review App URL with coaching staff:')
print(f'   {session.url}')
print(f'\\n📊 Track labeling progress in MLflow UI:')
print(f'   {mlflow_ui_url}/experiments/{experiment_id}/traces')`

export function PromptTesting() {
  const { data: preloadedResultsData, isLoading: isPreloadedResultsLoading } =
    useQueryPreloadedResults();
  const preloadedReviewAppUrl = preloadedResultsData?.sample_review_app_url;

  const judgeAssessmentTraceUrl = "https://e2-demo-field-eng.cloud.databricks.com/ml/experiments/1879320556980726/traces?o=1444828305810485&sqlWarehouseId=862f1d757f0424f7&selectedEvaluationId=tr-77922f4435e77a874ce9bd825fe8ea5b";
  const labelSchemasUrl = "https://e2-demo-field-eng.cloud.databricks.com/ml/experiments/1879320556980726/label-schemas?o=1444828305810485";

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="1. Create Labeling Schemas"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces"
      >
        <div className="space-y-4">
          <MarkdownContent content="Define the specific quality dimensions you want coaching staff to evaluate. Schemas can use yes/no, rating scales, or categorical choices. Align schemas with your LLM judges for direct comparison." />
          <CodeSnippet
            code={createLabelingSchemasCode}
            title="Define Labeling Schemas for DC Assistant"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="2. Create Labeling Session & Add Traces"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces"
      >
        <div className="space-y-4">
          <MarkdownContent content="Create a labeling session that groups traces for review. Target traces where judges had low confidence or where you need human validation. The Review App URL can be shared with non-technical SMEs." />
          <CodeSnippet
            code={createLabelingSessionCode}
            title="Create Session and Add Traces"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/3_collect_ground_truth_labels.ipynb"
        notebookName="3_collect_ground_truth_labels"
        description="Set up labeling sessions and collect structured expert feedback for quality improvement"
      />
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="We have LLM judge outputs showing the current quality assessment. Now we need domain experts to validate those assessments and provide ground truth labels. Walk through the three steps below to see the full SME feedback collection workflow." />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Step 1: View the LLM judge assessments
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MarkdownContent content="Start by reviewing the current LLM judge outputs on existing traces. These automated assessments show how the system currently scores DC Assistant responses across quality dimensions like football language, data groundedness, and strategic soundness. This is the baseline that SME feedback will validate and improve." />
            <Button
              variant="open_mlflow_ui"
              size="lg"
              onClick={() =>
                window.open(judgeAssessmentTraceUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View trace with judge assessments
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Step 2: Configure the labeling schema
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MarkdownContent content="A **labeling schema** defines exactly what you want SMEs to evaluate on each trace — the quality dimensions, the rating type (pass/fail, 1-5 scale, categorical), and the instructions reviewers see. Schemas are reusable across labeling sessions and align directly with your LLM judges so human labels can be compared to automated scores. View the pre-configured schemas for the DC Assistant below." />
            <Button
              variant="open_mlflow_ui"
              size="lg"
              onClick={() =>
                window.open(labelSchemasUrl, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View Labeling Schema Configuration
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCheck className="h-5 w-5" />
              Step 3: Kick off a labeling session with the Review App
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MarkdownContent content="A labeling session groups traces with your schemas and launches the Review App for coaching staff. The Review App is a polished, non-technical interface that doesn't require Databricks workspace access — just share the URL. Try labeling a trace yourself: review the question and analysis, evaluate against each quality dimension, add comments, and submit. Labels flow directly back into MLflow, linked to the original traces." />
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
              Launch Review App
            </Button>
            <div className="mt-4 p-3 bg-muted/50 rounded-lg border text-sm text-muted-foreground">
              <p>
                <strong>Want a fully customizable Review App?</strong> Databricks provides an open-source custom Review App template you can iterate on and deploy with Claude Code.{" "}
                <a
                  href="https://github.com/databricks-solutions/custom-mlflow-review-app"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary underline hover:no-underline"
                >
                  Git repo with video instructions
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Collect Ground Truth Labels"
      description="Collect expert feedback to improve GenAI quality through structured labeling"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
