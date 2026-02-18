import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ExternalLink,
  BarChart3,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Play,
  Loader2,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { NotebookReference } from "@/components/notebook-reference";
import ReactDiffViewer from "react-diff-viewer";

const introContent = `
# Align Judges to Coaching Expertise

You've created baseline judges and collected expert labels — but your judges and your coaches likely disagree. A generic judge might score an analysis 5/5 because it "sounds good," while a coach gives it 2/5 because it discussed tendencies when they asked for a play sequence.

**Judge alignment automatically calibrates your judges to match expert preferences.** The optimizer analyzes disagreements between human labels and judge scores, then refines judge instructions to encode domain-specific expertise. The result: scalable quality assessment that reflects coaching judgment, not generic LLM preferences.

MLflow provides two alignment algorithms — **SIMBA** (iterative instruction editing) and **MemAlign** (dual-memory learning, recommended for MLflow 3.9+). Both take labeled traces from the previous step and produce aligned judges that better match expert judgment.
`;

const originalInstructions = `Evaluate if the response in {{ outputs }} appropriately analyzes the available data and provides an actionable recommendation the question in {{ inputs }}. The response should be accurate, contextually relevant, and give a strategic advantage to the  person making the request. Your grading criteria should be:  1: Completely unacceptable. Incorrect data interpretation or no recommendations 2: Mostly unacceptable. Irrelevant or spurious feedback or weak recommendations provided with minimal strategic advantage 3: Somewhat acceptable. Relevant feedback provided with some strategic advantage 4: Mostly acceptable. Relevant feedback provided with strong strategic advantage 5 Completely acceptable. Relevant feedback provided with excellent strategic advantage`;

const alignedInstructions = `Evaluate if the response in {{ outputs }} appropriately analyzes the available data and provides an actionable recommendation the question in {{ inputs }}. The response should be accurate, contextually relevant, and give a strategic advantage to the  person making the request. Your grading criteria should be:  1: Completely unacceptable. Incorrect data interpretation or no recommendations 2: Mostly unacceptable. Irrelevant or spurious feedback or weak recommendations provided with minimal strategic advantage 3: Somewhat acceptable. Relevant feedback provided with some strategic advantage 4: Mostly acceptable. Relevant feedback provided with strong strategic advantage 5 Completely acceptable. Relevant feedback provided with excellent strategic advantage

If the input question asks for a **"typical play sequence"** (keywords: "sequence", "play-by-play", "what do they call first/next", "script", "with under X minutes"), then you should **check that the output contains an explicit ordered series of actions** (e.g., Step 1/2/3; "1st play: … 2nd play: …"; or a plausible sample drive with down/distance/clock). If the output is mostly **tendencies, rates, formations, or defensive tips** without an ordered progression, you should cap the rating around **3 (somewhat acceptable)** even if the football analysis is otherwise strong.

If the output includes numbers/statistics (pass rate, EPA, air yards) but does not explain **how those translate into an actual sequence** (e.g., "open with quick game to boundary, then spike/check, then shot play"), treat it as **partial credit**: relevant but not answering the "sequence" framing.

When grading, explicitly map the user's ask to required elements:
- For "typical sequence": require (a) ordering, (b) situational context (clock/TOs/field position or down & distance), and (c) representative play types/concepts in that order.
- If missing (a), do not award 4–5.
- Reserve 5 only when the response both answers the sequence request and provides actionable recommendations aligned to that sequence.

If the input question is NOT asking for a "typical play sequence" (i.e., it asks "How do they use X vs Y?", "what concepts/tendencies?", "how do they attack coverage?"), then you should NOT penalize primarily for missing an ordered step-by-step sequence; instead grade on whether the output provides (a) concrete schematic explanation (formations/personnel, route concepts, protection/action, intended leverage vs man), (b) actionable coaching takeaways/counters, and (c) at least a few specific examples (even if qualitative) such as common concept families (e.g., boot/flood, crossers, dagger, glance/RPO-like looks) and who they target.

If the output is only clarifying questions or meta-discussion with zero analysis/recommendations, then assign a 1 and explicitly say: it failed to answer the question at all; clarifications can be asked but must come after giving an initial best-effort analysis.

If the output gives some correct high-level ideas but is vague (no concrete concepts/usage details, no actionable adjustments), cap at 2–3. Reserve 4–5 for responses that translate play-action vs man into coach-usable guidance (what the offense is trying to create vs man, what defenders should key, what coverages/techniques to call, and situational tendencies).

Always format \`result\` as an integer (1–5) matching the module schema; do not include extra text like "1: Completely unacceptable…" inside the numeric field.`;

