import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ExternalLink,
  Plus,
  Target,
  Award,
  TrendingUp,
  Trash2,
  Loader2,
} from "lucide-react";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { NotebookReference } from "@/components/notebook-reference";

const introContent = `
# LLM Judges: Scale Your Human Expertise

LLM judges are AI-powered quality assessment tools that scale human expertise to evaluate GenAI quality automatically - in development and production. They assess semantic correctness, style, safety, and relative quality - answering questions like "Does this answer correctly?" and "Is this appropriate for our brand?"

MLflow has 2 flavors of judges:
- **Built-in Judges** - Research-backed judges for safety, hallucination, retrieval quality, and relevance
- **Custom Judges** - Tune our research-backed LLM judges to your business needs and human expert judgment

MLflow also supports *custom code-based metrics*, so if the built-in judges don't fit your use case, you can write your own.

The same judges can be used to both evaluate quality in development and monitor quality in production.

![demo-eval](https://i.imgur.com/M3kLBHF.gif)
`;

const builtinJudgesCode = `import mlflow
import mlflow.genai
from mlflow.genai.scorers import Guidelines, RelevanceToQuery, Safety
from mlflow_demo.agent.email_generator import EmailGenerator
from datetime import datetime

# Create instances of applicable built-in judges
builtin_scorers = [
    RelevanceToQuery(),
    Safety(),
]

print("✅ Created built-in scorers for our use case:")
for scorer in builtin_scorers:
    print(f"   - {scorer.__class__.__name__}")

# Load recent production traces for evaluation
traces = mlflow.search_traces(
    max_results=5,
    filter_string='attributes.status = "OK" and tags.sample_data = "yes"',
    order_by=['attributes.timestamp_ms DESC']
)

# Define prediction function for evaluation
def predict_fn(customer_data: dict):
    """Generate email for evaluation - uses current production prompt"""
    generator = EmailGenerator()
    customer_name = customer_data["account"]["name"]
    user_input = customer_data.get("user_input")
    return generator.generate_email_with_retrieval(customer_name, user_input)

# Run the evaluation
with mlflow.start_run(
    run_name=f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_quality_metrics_demo'
) as run:
    results = mlflow.genai.evaluate(
        data=traces,
        predict_fn=predict_fn,
        scorers=builtin_scorers,
    )
    run_id = run.info.run_id

print(f"✅ Evaluation completed! Run ID: {run_id}")`;

const customJudgesCode = `import mlflow
from mlflow.genai.scorers import Guidelines

# Define custom guidelines for email quality
custom_guidelines = [
    {
        "name": "accuracy",
        "guideline": """The response correctly references all factual information from the provided_info based on these rules:
- All factual information must be directly sourced from the provided data with NO fabrication
- Names, dates, numbers, and company details must be 100% accurate with no errors
- Meeting discussions must be summarized with the exact same sentiment and priority as presented in the data
- Support ticket information must include correct ticket IDs, status, and resolution details when available
- All product usage statistics must be presented with the same metrics provided in the data
- No references to CloudFlow features, services, or offerings unless specifically mentioned in the customer data
- AUTOMATIC FAIL if any information is mentioned that is not explicitly provided in the data"""
    },
    {
        "name": "personalized",
        "guideline": """The response demonstrates clear personalization based on the provided_info based on these rules:
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
    },
    {
        "name": "relevance",
        "guideline": """The response prioritizes content that matters to the recipient in the provided_info based on these rules:
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
    }
]

# Create Guidelines scorers
custom_scorers = [
    Guidelines(name=g["name"], guidelines=g["guideline"])
    for g in custom_guidelines
]

# Combine all scorers
all_scorers = builtin_scorers + custom_scorers

# Run evaluation with combined scorers
results = mlflow.genai.evaluate(
    data=traces,
    predict_fn=predict_fn,
    scorers=all_scorers,
)
`;

const customCodeMetricsCode = `import mlflow
from mlflow.entities import Feedback, Trace
from mlflow.genai.scorers import scorer

@scorer
def tool_call_efficiency(trace: Trace) -> Feedback:
    """Evaluate how effectively the app uses tools"""
    # Retrieve all tool call spans from the trace
    tool_calls = trace.search_spans(span_type="TOOL")

    if not tool_calls:
        return Feedback(
            value=None,
            rationale="No tool usage to evaluate"
        )

    # Check for redundant calls
    tool_names = [span.name for span in tool_calls]
    if len(tool_names) != len(set(tool_names)):
        return Feedback(
            value=False,
            rationale=f"Redundant tool calls detected: {tool_names}"
        )

    # Check for errors
    failed_calls = [s for s in tool_calls if s.status.status_code != "OK"]
    if failed_calls:
        return Feedback(
            value=False,
            rationale=f"{len(failed_calls)} tool calls failed"
        )

    return Feedback(
        value=True,
        rationale=f"Efficient tool usage: {len(tool_calls)} successful calls"
    )

# Run eval on the last 5 production traces
traces = mlflow.search_traces(max_results=5, order_by=['attributes.timestamp_ms DESC'])

mlflow.genai.evaluate(
    data=traces,
    # your application's prediction function
    predict_fn=email_generation_app,
    scorers=[tool_call_efficiency],
)
`;

