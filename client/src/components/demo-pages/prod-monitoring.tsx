import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { NotebookReference } from "@/components/notebook-reference";
import { Textarea } from "@/components/ui/textarea";
import {
  Activity,
  Sparkles,
  TrendingUp,
  CheckCircle2,
  Play,
  Loader2,
  Zap,
  Target,
} from "lucide-react";
import ReactDiffViewer from "react-diff-viewer";

const introContent = `
# Automatically Optimize Prompts with GEPA

You've built the infrastructure: aligned judges, labeled data from coaching staff, and calibrated quality metrics. Now comes the payoff: **automatically improving your prompts** to maximize those scores.

## The Problem

Manual prompt engineering is guesswork. Developers iterate blindly, prompts accumulate fragile ad-hoc rules, and there's no systematic way to know if a change actually helped. It doesn't scale.

## The Solution: GEPA (Generalized Preference Alignment)

GEPA is MLflow's prompt optimization algorithm. Give it your baseline prompt and your expert-aligned judges, and it automatically generates candidate prompts, tests them, and selects the highest scorer. No manual trial-and-error.

| Approach | Speed | Quality | Scalability | Expertise Required |
|----------|-------|---------|-------------|-------------------|
| **Manual Iteration** | Slow (days-weeks) | Unpredictable | Doesn't scale | High (domain + prompt engineering) |
| **GEPA Optimization** | Fast (hours) | Systematically improves | Scales via judges | Low (just define judges) |

The result: higher-quality, often more concise prompts — with a path to continuous improvement as you collect more labeled data.
`;

const baselinePrompt = `You are an expert NFL defensive coordinator assistant. Your role is to analyze play-by-play data and provide strategic defensive recommendations.

When answering questions:
- Query the available Unity Catalog tables for relevant play-by-play data
- Analyze offensive tendencies and patterns
- Provide actionable defensive adjustments
- Reference specific data points and percentages

Always ground your analysis in the actual data retrieved from tool calls.`;

const optimizedPrompt = `You are an expert NFL defensive coordinator assistant. Your role is to analyze play-by-play data and provide strategic defensive recommendations tailored to the coaching staff's needs.

## Query Analysis Framework

**CRITICAL: Identify the query type before answering**

1. **Sequence Questions** (keywords: "typical sequence", "play-by-play", "what do they call first/next", "script")
   - Provide an **ordered progression** of plays (Step 1, Step 2, Step 3 OR "1st play:..., 2nd play:...")
   - Include situational context (down, distance, clock, field position)
   - Describe specific play concepts in sequence order
   - Example: "Typical 2-minute drill: (1) Quick out to boundary WR, (2) Dig route to move chains, (3) Shot play to TE on seam"

2. **Tendency/Concept Questions** (keywords: "how do they use X", "what concepts", "tendencies")
   - Focus on schematic patterns and frequencies
   - Reference specific formations, personnel packages, route concepts
   - Provide actionable coaching takeaways and counters
   - No need for step-by-step sequences unless explicitly asked

3. **Scoped Queries** (keywords: "red zone only", "3rd down", "after turnover", "under 2 minutes")
   - **ONLY use data matching the requested scope**
   - If asked about "red zone", filter to plays inside the 20-yard line
   - If asked about "3rd down", analyze 3rd down plays only
   - State the scope in your answer: "In red zone situations specifically..."

## Data Analysis Requirements

- **Always query Unity Catalog tables** for play-by-play data before answering
- **Ground all claims in retrieved data** - cite percentages, frequencies, specific plays
- **No hallucination** - if data doesn't support a claim, don't make it
- Use standard NFL terminology:
  - Personnel: 11 (1 RB, 1 TE, 3 WR), 12 (1 RB, 2 TE, 2 WR), etc.
  - Coverage: Cover 2, Cover 3, Quarter-Quarter-Half, etc.
  - Down notation: "3rd and 6", "2nd and long"

## Strategic Recommendations

- Provide **specific defensive adjustments** (coverage calls, pressure schemes, personnel)
- Reference **key matchups** and player-specific insights
- Make recommendations **actionable** for game planning (not generic advice)

## Multi-Part Questions

If a question has multiple parts (e.g., "What concepts do they use AND who do they target?"):
- Address **all parts** explicitly
- Overall quality constrained by weakest sub-answer
- Don't skip parts—partial answers receive partial credit`;