const simbaAlignmentCode = `import mlflow
from mlflow.genai.scorers import get_scorer
from mlflow.genai.judges.optimizers import SIMBAAlignmentOptimizer

# Load baseline judge created in evaluation step
football_analysis_judge = get_scorer(name="football_analysis_base")

# Load traces with both human labels and judge scores
traces_for_alignment = mlflow.search_traces(
    experiment_ids=[EXPERIMENT_ID],
    filter_string="tag.eval = 'complete'",
    max_results=50
)

# Filter to traces that have BOTH human feedback AND judge scores
valid_traces = []
for trace in traces_for_alignment:
    feedbacks = trace.search_assessments(name="football_analysis_base")
    has_judge = any(f.source.source_type == "LLM_JUDGE" for f in feedbacks)
    has_human = any(f.source.source_type == "HUMAN" for f in feedbacks)
    if has_judge and has_human:
        valid_traces.append(trace)

print(f"Using {len(valid_traces)} labeled traces for alignment")

# Run SIMBA alignment
aligned_judge = football_analysis_judge.align(
    traces=valid_traces,
    optimizer=SIMBAAlignmentOptimizer(model=REFLECTION_MODEL)
)

print("Original instructions:", football_analysis_judge.instructions)
print("\\nAligned instructions:", aligned_judge.instructions)`;

const memalignAlignmentCode = `import mlflow
from mlflow.genai.scorers import get_scorer
from mlflow.genai.judges.optimizers import MemAlignOptimizer

# Load baseline judge
football_analysis_judge = get_scorer(name="football_analysis_base")

# Load labeled traces (same as SIMBA)
valid_traces = mlflow.search_traces(...)  # Same filtering logic

# Run MemAlign optimization (MLflow 3.9+ default)
aligned_judge = football_analysis_judge.align(
    traces=valid_traces,
    optimizer=MemAlignOptimizer(
        reflection_lm="databricks:/databricks-gpt-5-2",
        embedding_model="databricks:/databricks-qwen3-embedding-0-6b"
    )
)

print("Original instructions:", football_analysis_judge.instructions)
print("\\nAligned instructions:", aligned_judge.instructions)

# MemAlign produces distilled guidelines in addition to refined instructions
print("\\nDistilled Guidelines:", aligned_judge.distilled_guidelines)`;

const registerAlignedJudgeCode = `import mlflow
from mlflow.genai.judges import make_judge

# Register aligned judge for use in evaluations
aligned_judge_registered = make_judge(
    name="football_analysis_aligned",
    instructions=aligned_judge.instructions,
    feedback_value_type=float,
)

aligned_judge_registered.register(experiment_id=EXPERIMENT_ID)

print(f"Registered aligned judge: {aligned_judge_registered.name}")

# Now use the aligned judge in evaluations
from mlflow.genai import evaluate

results = evaluate(
    data=eval_dataset,
    predict_fn=dc_assistant_predict,
    scorers=[aligned_judge_registered]  # Uses expert-calibrated judge
)`;

