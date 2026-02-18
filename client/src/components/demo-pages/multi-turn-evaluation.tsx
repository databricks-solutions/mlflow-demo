import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Target, ExternalLink, Loader2, CheckCircle2, Play } from "lucide-react";
import { useQueryExperiment } from "@/queries/useQueryTracing";

const SESSION_JUDGES = [
  {
    name: "ConversationCompleteness",
    description: "Does the agent address all user questions throughout the conversation?",
    enabled: true,
  },
  {
    name: "ConversationalRoleAdherence",
    description: "Does the assistant maintain its assigned role throughout the conversation?",
    enabled: true,
  },
  {
    name: "ConversationalSafety",
    description: "Are the assistant's responses safe and free of harmful content?",
    enabled: true,
  },
  {
    name: "ConversationalToolCallEfficiency",
    description: "Was tool usage across the conversation efficient and appropriate?",
    enabled: true,
  },
  {
    name: "KnowledgeRetention",
    description: "Does the assistant correctly retain information from earlier user inputs?",
    enabled: true,
  },
  {
    name: "UserFrustration",
    description: "Is the user frustrated? Was the frustration resolved?",
    enabled: true,
  },
];

export function MultiTurnEvaluation() {
  const [judges, setJudges] = React.useState(SESSION_JUDGES);
  const [isRunning, setIsRunning] = React.useState(false);
  const [hasRun, setHasRun] = React.useState(false);
  const [progress, setProgress] = React.useState(0);
  const [progressMessage, setProgressMessage] = React.useState("");
  const progressIntervalRef = React.useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: experimentData, isLoading: isExperimentLoading } = useQueryExperiment();
  const evaluationRunsUrl = experimentData?.link
    ? experimentData.link.replace("?compareRunsMode=TRACES", "/evaluation-runs")
    : null;

  const activeJudges = judges.filter(j => j.enabled);
  const totalScorers = activeJudges.length;

  const runSessionEvaluation = async () => {
    setIsRunning(true);
    setHasRun(false);
    setProgress(0);
    setProgressMessage("Loading session traces and scorers...");

    progressIntervalRef.current = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 85) return prev;
        const next = prev + 1;
        if (next >= 65) setProgressMessage("Scoring sessions with session-level judges...");
        else if (next >= 45) setProgressMessage("Evaluating multi-turn conversations...");
        else if (next >= 25) setProgressMessage("Running agent on session evaluation data...");
        else if (next >= 10) setProgressMessage("Loading session traces and scorers...");
        return next;
      });
    }, 2000);

    try {
      const response = await fetch("/api/evaluation/run-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_judges: activeJudges.map(j => j.name),
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
                setProgress(100);
                setProgressMessage("Session evaluation complete!");
                setHasRun(true);
                setIsRunning(false);
              } else if (data.type === "error") {
                if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
                setIsRunning(false);
              }
            } catch (e) {
              console.error("Failed to parse SSE:", e);
            }
          }
        }
      }
    } catch (err) {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Narrative Transition */}
      <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-950/20">
        <CardContent className="pt-6 space-y-3 text-sm text-purple-900/90 dark:text-purple-100/90">
          <p className="font-semibold text-base text-purple-900 dark:text-purple-100">
            Single responses are only half the story
          </p>
          <p>
            We've seen how MLflow can evaluate the accuracy of a single response—did the agent use the right tool? Was the answer relevant? That's critical, but for a conversational coaching assistant, it's only half the picture.
          </p>
          <p>
            A DC Assistant can give a series of technically correct answers but still provide a terrible coaching experience. Imagine a coordinator asking follow-up questions about the Cowboys' 3rd down tendencies, and the agent keeps re-fetching the same data, forgets what formation was just discussed, or gives disjointed analysis that doesn't build toward an actionable game plan. Every individual answer might be "correct," but the session as a whole fails.
          </p>
          <p>
            <strong>That's why MLflow provides session-level judges</strong> that evaluate the entire multi-turn conversation—not just individual responses. These judges measure what actually matters to the end user: Was the conversation coherent? Did the agent retain context? Was tool usage efficient across turns?
          </p>
        </CardContent>
      </Card>

      {/* Session-Level Built-in Judges */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Built-in session-level judges for multi-turn analysis across the entire conversation
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {judges.map((judge, index) => (
            <div key={index} className="flex items-start space-x-3">
              <input
                type="checkbox"
                id={`session-judge-${index}`}
                checked={judge.enabled}
                onChange={() => {
                  setJudges(prev =>
                    prev.map((j, i) =>
                      i === index ? { ...j, enabled: !j.enabled } : j
                    )
                  );
                }}
                className="mt-1 cursor-pointer"
              />
              <div className="flex-1">
                <Label
                  htmlFor={`session-judge-${index}`}
                  className="font-medium text-sm cursor-pointer"
                >
                  {judge.name}
                </Label>
                <p className="text-xs text-muted-foreground mt-1">
                  {judge.description}
                </p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Run Session Evaluation */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <p className="text-xs text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-2">
            Running session evaluations live will take a few minutes. For demos, we recommend using the pre-run results below.
          </p>

          <div>
            <p className="font-semibold text-sm">
              {totalScorers} session scorer{totalScorers !== 1 ? "s" : ""} selected: {activeJudges.map(j => j.name).join(", ")}
            </p>
          </div>

          {isRunning && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-xs text-center text-muted-foreground">
                {progressMessage}
              </p>
            </div>
          )}

          {hasRun && !isRunning && (
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded px-3 py-2">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-sm font-medium">Session evaluation complete!</span>
            </div>
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
              {hasRun ? "View Results" : "View Pre-run Results"}
            </Button>
            <Button
              size="lg"
              variant="outline"
              disabled={totalScorers === 0 || isRunning || hasRun}
              onClick={runSessionEvaluation}
            >
              {isRunning ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Running Session Evaluation...
                </>
              ) : hasRun ? (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Session Evaluation Complete
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Run Session Evaluation Live ({totalScorers} scorers)
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
