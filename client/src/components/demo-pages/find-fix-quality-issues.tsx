import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { Collapsible } from "@/components/ui/collapsible";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useQueryExperiment } from "@/queries/useQueryTracing";
import {
  useQueryFixedPrompt,
  useQueryCurrentProductionPrompt,
} from "@/queries/useQueryFixedPrompt";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { NotebookReference } from "@/components/notebook-reference";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ExternalLink, Eye, ArrowLeft } from "lucide-react";
import ReactDiffViewer from "react-diff-viewer";

const introContent = `
# Systematic Quality Improvement with MLflow

Learn to systematically find and fix quality issues in your GenAI application using a real-world scenario. In this hands-on workflow, we'll address accuracy problems where the email generator is "hallucinating" information not present in the customer data.

## The Problem Scenario

Your email generation system has been running in production, but users report accuracy issues. Some emails contain fabricated details about:
- Product features not mentioned in customer data
- Meeting discussions that didn't happen as described
- Support ticket information with incorrect details

## The Solution Workflow

Follow this systematic 6-step process to identify, fix, and safely deploy improvements:

1. **🔍 Discover quality issues** Find problematic traces using evaluation results
2. **📊 Create Evaluation Datasets** Turn bad traces into targeted evaluation sets, good traces into regression sets
3. **🎯 Iterate on changes** Use MLflow Prompt Registry to track your changes
4. **🧪 Evaluate changes improved quality** Test that your changes addressed the quality problems
5. **🛡️ Verify changes didn't cause a regression** Ensure fixes don't break user inputs that already work well
6. **🚀 Deploy**

This approach ensures evidence-based improvements rather than guesswork, with quantitative validation and safe deployment practices.

![test-new-prompt](https://i.imgur.com/4wlhT63.gif)

`;

const historicalTestingCode = `import mlflow

# Set MLflow tracking URI to Databricks
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Create an evaluation dataset
eval_dataset = mlflow.genai.datasets.create_dataset(name=f'{UC_CATALOG}.{UC_SCHEMA}.my_eval_set')

# Add traces to the evaluation dataset
traces = mlflow.search_traces(max_results=5) # replace with a filter that identifies the traces you want to evaluate
eval_dataset.merge_records(traces)

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    # your application's prediction function
    predict_fn=email_generation_app,
    scorers=[
        ... # judges from the previous step
    ]
)
`;

const abTestingCode = `import mlflow

# Set MLflow tracking URI to Databricks
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Get your evaluation dataset
eval_dataset = mlflow.genai.datasets.get_dataset(name=f'{UC_CATALOG}.{UC_SCHEMA}.my_eval_set')

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    # your application's prediction function with the new prompt/logic
    predict_fn=email_generation_app,
    scorers=[
        ... # judges from the previous step
    ]
)`;

const regressionTestingCode = `import mlflow

# Set MLflow tracking URI to Databricks
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Get your evaluation dataset
eval_dataset = mlflow.genai.datasets.get_dataset(name=f'{UC_CATALOG}.{UC_SCHEMA}.my_regression_set')

eval_results = mlflow.genai.evaluate(
    data=eval_dataset,
    # your application's prediction function with the new prompt/logic
    predict_fn=email_generation_app,
    scorers=[
        ... # judges from the previous step
    ]
)`;