const loadPromptCode = `import mlflow
from mlflow.genai.scorers import get_scorer

PROMPT_NAME = "dc_assistant_system_prompt"
baseline_prompt = mlflow.genai.load_prompt(
    f"prompts://{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}@production"
)
print(f"Loaded prompt v{baseline_prompt.version} ({len(baseline_prompt.get_text())} chars)")`;

const prepareOptimizationDataCode = `import mlflow
import pandas as pd

# Load labeled traces from SME review sessions
labeling_session = mlflow.genai.get_labeling_session("dc_quality_review_20250115")
labeled_traces = labeling_session.get_labeled_traces()

optimization_data = []
for trace in labeled_traces:
    labels = trace.get_labels()
    optimization_data.append({
        "question": trace.inputs["question"],
        "response": trace.outputs["response"],
        "expert_overall_quality": int(labels.get("overall_quality", {}).get("value", 3)),
        "expert_football_language": labels.get("football_language", {}).get("value") == "pass",
        "expert_data_grounded": labels.get("data_grounded", {}).get("value") == "pass",
    })

optimization_df = pd.DataFrame(optimization_data)
print(f"✅ Prepared {len(optimization_df)} labeled traces for optimization")`;

const runGepaOptimizationCode = `from mlflow.genai.optimizers import GepaPromptOptimizer
from mlflow.genai import optimize_prompts

aligned_judge = get_scorer(name="football_analysis_aligned")

def predict_fn(inputs):
    messages = [
        {"role": "system", "content": inputs["system_prompt"]},
        {"role": "user", "content": inputs["question"]}
    ]
    return {"response": dc_assistant_agent.predict(messages=messages)}

result = optimize_prompts(
    predict_fn=predict_fn,
    train_data=optimization_dataset,
    prompt_uris=[baseline_prompt.uri],
    optimizer=GepaPromptOptimizer(
        reflection_model="databricks-meta-llama-3-1-70b-instruct",
        max_metric_calls=75,
        num_candidates_per_iteration=5,
        convergence_threshold=0.02,
    ),
    scorers=[aligned_judge],
    experiment_name="dc_prompt_optimization"
)

best_prompt = result.best_prompt
print(f"✅ Baseline: {result.baseline_score:.3f} → Optimized: {result.best_score:.3f}")
print(f"   Improvement: {((result.best_score - result.baseline_score) / result.baseline_score * 100):.1f}%")`;

const registerOptimizedPromptCode = `import mlflow

# Register optimized prompt to Prompt Registry
new_version = mlflow.genai.save_prompt(
    prompt=best_prompt,
    name=f"{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}",
    tags={
        "optimization_method": "gepa",
        "baseline_score": str(baseline_score),
        "optimized_score": str(best_score),
    }
)
print(f"✅ Registered optimized prompt as version {new_version}")

# Promote to production if score exceeds threshold
PROMOTION_THRESHOLD = 0.75
if best_score >= PROMOTION_THRESHOLD:
    client = mlflow.tracking.MlflowClient()
    client.set_registered_model_alias(
        name=f"{UC_CATALOG}.{UC_SCHEMA}.{PROMPT_NAME}",
        alias="production",
        version=new_version
    )
    print(f"🚀 Promoted to production (score {best_score:.3f} >= {PROMOTION_THRESHOLD})")`;