export function JudgeAlignment() {
  const [selectedOptimizer, setSelectedOptimizer] = React.useState<"simba" | "memalign">("memalign");
  const [viewMode, setViewMode] = React.useState<"side-by-side" | "diff">("side-by-side");
  const [isRunning, setIsRunning] = React.useState(false);
  const [hasRun, setHasRun] = React.useState(false);
  const [optimizationProgress, setOptimizationProgress] = React.useState(0);

  const runOptimization = () => {
    setIsRunning(true);
    setHasRun(false);
    setOptimizationProgress(0);

    // Simulate optimization progress
    const progressInterval = setInterval(() => {
      setOptimizationProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 10;
      });
    }, 300);

    // Simulate completion after 3 seconds
    setTimeout(() => {
      clearInterval(progressInterval);
      setOptimizationProgress(100);
      setIsRunning(false);
      setHasRun(true);
    }, 3000);
  };

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="Step 1: Load labeled traces and baseline judge"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/judge-alignment/"
      >
        <div className="space-y-4">
          <MarkdownContent content="Judge alignment requires traces with both human labels (from labeling sessions) and judge scores (from evaluation runs). The optimizer analyzes disagreements to refine judge instructions." />
          <CodeSnippet
            code={selectedOptimizer === "simba" ? simbaAlignmentCode : memalignAlignmentCode}
            title={`${selectedOptimizer === "simba" ? "SIMBA" : "MemAlign"} Alignment`}
            filename="align_judge.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Step 2: Register and use aligned judge"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/scorers/register-scorer"
      >
        <div className="space-y-4">
          <MarkdownContent content="After alignment, register the improved judge for use in future evaluations and prompt optimization. The aligned judge now reflects coaching expertise at scale." />
          <CodeSnippet
            code={registerAlignedJudgeCode}
            title="Register Aligned Judge"
            filename="register_judge.py"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/4_align_judges_to_experts.ipynb"
        notebookName="4_align_judges_to_experts"
        description="Align judges to coaching expertise using SIMBA or MemAlign optimizers"
      />
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="See how judge alignment learns domain-specific coaching expertise from labeled data. The comparison below shows what the judge learned from analyzing disagreements between coach labels and baseline judge scores." />

      {/* How SIMBA and MemAlign Work - Visual Comparison */}
      <Card className="border-2 border-blue-200 bg-blue-50/30 dark:border-blue-800 dark:bg-blue-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
            <Sparkles className="h-5 w-5" />
            How Judge Alignment Works: SIMBA vs MemAlign
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* SIMBA Explanation */}
            <div className="border rounded-lg p-4 bg-white dark:bg-gray-900">
              <div className="flex items-center gap-2 mb-3">
                <Badge variant="outline" className="text-xs">MLflow 3.8 default</Badge>
                <h3 className="font-semibold text-lg">SIMBA</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Stochastic Introspective Mini-Batch Ascent
              </p>

              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-semibold text-blue-700 dark:text-blue-300">
                    1
                  </div>
                  <div>
                    <p className="text-sm font-medium">Find Disagreements</p>
                    <p className="text-xs text-muted-foreground">
                      Identify traces where judge score ≠ coach label
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-semibold text-blue-700 dark:text-blue-300">
                    2
                  </div>
                  <div>
                    <p className="text-sm font-medium">Analyze Failures</p>
                    <p className="text-xs text-muted-foreground">
                      Reflection LLM examines why the judge was wrong
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-semibold text-blue-700 dark:text-blue-300">
                    3
                  </div>
                  <div>
                    <p className="text-sm font-medium">Propose Edits</p>
                    <p className="text-xs text-muted-foreground">
                      Generate specific instruction refinements
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-semibold text-blue-700 dark:text-blue-300">
                    4
                  </div>
                  <div>
                    <p className="text-sm font-medium">Iterate</p>
                    <p className="text-xs text-muted-foreground">
                      Repeat until alignment improves (multiple iterations)
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <p className="text-xs font-semibold mb-1">Example Learning:</p>
                <p className="text-xs text-muted-foreground italic">
                  "Coach rated this 2/5 but judge gave 5/5. Analyzing... The response discusses general tendencies when the question asked for a specific play sequence. Add rule: 'sequence questions require ordered steps.'"
                </p>
              </div>
            </div>

            {/* MemAlign Explanation */}
            <div className="border-2 border-green-500 rounded-lg p-4 bg-white dark:bg-gray-900">
              <div className="flex items-center gap-2 mb-3">
                <Badge className="bg-green-600 text-xs">MLflow 3.9+ default</Badge>
                <h3 className="font-semibold text-lg">MemAlign</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Dual-Memory Framework (Recommended)
              </p>

              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-sm font-semibold text-green-700 dark:text-green-300">
                    1
                  </div>
                  <div>
                    <p className="text-sm font-medium">Build Semantic Memory</p>
                    <p className="text-xs text-muted-foreground">
                      Extract general rules from labeled data
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-sm font-semibold text-green-700 dark:text-green-300">
                    2
                  </div>
                  <div>
                    <p className="text-sm font-medium">Build Episodic Memory</p>
                    <p className="text-xs text-muted-foreground">
                      Store specific examples as reference cases
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-sm font-semibold text-green-700 dark:text-green-300">
                    3
                  </div>
                  <div>
                    <p className="text-sm font-medium">Apply Both</p>
                    <p className="text-xs text-muted-foreground">
                      Use principles + examples to judge new traces
                    </p>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-sm font-semibold text-green-700 dark:text-green-300">
                    ✓
                  </div>
                  <div>
                    <p className="text-sm font-medium">Fast & Efficient</p>
                    <p className="text-xs text-muted-foreground">
                      Single pass - no iterative refinement needed
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
                <p className="text-xs font-semibold mb-1 text-green-900 dark:text-green-100">Example Learning:</p>
                <p className="text-xs text-green-800 dark:text-green-200 italic">
                  Semantic: "Sequence questions need ordered steps"<br/>
                  Episodic: "Remember trace #42 - coach gave 2/5 because answer lacked play-by-play progression"
                </p>
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 dark:bg-gray-800">
                <tr>
                  <th className="text-left p-3 font-semibold">Characteristic</th>
                  <th className="text-left p-3 font-semibold">SIMBA</th>
                  <th className="text-left p-3 font-semibold">MemAlign</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="p-3 font-medium">Speed</td>
                  <td className="p-3 text-muted-foreground">Multiple iterations (slower)</td>
                  <td className="p-3 text-green-700 dark:text-green-400 font-medium">Single pass (100x faster)</td>
                </tr>
                <tr>
                  <td className="p-3 font-medium">Cost</td>
                  <td className="p-3 text-muted-foreground">More LLM calls</td>
                  <td className="p-3 text-green-700 dark:text-green-400 font-medium">10x cheaper</td>
                </tr>
                <tr>
                  <td className="p-3 font-medium">Min Examples</td>
                  <td className="p-3 text-muted-foreground">~20-30 labeled traces</td>
                  <td className="p-3 text-green-700 dark:text-green-400 font-medium">2-10 labeled traces</td>
                </tr>
                <tr>
                  <td className="p-3 font-medium">Approach</td>
                  <td className="p-3 text-muted-foreground">Iterative instruction editing</td>
                  <td className="p-3 text-muted-foreground">Dual-memory learning</td>
                </tr>
                <tr>
                  <td className="p-3 font-medium">Output</td>
                  <td className="p-3 text-muted-foreground">Refined instructions</td>
                  <td className="p-3 text-muted-foreground">Instructions + distilled guidelines</td>
                </tr>
                <tr>
                  <td className="p-3 font-medium">When to Use</td>
                  <td className="p-3 text-muted-foreground">MLflow 3.8 or below</td>
                  <td className="p-3 text-green-700 dark:text-green-400 font-medium">MLflow 3.9+ (recommended)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Concrete Example of What Each Produces */}
      <Card className="border-purple-200 bg-purple-50/30 dark:border-purple-800 dark:bg-purple-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-purple-900 dark:text-purple-100">
            <CheckCircle2 className="h-5 w-5" />
            What Each Optimizer Learns from the Same Disagreement
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <p className="text-xs font-semibold mb-2">Example Scenario:</p>
            <p className="text-xs text-muted-foreground mb-2">
              <strong>Question:</strong> "What's the typical 2-minute drill sequence for the 49ers?"
            </p>
            <p className="text-xs text-muted-foreground mb-2">
              <strong>Agent Response:</strong> Discusses general passing tendencies, formations, and targets but doesn't provide an ordered play-by-play sequence
            </p>
            <p className="text-xs mb-1">
              <strong>Baseline Judge Score:</strong> <Badge variant="outline">5/5</Badge> (thought tendencies = good answer)
            </p>
            <p className="text-xs">
              <strong>Coach Label:</strong> <Badge variant="destructive">2/5</Badge> (wanted actual play sequence, not tendencies)
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="border rounded-lg p-4 bg-white dark:bg-gray-900">
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Badge variant="outline">SIMBA</Badge>
                Learns Through Iterative Editing
              </h4>
              <div className="space-y-2 text-xs">
                <p className="font-medium text-green-700 dark:text-green-400">Adds to instructions:</p>
                <div className="p-2 bg-green-50 dark:bg-green-950/30 rounded border border-green-200 dark:border-green-800">
                  <p className="italic">
                    "If the input question asks for a 'typical play sequence' (keywords: 'sequence', 'play-by-play', 'what do they call first/next'), then check that the output contains an explicit ordered series of actions (e.g., Step 1/2/3; '1st play: ... 2nd play: ...')."
                  </p>
                </div>
                <p className="text-muted-foreground mt-2">
                  Result: Refines instructions through multiple iterations
                </p>
              </div>
            </div>

            <div className="border-2 border-green-500 rounded-lg p-4 bg-white dark:bg-gray-900">
              <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
                <Badge className="bg-green-600">MemAlign</Badge>
                Learns Through Dual Memory
              </h4>
              <div className="space-y-2 text-xs">
                <p className="font-medium text-green-700 dark:text-green-400">Semantic Memory (general rule):</p>
                <div className="p-2 bg-green-50 dark:bg-green-950/30 rounded border border-green-200 dark:border-green-800 mb-2">
                  <p className="italic">
                    "Sequence questions require ordered progression with play-by-play details"
                  </p>
                </div>
                <p className="font-medium text-blue-700 dark:text-blue-400">Episodic Memory (specific example):</p>
                <div className="p-2 bg-blue-50 dark:bg-blue-950/30 rounded border border-blue-200 dark:border-blue-800">
                  <p className="italic">
                    "Trace #tr-2a91cd: Coach wanted sequence but got tendencies → gave 2/5"
                  </p>
                </div>
                <p className="text-muted-foreground mt-2">
                  Result: Applies both principle + example to future evaluations
                </p>
              </div>
            </div>
          </div>

          <div className="p-3 bg-green-50 dark:bg-green-950/30 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-xs font-semibold text-green-900 dark:text-green-100 mb-1">
              Outcome: Both produce aligned judges, but MemAlign is faster and needs fewer examples
            </p>
            <p className="text-xs text-green-800 dark:text-green-200">
              For most use cases with MLflow 3.9+, MemAlign is the recommended approach. It learns just as well but at a fraction of the cost and latency.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Optimizer Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Select Optimizer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="optimizer">Optimization Algorithm</Label>
              <Select
                value={selectedOptimizer}
                onValueChange={(value: "simba" | "memalign") => {
                  setSelectedOptimizer(value);
                  setHasRun(false); // Reset results when changing optimizer
                }}
              >
                <SelectTrigger id="optimizer" className="mt-2">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="simba">
                    <div className="flex items-center gap-2">
                      <span>SIMBA</span>
                      <Badge variant="outline" className="text-xs">MLflow 3.8 default</Badge>
                    </div>
                  </SelectItem>
                  <SelectItem value="memalign">
                    <div className="flex items-center gap-2">
                      <span>MemAlign</span>
                      <Badge variant="default" className="text-xs">MLflow 3.9+ default</Badge>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="p-4 bg-muted/30 rounded-lg border text-sm space-y-2">
              {selectedOptimizer === "simba" ? (
                <>
                  <p className="font-semibold mb-2">SIMBA (DSPy-based)</p>
                  <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                    <li>Iteratively refines instructions by analyzing failures</li>
                    <li>Requires ~20-30 labeled traces</li>
                    <li>Multiple LLM calls for reflection and editing</li>
                    <li><strong>Best for:</strong> MLflow 3.8 or below</li>
                  </ul>
                </>
              ) : (
                <>
                  <p className="font-semibold mb-2">MemAlign (Dual-Memory Framework) ⭐ Recommended</p>
                  <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                    <li>Fast single-pass learning with semantic + episodic memory</li>
                    <li>Works with as few as 2-10 labeled traces</li>
                    <li>100x faster, 10x cheaper than SIMBA</li>
                    <li><strong>Best for:</strong> MLflow 3.9+ and most use cases</li>
                  </ul>
                </>
              )}
            </div>

            {/* Run Optimizer Button */}
            <div className="pt-4">
              <Button
                onClick={runOptimization}
                disabled={isRunning}
                size="lg"
                className="w-full"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Running {selectedOptimizer === "simba" ? "SIMBA" : "MemAlign"} Optimizer...
                  </>
                ) : hasRun ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Optimization Complete - Run Again
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run {selectedOptimizer === "simba" ? "SIMBA" : "MemAlign"} Alignment
                  </>
                )}
              </Button>

              {/* Progress Bar */}
              {isRunning && (
                <div className="mt-4 space-y-2">
                  <Progress value={optimizationProgress} className="w-full" />
                  <p className="text-xs text-center text-muted-foreground">
                    {optimizationProgress < 30 && "Loading labeled traces with coach feedback..."}
                    {optimizationProgress >= 30 && optimizationProgress < 60 && selectedOptimizer === "simba" && "Analyzing disagreements and proposing edits..."}
                    {optimizationProgress >= 30 && optimizationProgress < 60 && selectedOptimizer === "memalign" && "Building semantic and episodic memories..."}
                    {optimizationProgress >= 60 && optimizationProgress < 100 && "Refining judge instructions..."}
                    {optimizationProgress === 100 && "Alignment complete!"}
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Section - Only show after running */}
      {hasRun && (
        <>
          {/* Success Message */}
          <Card className="border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-green-900 dark:text-green-100">
                    {selectedOptimizer === "simba" ? "SIMBA" : "MemAlign"} Optimization Complete
                  </p>
                  <p className="text-sm text-green-800 dark:text-green-200 mt-1">
                    The judge has been aligned to coaching expertise. Review the refined instructions below to see what domain-specific rules were learned.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* View Mode Toggle */}
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Aligned Judge Instructions</h3>
            <div className="flex gap-2">
              <Button
                variant={viewMode === "side-by-side" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("side-by-side")}
              >
                Side by Side
              </Button>
              <Button
                variant={viewMode === "diff" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("diff")}
              >
                Diff View
              </Button>
            </div>
          </div>

      {viewMode === "side-by-side" ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Original Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-muted-foreground">
                <AlertCircle className="h-5 w-5" />
                Original Judge Instructions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Badge variant="outline">Baseline (Generic)</Badge>
                <Textarea
                  value={originalInstructions}
                  rows={20}
                  className="font-mono text-xs"
                  readOnly
                />
                <p className="text-xs text-muted-foreground">
                  Generic instructions that miss domain-specific nuance
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Aligned Instructions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" />
                Aligned Judge Instructions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Badge className="bg-green-600">Expert-Calibrated</Badge>
                <Textarea
                  value={alignedInstructions}
                  rows={20}
                  className="font-mono text-xs"
                  readOnly
                />
                <p className="text-xs text-green-700 font-medium">
                  Added 9 paragraphs of coaching-specific evaluation criteria
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Instruction Diff: What the Judge Learned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-md overflow-hidden">
              <ReactDiffViewer
                oldValue={originalInstructions}
                newValue={alignedInstructions}
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
                    fontSize: "11px",
                    fontFamily:
                      'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
                  },
                }}
              />
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              <strong>Green highlights</strong> show what the optimizer learned from coach feedback. The aligned judge now understands sequence vs tendency questions, scoped queries, multi-part analysis, and when to penalize vague recommendations.
            </p>
          </CardContent>
        </Card>
      )}

      {/* What the Judge Learned */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Key Learned Rules (Extracted from Aligned Instructions)
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-2">
            These rules were automatically added by the alignment process by analyzing disagreements between coach labels and baseline judge scores. They represent the domain-specific coaching expertise the judge learned.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-4 border-l-4 border-green-500 bg-green-50 rounded-r-lg">
              <p className="font-semibold text-green-900">Sequence vs Tendency Questions</p>
              <p className="text-sm text-green-800 mt-1">
                Learned to distinguish "typical play sequence" requests from "tendency" questions. Requires ordered progression (Step 1/2/3) for sequence questions, but doesn't penalize missing sequences when analyzing tendencies.
              </p>
            </div>

            <div className="p-4 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg">
              <p className="font-semibold text-blue-900">Scoped Query Detection</p>
              <p className="text-sm text-blue-800 mt-1">
                Learned to check if responses match requested scope (e.g., "red zone only", "3rd down", "after turnovers"). Caps score at 3-4 when response uses all-field data for scoped questions.
              </p>
            </div>

            <div className="p-4 border-l-4 border-purple-500 bg-purple-50 rounded-r-lg">
              <p className="font-semibold text-purple-900">Multi-Part Question Handling</p>
              <p className="text-sm text-purple-800 mt-1">
                Learned that overall score should be constrained by the weakest sub-answer. If part A is well-answered but part B is incomplete, doesn't award perfect score.
              </p>
            </div>

            <div className="p-4 border-l-4 border-orange-500 bg-orange-50 rounded-r-lg">
              <p className="font-semibold text-orange-900">Actionability Over Vagueness</p>
              <p className="text-sm text-orange-800 mt-1">
                Learned to reserve 4-5 scores for responses with concrete coaching guidance (specific coverages, techniques, matchups) rather than generic or vague recommendations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alignment Impact */}
      <Card>
        <CardHeader>
          <CardTitle>Alignment Impact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border rounded-lg bg-green-50">
              <div className="text-3xl font-bold text-green-600">31</div>
              <div className="text-sm text-muted-foreground">Labeled Traces Used</div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-blue-50">
              <div className="text-3xl font-bold text-blue-600">+9</div>
              <div className="text-sm text-muted-foreground">Paragraphs Added</div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-purple-50">
              <div className="text-3xl font-bold text-purple-600">4</div>
              <div className="text-sm text-muted-foreground">Major Criteria Learned</div>
            </div>
          </div>
        </CardContent>
      </Card>
        </>
      )}

      {/* Call to Action when not run */}
      {!hasRun && !isRunning && (
        <Card className="border-blue-200 bg-blue-50/30 dark:border-blue-800 dark:bg-blue-950/20">
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground mb-2">
              Click "Run {selectedOptimizer === "simba" ? "SIMBA" : "MemAlign"} Alignment" above to see how the optimizer learns from coach feedback
            </p>
            <p className="text-xs text-muted-foreground">
              The demo will simulate the alignment process and show you the refined judge instructions
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );

  return (
    <StepLayout
      title="Align Judges to Expert Feedback"
      description="Calibrate judges to match coaching expertise using SIMBA or MemAlign optimizers"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
