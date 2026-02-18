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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/progress";
import {
  ExternalLink,
  Plus,
  Target,
  Award,
  Trash2,
  Loader2,
  CheckCircle2,
  Play,
} from "lucide-react";
import { useQueryPreloadedResults } from "@/queries/useQueryPreloadedResults";
import { useQueryExperiment } from "@/queries/useQueryTracing";
import { NotebookReference } from "@/components/notebook-reference";
import {
  builtinJudgesCode, customJudgesCode, customCodeMetricsCode,
  SAMPLE_EVAL_QUESTIONS, introContent, INITIAL_GUIDELINES,
} from "./eval-code-snippets";
import { MultiTurnEvaluation } from "./multi-turn-evaluation";


export function EvaluationBuilder() {
  const [builtinJudges, setBuiltinJudges] = React.useState([
    {
      name: "RelevanceToQuery",
      description: "Does the response directly address the user's input?",
      enabled: true,
    },
    {
      name: "Safety",
      description: "Does the response avoid harmful or toxic content?",
      enabled: true,
    },
    {
      name: "ToolCallCorrectness",
      description: "Are the tool calls and arguments correct for the user query?",
      enabled: true,
    },
    {
      name: "ToolCallEfficiency",
      description: "Are the tool calls efficient without redundancy?",
      enabled: true,
    },
    {
      name: "RetrievalGroundedness",
      description: "Is the response grounded in retrieved information?",
      enabled: false,
      disabled: true,
      disabledReason:
        "The DC Assistant uses Unity Catalog SQL functions (not a vector search index) to retrieve data. If this agent used a vector search index for retrieval, this judge would measure whether the response is grounded in the retrieved documents.",
    },
    {
      name: "RetrievalRelevance",
      description: "Are retrieved documents relevant to the user's request?",
      enabled: false,
      disabled: true,
      disabledReason:
        "The DC Assistant uses Unity Catalog SQL functions (not a vector search index) to retrieve data. If this agent used vector search, this judge would measure whether the retrieved documents are relevant to the query.",
    },
    {
      name: "Correctness",
      description: "Is the response correct compared to ground-truth answer?",
      enabled: false,
      disabled: true,
      disabledReason:
        "Requires a human-labeled ground truth dataset. If we had coaching staff label \"correct\" answers for common questions, this judge would compare the agent's response against those ground truths.",
    },
    {
      name: "RetrievalSufficiency",
      description:
        "Do the retrieved documents contain all necessary information in the ground truth answer?",
      disabledReason:
        "Requires both a vector search retrieval step and human-labeled ground truth answers, neither of which apply to this demo.",
      enabled: false,
      disabled: true,
    },
  ]);

  const [guidelines, setGuidelines] = React.useState(INITIAL_GUIDELINES);

  // Evaluation run state
  const [isEvalRunning, setIsEvalRunning] = React.useState(false);
  const [evalHasRun, setEvalHasRun] = React.useState(false);
  const [evalProgress, setEvalProgress] = React.useState(0);
  const [evalProgressMessage, setEvalProgressMessage] = React.useState("");
  const [evalError, setEvalError] = React.useState<string | null>(null);

  // Ref to hold the progress interval so we can clear it on completion
  const progressIntervalRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const PROGRESS_MESSAGES = [
    { threshold: 0, message: "Loading agent and scorers..." },
    { threshold: 10, message: "Running agent on evaluation questions..." },
    { threshold: 25, message: "Agent generating responses (this may take a few minutes)..." },
    { threshold: 45, message: "Scoring responses with built-in judges..." },
    { threshold: 65, message: "Scoring responses with custom Guidelines judges..." },
    { threshold: 80, message: "Aggregating results..." },
  ];

  const getProgressMessage = (pct: number) => {
    for (let i = PROGRESS_MESSAGES.length - 1; i >= 0; i--) {
      if (pct >= PROGRESS_MESSAGES[i].threshold) return PROGRESS_MESSAGES[i].message;
    }
    return PROGRESS_MESSAGES[0].message;
  };

  const runEvaluation = async () => {
    setIsEvalRunning(true);
    setEvalHasRun(false);
    setEvalProgress(0);
    setEvalProgressMessage("Loading agent and scorers...");
    setEvalError(null);

    // Simulate progress on the frontend while backend runs
    // Slowly fills to ~85%, then waits for the real "done" event
    progressIntervalRef.current = setInterval(() => {
      setEvalProgress((prev) => {
        if (prev >= 85) return prev; // Cap at 85% until backend confirms done
        const next = prev + 1;
        setEvalProgressMessage(getProgressMessage(next));
        return next;
      });
    }, 2000);

    const enabledBuiltin = builtinJudges
      .filter((j) => j.enabled && !j.disabled)
      .map((j) => j.name);
    const customGuidelines = guidelines
      .filter((g) => g.name.trim() !== "")
      .map((g) => ({ name: g.name, guideline: g.content }));

    try {
      const response = await fetch("/api/evaluation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          builtin_judges: enabledBuiltin,
          custom_guidelines: customGuidelines,
        }),
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("No response body");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "done") {
                if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
                setEvalProgress(100);
                setEvalProgressMessage("Evaluation complete!");
                setEvalHasRun(true);
                setIsEvalRunning(false);
              } else if (data.type === "error") {
                if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
                setEvalError(data.error);
                setIsEvalRunning(false);
              }
            } catch (e) {
              console.error("Failed to parse SSE:", e);
            }
          }
        }
      }
    } catch (err: any) {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setEvalError(err.message || "Evaluation failed");
      setIsEvalRunning(false);
    }
  };

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
  const { data: experimentData, isLoading: isExperimentLoading } =
    useQueryExperiment();

  // Build evaluation-runs URL from experiment data
  const evaluationRunsUrl = experimentData?.link
    ? experimentData.link.replace("?compareRunsMode=TRACES", "/evaluation-runs")
    : null;

  // Compute active scorers for the Run Evaluation button
  const activeBuiltinJudges = builtinJudges.filter(j => j.enabled && !j.disabled);
  const activeGuidelines = guidelines.filter(g => g.name.trim() !== "");
  const totalScorers = activeBuiltinJudges.length + activeGuidelines.length;

  const demoSection = (
    <div className="space-y-6">
      {/* Why Evals Matter - Data Engineering Parallel */}
      <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
        <CardContent className="pt-6 space-y-3 text-sm text-blue-900/90 dark:text-blue-100/90">
          <p className="font-semibold text-base text-blue-900 dark:text-blue-100">
            Why evaluation matters: the AI equivalent of unit tests and data quality checks
          </p>
          <p>
            <strong>For software engineers:</strong> LLM judges are the equivalent of <strong>unit tests</strong> for your AI agent. Just like you wouldn't ship code without tests that verify your functions return the right outputs for given inputs, you shouldn't ship an agent without judges that verify it produces quality responses for representative questions. Unit tests give you confidence that your code works correctly—LLM judges give you the same confidence for your agent's outputs.
          </p>
          <p>
            <strong>For data engineers:</strong> Think of LLM judges like <strong>data quality testing during pipeline runtime</strong>. Just as you run Great Expectations, dbt tests, or custom SQL assertions to ensure the data flowing through your pipelines is accurate and well-formed before downstream consumers use it, LLM judges validate that your agent's outputs meet quality standards before they reach end users. You wouldn't let a pipeline produce unchecked data for a dashboard—don't let an agent produce unchecked responses for your users.
          </p>
          <p>
            The key difference from both? Unit tests and data quality checks validate deterministic outputs—a number is either right or wrong. Agent outputs are non-deterministic—the same question can produce different phrasing each time. That's why you need <strong>LLM judges</strong> that can assess semantic quality, not just exact matches.
          </p>
        </CardContent>
      </Card>

      <MarkdownContent content="Before running LLM judges, you need a **representative set of evaluation questions** that cover the range of questions your agent will face in production. These should span different teams, situations, and analysis types. In MLflow, evaluation questions are stored as an **MLflow Dataset**—the standard object used to run evaluations against." />

      {/* Evaluation Dataset Preview */}
      <Card className="border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20">
        <CardHeader>
          <CardTitle className="text-green-900 dark:text-green-100 text-base">
            Evaluation Dataset (MLflow Dataset - {SAMPLE_EVAL_QUESTIONS.length} of 34 questions)
          </CardTitle>
          <p className="text-sm text-green-800/80 dark:text-green-200/80">
            For this demo, we've already created a dataset with 34 coaching questions. Here's a sample:
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {SAMPLE_EVAL_QUESTIONS.map((q, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-green-900 dark:text-green-100">
                <span className="text-green-600 dark:text-green-400 font-mono text-xs mt-0.5">{idx + 1}.</span>
                <span className="italic">&ldquo;{q}&rdquo;</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <MarkdownContent content="Now configure the judges that will score each question's response. Built-in judges handle safety and tool efficiency, while custom Guidelines judges evaluate football-specific quality." />

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
                        onChange={() => {
                          setBuiltinJudges(prev =>
                            prev.map((j, i) =>
                              i === index ? { ...j, enabled: !j.enabled } : j
                            )
                          );
                        }}
                        className="mt-1 cursor-pointer"
                      />
                      <div className="flex-1">
                        <Label
                          htmlFor={`judge-${index}`}
                          className="font-medium text-sm cursor-pointer"
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
              Curate your domain-specific judges
            </CardTitle>
            <div className="mt-3 space-y-3 text-sm text-muted-foreground">
              <p>
                Built-in judges handle universal quality dimensions (safety, relevance), but they don't know anything about <em>your</em> domain. A generic relevance judge can't tell you whether "11 personnel" is the right terminology or whether a defensive adjustment is strategically sound.
              </p>
              <p>
                <strong>Domain-specific judges encode subject matter expertise as evaluation criteria.</strong> Think of it like data quality rules in a warehouse: just as you'd write assertions that "revenue should never be negative" or "every order must have a customer_id", here you write rules like "personnel packages must use standard NFL notation" or "recommendations must cite specific data from the tool calls."
              </p>
              <p>
                The key advantage of Guidelines judges is that <strong>domain experts write them directly in natural language</strong>. A defensive coordinator doesn't need to write code—they describe what "good" looks like in their own words, and the LLM judge applies those rules at scale. This is the bridge between coaching expertise and automated evaluation.
              </p>
            </div>
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
                        onChange={(e) =>
                          updateGuideline(guideline.id, "name", e.target.value)
                        }
                        placeholder="e.g., Email Professionalism"
                        className="mt-1"
                      />
                    </div>
                    {guidelines.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeGuideline(guideline.id)}
                        className="text-red-500 hover:text-red-700 mt-6"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  <div>
                    <Label htmlFor={`guideline-content-${guideline.id}`}>
                      Guideline
                    </Label>
                    <Textarea
                      id={`guideline-content-${guideline.id}`}
                      value={guideline.content}
                      onChange={(e) =>
                        updateGuideline(guideline.id, "content", e.target.value)
                      }
                      rows={8}
                      className="mt-1 font-mono text-xs"
                      placeholder="Define your custom evaluation guidelines..."
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={addGuideline}>
                <Plus className="h-4 w-4 mr-1" />
                Add Guideline
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Run Evaluation Summary & Buttons */}
        <Card>
          <CardContent className="pt-6 space-y-4">
            <p className="text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
              Running evaluations live will take a few minutes. For demos, we recommend using the pre-run results below.
            </p>

            <div>
              <p className="font-semibold text-sm">
                {totalScorers} scorer{totalScorers !== 1 ? "s" : ""} selected: {activeBuiltinJudges.map(j => j.name).concat(activeGuidelines.map(g => g.name)).join(", ")}
              </p>
            </div>

            {/* Progress Bar */}
            {isEvalRunning && (
              <div className="space-y-2">
                <Progress value={evalProgress} className="w-full" />
                <p className="text-xs text-center text-muted-foreground">
                  {evalProgressMessage}
                </p>
              </div>
            )}

            {/* Completion state */}
            {evalHasRun && !isEvalRunning && (
              <div className="flex items-center gap-2 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded px-3 py-2">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-sm font-medium">Evaluation complete!</span>
              </div>
            )}

            {evalError && (
              <p className="text-sm text-red-600">{evalError}</p>
            )}

            <div className="flex gap-4">
              <Button
                variant="open_mlflow_ui"
                size="lg"
                onClick={() =>
                  evaluationRunsUrl &&
                  window.open(evaluationRunsUrl, "_blank")
                }
                disabled={isExperimentLoading || !evaluationRunsUrl}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                {evalHasRun ? "View Results" : "View Pre-run Results"}
              </Button>
              <Button
                size="lg"
                variant="outline"
                disabled={totalScorers === 0 || isEvalRunning || evalHasRun}
                onClick={runEvaluation}
              >
                {isEvalRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Running Evaluation...
                  </>
                ) : evalHasRun ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Evaluation Complete
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Evaluation Live ({totalScorers} scorers)
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

      </div>

      <MultiTurnEvaluation />

      {/* Bottom Callout - Judges need SME alignment */}
      <Card className="border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-900 dark:text-amber-100">
            <Award className="h-5 w-5" />
            LLM judges give us general signals - but are they aligned with your experts?
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-amber-900/90 dark:text-amber-100/90">
          <p>
            We now have both single-turn and session-level judges scoring our agent's outputs. These judges give us <strong>general signals of performance</strong>—relevance, safety, tool efficiency, conversation coherence—but there's a critical question we haven't answered yet:
          </p>
          <p>
            <strong>Do these automated scores actually match what your subject matter experts consider "good"?</strong> A judge might rate a response as highly relevant, but a defensive coordinator might disagree because it missed a key personnel package detail. A session might score well on completeness, but a coach might feel the defensive adjustments weren't actionable enough.
          </p>
          <p className="pt-2 font-medium">
            <strong>Next step:</strong> We'll collect feedback from SMEs (coaching staff) and compare their assessments against our judges' scores. This human validation will reveal where judges and experts disagree, so we can refine our evaluation criteria to truly reflect domain expertise.
          </p>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <StepLayout
      title="Evaluate DC recommendations using LLM judges"
      description="Scale coaching expertise with LLM judges for automated quality evaluation of defensive game analysis"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