export function MonitoringDemo() {
  const [isOptimizing, setIsOptimizing] = React.useState(false);
  const [hasOptimized, setHasOptimized] = React.useState(false);
  const [optimizationProgress, setOptimizationProgress] = React.useState(0);
  const [currentIteration, setCurrentIteration] = React.useState(0);
  const [viewMode, setViewMode] = React.useState<"side-by-side" | "diff">("side-by-side");

  const runOptimization = () => {
    setIsOptimizing(true);
    setHasOptimized(false);
    setOptimizationProgress(0);
    setCurrentIteration(0);

    // Simulate GEPA optimization progress
    let iteration = 0;
    const progressInterval = setInterval(() => {
      setOptimizationProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 5;
      });

      // Update iteration every 20%
      if (optimizationProgress % 20 === 0 && iteration < 5) {
        iteration += 1;
        setCurrentIteration(iteration);
      }
    }, 400);

    // Complete after ~8 seconds
    setTimeout(() => {
      clearInterval(progressInterval);
      setOptimizationProgress(100);
      setCurrentIteration(5);
      setIsOptimizing(false);
      setHasOptimized(true);
    }, 8000);
  };

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="1. Load baseline prompt"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/"
      >
        <CodeSnippet code={loadPromptCode} title="Load Production Prompt" />
      </CollapsibleSection>

      <CollapsibleSection
        title="2. Prepare optimization dataset"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/build-eval-dataset"
      >
        <CodeSnippet code={prepareOptimizationDataCode} title="Prepare Labeled Dataset" />
      </CollapsibleSection>

      <CollapsibleSection
        title="3. Run GEPA optimization"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/prompt-optimization/"
      >
        <CodeSnippet code={runGepaOptimizationCode} title="Run GEPA Optimization" />
      </CollapsibleSection>

      <CollapsibleSection
        title="4. Register and promote optimized prompt"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/"
      >
        <CodeSnippet code={registerOptimizedPromptCode} title="Register Optimized Prompt" />
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/5_optimize_prompts.ipynb"
        notebookName="5_optimize_prompts"
        description="Run GEPA optimization to automatically improve prompts using aligned judges"
      />
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      {/* Run GEPA Button */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Run GEPA Optimization
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Simulate the optimization: GEPA generates candidate prompts, scores each with your aligned judges, and selects the best performer.
          </p>

          <Button
            onClick={runOptimization}
            disabled={isOptimizing}
            size="lg"
            className="w-full"
          >
            {isOptimizing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running GEPA Optimization... (Iteration {currentIteration}/5)
              </>
            ) : hasOptimized ? (
              <>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Optimization Complete - Run Again
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run GEPA Optimization
              </>
            )}
          </Button>

          {isOptimizing && (
            <div className="space-y-2">
              <Progress value={optimizationProgress} className="w-full" />
              <p className="text-xs text-center text-muted-foreground flex items-center justify-center gap-2">
                <Activity className="h-3 w-3 animate-pulse" />
                {optimizationProgress < 30 && "Generating candidate prompts..."}
                {optimizationProgress >= 30 && optimizationProgress < 70 && "Testing candidates with aligned judges..."}
                {optimizationProgress >= 70 && optimizationProgress < 100 && "Refining top performers..."}
                {optimizationProgress === 100 && "Selecting best prompt!"}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Section */}
      {hasOptimized && (
        <>
          {/* Optimization Results Stats */}
          <Card className="border-green-200">
            <CardHeader>
              <CardTitle>Optimization Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 border rounded-lg bg-blue-50 dark:bg-blue-950/20">
                  <div className="text-2xl font-bold text-blue-600">67</div>
                  <div className="text-xs text-muted-foreground">Prompts Tested</div>
                </div>
                <div className="text-center p-4 border rounded-lg bg-green-50 dark:bg-green-950/20">
                  <div className="text-2xl font-bold text-green-600">+18%</div>
                  <div className="text-xs text-muted-foreground">Judge Score Improvement</div>
                </div>
                <div className="text-center p-4 border rounded-lg bg-purple-50 dark:bg-purple-950/20">
                  <div className="text-2xl font-bold text-purple-600">0.68 → 0.80</div>
                  <div className="text-xs text-muted-foreground">Baseline → Optimized</div>
                </div>
                <div className="text-center p-4 border rounded-lg bg-orange-50 dark:bg-orange-950/20">
                  <div className="text-2xl font-bold text-orange-600">5</div>
                  <div className="text-xs text-muted-foreground">Optimization Iterations</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* View Toggle */}
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Prompt Comparison</h3>
            <div className="flex gap-2">
              <Button variant={viewMode === "side-by-side" ? "default" : "outline"} size="sm" onClick={() => setViewMode("side-by-side")}>Side by Side</Button>
              <Button variant={viewMode === "diff" ? "default" : "outline"} size="sm" onClick={() => setViewMode("diff")}>Diff View</Button>
            </div>
          </div>

          {/* Prompt Comparison */}
          {viewMode === "side-by-side" ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Target className="h-4 w-4" /> Baseline <Badge variant="outline" className="ml-auto text-xs">{baselinePrompt.length} chars &middot; 0.68</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea value={baselinePrompt} rows={18} className="font-mono text-xs" readOnly />
                </CardContent>
              </Card>
              <Card className="border-green-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-sm text-green-600">
                    <TrendingUp className="h-4 w-4" /> GEPA-Optimized <Badge className="ml-auto bg-green-600 text-xs">{optimizedPrompt.length} chars &middot; 0.80</Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Textarea value={optimizedPrompt} rows={18} className="font-mono text-xs border-green-300" readOnly />
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Prompt Diff</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="border rounded-md overflow-hidden">
                  <ReactDiffViewer
                    oldValue={baselinePrompt}
                    newValue={optimizedPrompt}
                    splitView={false}
                    useDarkTheme={false}
                    hideLineNumbers={true}
                    showDiffOnly={false}
                    styles={{
                      contentText: { fontSize: "11px", fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, monospace' },
                    }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-2">Green = additions GEPA learned from coaching feedback.</p>
              </CardContent>
            </Card>
          )}

          {/* What GEPA Changed */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                What GEPA Learned from Coaching Feedback
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-950/20 rounded-r-lg">
                  <p className="font-semibold text-sm text-blue-900 dark:text-blue-100">Query Type Framework</p>
                  <p className="text-xs text-blue-800 dark:text-blue-200 mt-1">
                    Distinguishes sequence vs tendency vs scoped questions
                  </p>
                </div>
                <div className="p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-950/20 rounded-r-lg">
                  <p className="font-semibold text-sm text-green-900 dark:text-green-100">Scope Detection</p>
                  <p className="text-xs text-green-800 dark:text-green-200 mt-1">
                    Filters data to requested scope (red zone, 3rd down, etc.)
                  </p>
                </div>
                <div className="p-3 border-l-4 border-purple-500 bg-purple-50 dark:bg-purple-950/20 rounded-r-lg">
                  <p className="font-semibold text-sm text-purple-900 dark:text-purple-100">Multi-Part Handling</p>
                  <p className="text-xs text-purple-800 dark:text-purple-200 mt-1">
                    Addresses all parts; quality constrained by weakest sub-answer
                  </p>
                </div>
                <div className="p-3 border-l-4 border-orange-500 bg-orange-50 dark:bg-orange-950/20 rounded-r-lg">
                  <p className="font-semibold text-sm text-orange-900 dark:text-orange-100">Actionability</p>
                  <p className="text-xs text-orange-800 dark:text-orange-200 mt-1">
                    Specific defensive adjustments, not generic coaching platitudes
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Next Steps */}
          <Card className="border-blue-200 bg-blue-50/30 dark:border-blue-800 dark:bg-blue-950/20">
            <CardContent className="pt-6 text-sm text-blue-900/90 dark:text-blue-100/90">
              <p className="font-medium mb-2">Next: Register → A/B test → Promote to production → Re-run GEPA as more coach feedback arrives.</p>
              <p className="text-xs text-muted-foreground">
                Expert feedback → aligned judges → optimized prompts → better outputs → more feedback. The loop is self-improving.
              </p>
            </CardContent>
          </Card>
        </>
      )}

    </div>
  );

  return (
    <StepLayout
      title="Optimize Prompts with GEPA"
      description="Automatically improve prompts using Generalized Preference Alignment guided by coaching-aligned judges"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