const judgeValidationCode = `import mlflow
import pandas as pd
from sklearn.metrics import cohen_kappa_score, accuracy_score

# Step 1: Run judges on evaluation dataset with human labels
eval_results = mlflow.genai.evaluate(
    data=eval_dataset_with_human_labels,
    predict_fn=email_generation_app,
    scorers=[
        professionalism_scorer,
        brand_voice_scorer,
        RelevanceToQuery(),
        Safety()
    ]
)

# Step 2: Compare judge scores to human ratings for alignment
def validate_judge_accuracy(eval_results, human_labels_df):
    """Check how well judges align with human expert ratings."""

    # Extract judge scores and human ratings
    judge_scores = eval_results.metrics
    human_ratings = human_labels_df

    alignment_metrics = {}

    for judge_name in ['professionalism', 'brand_voice', 'relevance', 'safety']:
        # Convert scores to binary (pass/fail) for comparison
        judge_binary = (judge_scores[f'{judge_name}_score'] >= 3).astype(int)
        human_binary = (human_ratings[f'human_{judge_name}'] >= 3).astype(int)

        # Calculate agreement metrics
        kappa = cohen_kappa_score(human_binary, judge_binary)
        accuracy = accuracy_score(human_binary, judge_binary)

        alignment_metrics[judge_name] = {
            'kappa': kappa,
            'accuracy': accuracy,
            'human_avg': human_ratings[f'human_{judge_name}'].mean(),
            'judge_avg': judge_scores[f'{judge_name}_score'].mean()
        }

        print(f"{judge_name.title()} Judge Alignment:")
        print(f"  Cohen's Kappa: {kappa:.3f} (>0.6 is good agreement)")
        print(f"  Accuracy: {accuracy:.3f}")
        print(f"  Human avg: {human_ratings[f'human_{judge_name}'].mean():.2f}")
        print(f"  Judge avg: {judge_scores[f'{judge_name}_score'].mean():.2f}\n")

    return alignment_metrics

# Step 3: Identify areas for guideline refinement
def suggest_guideline_improvements(alignment_metrics, threshold=0.6):
    """Suggest which judges need guideline tuning."""

    needs_tuning = []
    for judge_name, metrics in alignment_metrics.items():
        if metrics['kappa'] < threshold:
            needs_tuning.append({
                'judge': judge_name,
                'kappa': metrics['kappa'],
                'issue': 'Low agreement with humans',
                'suggestion': 'Refine guidelines to be more specific and measurable'
            })

        # Check for systematic bias
        score_diff = abs(metrics['human_avg'] - metrics['judge_avg'])
        if score_diff > 1.0:
            needs_tuning.append({
                'judge': judge_name,
                'score_diff': score_diff,
                'issue': 'Systematic scoring bias',
                'suggestion': 'Adjust judge calibration or guideline strictness'
            })

    return needs_tuning

# Step 4: Iterative refinement workflow
def iterative_judge_refinement():
    """Workflow for continuously improving judge-human alignment."""

    print("Judge Validation Workflow:")
    print("1. Run judges on evaluation set with human labels")
    print("2. Calculate agreement metrics (Cohen's Kappa, accuracy)")
    print("3. Identify judges with low human alignment (<0.6 kappa)")
    print("4. Refine guidelines based on disagreement patterns")
    print("5. Re-run evaluation and measure improvement")
    print("6. Repeat until satisfactory alignment achieved")

    # Example: Updated guidelines after human feedback
    refined_professionalism_guidelines = """
    ## Refined Email Professionalism Guidelines

    ### Tone Requirements (Based on Human Feedback)
    - Use formal business language for enterprise customers (>1000 employees)
    - Use friendly but professional tone for SMB customers (<1000 employees)
    - Avoid contractions in first contact emails
    - Match customer's communication style from previous interactions

    ### Specific Pass/Fail Criteria
    - PASS: Addresses customer by correct name and title
    - PASS: References specific recent interaction or context
    - FAIL: Uses generic greetings like "Dear Valued Customer"
    - FAIL: Includes placeholder text or template artifacts
    """

    return refined_professionalism_guidelines

# Run validation
alignment_results = validate_judge_accuracy(eval_results, human_labels_df)
tuning_suggestions = suggest_guideline_improvements(alignment_results)`;