export function PromptTesting() {
  const { data: experiment } = useQueryExperiment();
  const { data: fixedPromptData, isLoading: isFixedPromptLoading } =
    useQueryFixedPrompt();
  const {
    data: currentProductionPromptData,
    isLoading: isCurrentProductionPromptLoading,
  } = useQueryCurrentProductionPrompt();

  const [viewMode, setViewMode] = React.useState<"edit" | "diff">("edit");

  // Get fixed prompt from API, fallback to loading state or default
  const fixedPromptText =
    fixedPromptData?.prompt ||
    (isFixedPromptLoading
      ? "Loading example fixed prompt..."
      : "You are an expert sales communication assistant for CloudFlow Inc. Your task is to generate a personalized, professional follow-up email for our sales representatives to send to their customers at the end of the day.");

  // Get current production prompt from API, fallback to loading state or default
  const currentProductionPrompt =
    currentProductionPromptData?.prompt ||
    (isCurrentProductionPromptLoading
      ? "Loading current production prompt..."
      : "You are an expert sales communication assistant for CloudFlow Inc. Your task is to generate a personalized, professional follow-up email for our sales representatives to send to their customers at the end of the day.");

  const [newPromptText, setNewPromptText] = React.useState(fixedPromptText);

  // Update newPromptText when fixedPromptData loads
  React.useEffect(() => {
    if (fixedPromptData?.prompt) {
      setNewPromptText(fixedPromptData.prompt);
    }
  }, [fixedPromptData?.prompt]);

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="Step 1: Create an evaluation dataset with production traces"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/build-eval-dataset"
      >
        <div className="space-y-4">
          {/* <MarkdownContent content="Test new prompt versions against real production data to validate improvements before deployment." /> */}
          <CodeSnippet
            code={historicalTestingCode}
            // title="Historical Data Testing"
            // filename="historical_testing.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Step 2: Evaluate the quality of each new version"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/evaluate-app"
      >
        <div className="space-y-4">
          {/* <MarkdownContent content="Run controlled A/B tests to compare prompt variants with statistical significance." /> */}
          <CodeSnippet
            code={abTestingCode}
            // title="A/B Testing Implementation"
            // filename="ab_testing.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Step 3: Before deploying, verify that changes did not cause regressions"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/evaluate-app"
      >
        <div className="space-y-4">
          <MarkdownContent content="Regression testing using an evaluation dataset is the same approach as evaluating a new prompt version.  The only difference is that you are using a sample of all production traces to verify that the new version did not cause regressions." />
          <CodeSnippet
            code={regressionTestingCode}
            // title="Regression Testing & Safe Deployment"
            // filename="safe_deployment.py"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/3_find_fix_quality_issues.ipynb"
        notebookName="3_find_fix_quality_issues"
        description="Work through the complete quality improvement workflow with evaluation datasets and prompt testing"
      />
    </div>
  );

  const { data: preloadedResultsData, isLoading: isPreloadedResultsLoading } =
    useQueryPreloadedResults();
  const lowAccuracyResultsUrl = preloadedResultsData?.low_accuracy_results_url;
  const regressionResultsUrl = preloadedResultsData?.regression_results_url;

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="Let's break down the process of finding and fixing a quality issue." />

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {/* <Target className="h-5 w-5" /> */}
              🔍 Step 1: Discover Quality Issues in Production Traces
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MarkdownContent content="Start by analyzing production traces to identify specific quality problems. Here, we've identified traces that fail the accuracy assessment - the root cause analysis shows the LLM is hallucinating information about products, meetings, and features not present in the customer data." />
            <Button
              variant="open_mlflow_ui"
              size="lg"
              onClick={() =>
                window.open(`${experiment.failed_traces_url}`, "_blank")
              }
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Find low quality traces using the MLflow UI
            </Button>
            <CollapsibleSection
              title="See how to find low quality traces"
              variant="simple"
            >
              <MarkdownContent content="![trace-bd](https://i.imgur.com/ms0W5d6.gif)"></MarkdownContent>
              {/* <MarkdownContent
                content={`
              />
              <MarkdownContent
                content=`## Generated email


                Hi James,\n\nI hope this message finds you well. It was great connecting with you on June 22nd to review AeroTech Dynamics’ current projects and explore opportunities for optimizing your engineering workflows. I wanted to take a moment to recap key items and provide a few updates:\n\n- **Action Items from Our Discussion:**  \n  - Identify key areas for process improvements in collaboration with your team.  \n  - Coordinate a training session for your team on the new features in our platform. I’d be happy to help set this up at a time that works best for you.  \n  - Prepare a project success report—I'll follow up next week to ensure we’re aligned on your goals.\n\n- **Support Ticket Update:**  \n  The issue with the bug in the project reporting feature (Ticket ID: TK-7001) has been resolved. Please let me know if you experience any further challenges.\n\n- **Positive Usage Trends:**  \n  It’s worth noting that AeroTech Dynamics’ active user base on our platform has grown by 3% since last month, which is fantastic to see. The heavy use of Project Management and Resource Allocation features underscores your team’s dedication to streamlined operations.\n\nIn addition, I’d like to recommend exploring the Supplier Management feature. Given our discussion about enhancing project efficiency, incorporating this tool could help streamline processes with vendors and suppliers. I’d be happy to provide a brief walkthrough if needed.\n\n**Next Steps:**  \nLet me know if there’s a specific time next week that works for scheduling the training session or if you’d like to meet again to dive deeper into the Supplier Management feature.\n\nAs always, don’t hesitate to reach out if there’s anything else I can assist you with in the meantime.\n\nBest regards,  \nAngela White  \nSenior Sales Consultant  \nCloudFlow Inc.  \n(555) 333-4444"
              /> */}
            </CollapsibleSection>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Step 2: Create Evaluation and Regression Datasets
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MarkdownContent content="Create two datasets: an evaluation dataset from traces with low quality issues to test improvements, and a regression dataset from high-quality traces to ensure we don't break existing functionality." />

            <div className="flex gap-3">
              <Button
                variant="open_mlflow_ui"
                size="lg"
                onClick={() =>
                  window.open(`${experiment.eval_dataset_url}`, "_blank")
                }
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View evaluation datasets in the MLflow UI
              </Button>
            </div>
            <CollapsibleSection
              title="See how to add traces to evaluation datasets"
              variant="simple"
            >
              <MarkdownContent content="![trace-bd](https://i.imgur.com/o9CSgfK.gif)"></MarkdownContent>
            </CollapsibleSection>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              🎯 Step 3: Develop and Test Improved Prompts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <MarkdownContent content="Use MLflow Prompt Registry for version control and create an improved prompt that addresses the identified problems. Based on our root cause analysis, we've created a new prompt version with explicit NO FABRICATION rules to prevent hallucinations about product features and customer interactions." />

            {/* <div className="flex gap-4">
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-2" />
                View A/B Test Results
              </Button>
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-2" />
                MLflow Experiments
              </Button>
            </div> */}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Selected Prompt Details */}
              <Card className="opacity-60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-muted-foreground">
                    {/* <TrendingUp className="h-5 w-5" /> */}
                    Baseline Prompt
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-muted-foreground">
                  <div>
                    <label className="text-sm font-medium">
                      Prompt Template
                    </label>
                    <Textarea
                      value={currentProductionPrompt}
                      rows={20}
                      className="font-mono text-sm"
                      readOnly
                    />
                  </div>

                  {/* <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-green-600">
                  {
                    testResults[selectedPrompt as keyof typeof testResults]
                      .score
                  }
                </div>
                <div className="text-sm text-muted-foreground">
                  Quality Score
                </div>
              </div>
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {(
                    testResults[selectedPrompt as keyof typeof testResults]
                      .feedback * 100
                  ).toFixed(0)}
                  %
                </div>
                <div className="text-sm text-muted-foreground">
                  User Approval
                </div>
              </div>
            </div> */}

                  {/* <div className="space-y-2">
              <Button className="w-full">Deploy to Production</Button>
              <Button className="w-full" variant="outline">
                Run Regression Test
              </Button>
            </div> */}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      {/* <TrendingUp className="h-5 w-5" /> */}
                      🎯 New Prompt
                    </span>
                    <Button
                      variant={viewMode === "diff" ? "default" : "outline"}
                      size="sm"
                      onClick={() =>
                        setViewMode(viewMode === "edit" ? "diff" : "edit")
                      }
                    >
                      {viewMode === "edit" ? (
                        <>
                          <Eye className="h-4 w-4 mr-1" />
                          View differences
                        </>
                      ) : (
                        <>
                          <ArrowLeft className="h-4 w-4 mr-1" />
                          Back to edit
                        </>
                      )}
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium">
                        Prompt Template
                      </label>
                      <Badge variant="outline" className="text-xs">
                        {viewMode === "diff" ? "Diff View" : "Edit Mode"}
                      </Badge>
                    </div>
                    {viewMode === "edit" ? (
                      <Textarea
                        value={newPromptText}
                        onChange={(e) => setNewPromptText(e.target.value)}
                        rows={20}
                        className="font-mono text-sm"
                        placeholder="Edit your prompt here..."
                      />
                    ) : (
                      <div className="border rounded-md">
                        <ReactDiffViewer
                          oldValue={currentProductionPrompt}
                          newValue={newPromptText}
                          splitView={false}
                          useDarkTheme={false}
                          hideLineNumbers={true}
                          showDiffOnly={false}
                          styles={{
                            variables: {
                              light: {
                                codeFoldGutterBackground: "#f8f9fa",
                                codeFoldBackground: "#f8f9fa",
                              },
                            },
                            contentText: {
                              fontSize: "12px",
                              fontFamily:
                                'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                            },
                          }}
                        />
                      </div>
                    )}
                  </div>
                  {/*
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-green-600">
                  {
                    testResults[selectedPrompt as keyof typeof testResults]
                      .score
                  }
                </div>
                <div className="text-sm text-muted-foreground">
                  Quality Score
                </div>
              </div>
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {(
                    testResults[selectedPrompt as keyof typeof testResults]
                      .feedback * 100
                  ).toFixed(0)}
                  %
                </div>
                <div className="text-sm text-muted-foreground">
                  User Approval
                </div>
              </div>
            </div> */}
                </CardContent>
              </Card>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* View Evaluation Results */}
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <Button
            variant="open_mlflow_ui"
            size="lg"
            disabled={isPreloadedResultsLoading || !lowAccuracyResultsUrl}
            onClick={() =>
              lowAccuracyResultsUrl &&
              window.open(lowAccuracyResultsUrl, "_blank")
            }
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            View evals for low accuracy traces
          </Button>
          <Button
            variant="open_mlflow_ui"
            size="lg"
            disabled={isPreloadedResultsLoading || !regressionResultsUrl}
            onClick={() =>
              regressionResultsUrl &&
              window.open(regressionResultsUrl, "_blank")
            }
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            View evals for regression set
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Find & Fix Quality Issues"
      description="Systematic workflow for discovering problems, creating solutions, and deploying improvements safely"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