export function EvaluationBuilder() {
  const [builtinJudges, setBuiltinJudges] = React.useState([
    {
      name: "RelevanceToQuery",
      description: "Does the response directly address the user's input?",
      enabled: false,
    },
    {
      name: "Safety",
      description: "Does the response avoid harmful or toxic content?",
      enabled: true,
    },
    {
      name: "RetrievalGroundedness",
      description: "Is the response grounded in retrieved information?",
      enabled: false,
      disabled: true,
      disabledReason:
        "This judge is designed for apps with a retrieval step, which doesn't apply to this demo",
    },
    {
      name: "RetrievalRelevance",
      description: "Are retrieved documents relevant to the user's request?",
      enabled: false,
      disabled: true,
      disabledReason:
        "This judge is designed for apps with a retrieval step, which doesn't apply to this demo",
    },
    {
      name: "Correctness",
      description: "Is the response correct compared to ground-truth answer?",
      enabled: false,
      disabled: true,
      disabledReason:
        "This judge is designed for use with human labeled ground truth answers, which doesn't apply to this demo.",
    },
    {
      name: "RetrievalSufficiency",
      description:
        "Do the retrieved documents contain all necessary information in the ground truth answer?",
      disabledReason:
        "This judge is designed for use with human labeled ground truth answers AND a retrieval step, which doesn't apply to this demo.",
      enabled: false,
      disabled: true,
    },
  ]);

  const [guidelines, setGuidelines] = React.useState([
    {
      id: "accuracy",
      name: "accuracy",
      content: `The response correctly references all factual information from the provided_info based on these rules:
- All factual information must be directly sourced from the provided data with NO fabrication
- Names, dates, numbers, and company details must be 100% accurate with no errors
- Meeting discussions must be summarized with the exact same sentiment and priority as presented in the data
- Support ticket information must include correct ticket IDs, status, and resolution details when available
- All product usage statistics must be presented with the same metrics provided in the data
- No references to CloudFlow features, services, or offerings unless specifically mentioned in the customer data
- AUTOMATIC FAIL if any information is mentioned that is not explicitly provided in the data`,
    },
    {
      id: "personalized",
      name: "personalized",
      content: `The response demonstrates clear personalization based on the provided_info based on these rules:
- Email must begin by referencing the most recent meeting/interaction
- Immediatly next, the email must address the customer's MOST pressing concern as evidenced in the data
- Content structure must be customized based on the account's health status (critical issues first for "Fair" or "Poor" accounts)
- Industry-specific language must be used that reflects the customer's sector
- Recommendations must ONLY reference features that are:
  a) Listed as "least_used_features" in the data, AND
  b) Directly related to the "potential_opportunity" field
- Relationship history must be acknowledged (new vs. mature relationship)
- Deal stage must influence communication approach (implementation vs. renewal vs. growth)
- AUTOMATIC FAIL if recommendations could be copied to another customer in a different situation`,
    },
    {
      id: "relevance",
      name: "relevance",
      content: `The response prioritizes content that matters to the recipient in the provided_info based on these rules:
- Critical support tickets (status="Open (Critical)") must be addressed after the greeting, reference to the most recent interaction, any pleasantrys, and references to closed tickets
    - it is ok if they name is slightly different as long as it is clearly the same issue as in the provided_info
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
- AUTOMATIC FAIL if the email requests a meeting without being tied to a specific action item or opportunity in the data`,
    },
  ]);

  const [humanAlignment, setHumanAlignment] = React.useState([
    { judge: "Professionalism", kappa: 0.78, accuracy: 0.85, status: "good" },
    { judge: "Brand Voice", kappa: 0.65, accuracy: 0.72, status: "good" },
    { judge: "Relevance", kappa: 0.45, accuracy: 0.68, status: "needs_tuning" },
    { judge: "Safety", kappa: 0.92, accuracy: 0.95, status: "excellent" },
  ]);

  // Helper functions for managing guidelines
  const addGuideline = () => {
    const newGuideline = {
      id: `guideline-${Date.now()}`,
      name: "",
      content: "",
    };
    setGuidelines([...guidelines, newGuideline]);
  };

  const updateGuideline = (
    id: string,
    field: "name" | "content",
    value: string,
  ) => {
    setGuidelines(
      guidelines.map((guideline) =>
        guideline.id === id ? { ...guideline, [field]: value } : guideline,
      ),
    );
  };

  const removeGuideline = (id: string) => {
    if (guidelines.length > 1) {
      setGuidelines(guidelines.filter((guideline) => guideline.id !== id));
    }
  };

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="1. Built-in LLM Judges"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/predefined-judge-scorers"
        // defaultOpen
      >
        <div className="space-y-4">
          <MarkdownContent content="Start with MLflow's research-backed judges for common evaluation needs. These provide accurate quality evaluation aligned with human expertise for safety, hallucination, retrieval quality, and relevance." />
          <CodeSnippet
            code={builtinJudgesCode}
            title="Built-in LLM Judges"
            // filename="builtin_judges.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="2. Customized LLM Judges for your use case"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-judge/"
      >
        <div className="space-y-4">
          <MarkdownContent content="Create custom LLM judges tailored to your business needs, aligned with your human expert judgment. Work with domain experts to define clear, specific guidelines that scale your expertise." />
          <CodeSnippet
            code={customJudgesCode}
            title="Custom Guidelines-Based Judges"
            // filename="custom_judges.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="3. Custom Code-Based Metrics"
        variant="advanced"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-scorers"
      >
        <div className="space-y-4">
          <MarkdownContent content="If the built-in judges don't fit your use case, you can write your own custom code-based metrics.  This example shows how to write a metric that checks for redundant tool calls." />
          <CodeSnippet
            code={customCodeMetricsCode}
            title="Custom Code-Based Metrics"
            // filename="custom_code_metrics.py"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/2_create_quality_metrics.ipynb"
        notebookName="2_create_quality_metrics"
        description="Create and test your own LLM judges with built-in and custom guidelines"
      />
    </div>
  );

  const { data: preloadedResultsData, isLoading: isPreloadedResultsLoading } =
    useQueryPreloadedResults();
  const preloadedResultsUrl = preloadedResultsData?.metrics_result_url;

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="Below is an example configuration showing how to set up LLM judges for email quality evaluation. We've configured the Safety judge and three custom guidelines that were used to evaluate recent production traces." />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Built-in Judges are tuned by Databricks' research team for
              accuracy and provide common quality evaluation.
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <TooltipProvider>
              {builtinJudges.map((judge, index) => (
                <div key={index} className="flex items-start space-x-3">
                  {judge.disabled ? (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <div className="flex items-start space-x-3 w-full cursor-not-allowed">
                          <input
                            type="checkbox"
                            id={`judge-${index}`}
                            checked={false}
                            disabled={true}
                            className="mt-1 opacity-50 cursor-not-allowed"
                          />
                          <div className="flex-1">
                            <Label
                              htmlFor={`judge-${index}`}
                              className="font-medium text-sm opacity-50 cursor-not-allowed"
                            >
                              {judge.name}
                            </Label>
                            <p className="text-xs text-muted-foreground mt-1 opacity-50">
                              {judge.description}
                            </p>
                          </div>
                        </div>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>{judge.disabledReason}</p>
                      </TooltipContent>
                    </Tooltip>
                  ) : (
                    <>
                      <input
                        type="checkbox"
                        id={`judge-${index}`}
                        checked={judge.enabled}
                        disabled={true}
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <Label
                          htmlFor={`judge-${index}`}
                          className="font-medium text-sm"
                        >
                          {judge.name}
                        </Label>
                        <p className="text-xs text-muted-foreground mt-1">
                          {judge.description}
                        </p>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </TooltipProvider>
          </CardContent>
        </Card>

        {/* Custom Guidelines */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              Guidelines allow you to customize Databricks' built-in judges to
              your use case.
            </CardTitle>
            <br />
            Guidelines have the distinct advantage of being easy to explain to
            business stakeholders ("we are evaluating if the app delivers upon
            this set of rules") and, as such, can often be directly written by
            domain experts.
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Guidelines</Label>
              </div>

              {guidelines.map((guideline, index) => (
                <div
                  key={guideline.id}
                  className="border rounded-lg p-4 space-y-3"
                >
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <Label htmlFor={`guideline-name-${guideline.id}`}>
                        Guideline Name
                      </Label>
                      <Input
                        id={`guideline-name-${guideline.id}`}
                        value={guideline.name}
                        disabled={true}
                        placeholder="e.g., Email Professionalism"
                        className="mt-1"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor={`guideline-content-${guideline.id}`}>
                      Guideline
                    </Label>
                    <Textarea
                      id={`guideline-content-${guideline.id}`}
                      value={guideline.content}
                      disabled={true}
                      rows={8}
                      className="mt-1 font-mono text-xs"
                      placeholder="Define your custom evaluation guidelines..."
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* <div className="flex gap-2">
              <Button size="sm" variant="outline">
                Preview
              </Button>
              <Button size="sm">Create Judge</Button>
            </div> */}
          </CardContent>
        </Card>

        <div className="space-y-4 mb-4">
          <div className="flex gap-4">
            <Button
              variant="open_mlflow_ui"
              size="lg"
              onClick={() =>
                preloadedResultsUrl &&
                window.open(preloadedResultsUrl, "_blank")
              }
              disabled={isPreloadedResultsLoading || !preloadedResultsUrl}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              View Results
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Evaluate quality using LLM judges"
      description="Scale your human expertise with LLM judges for automated quality evaluation that is tuned to your use case"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
