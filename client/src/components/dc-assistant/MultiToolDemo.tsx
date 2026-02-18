import React, { useState } from "react";
import { MarkdownContent } from "@/components/markdown-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Send, ExternalLink, CheckCircle2, ThumbsUp, ThumbsDown, Wrench } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

// Strip catalog.schema prefix from tool names for cleaner display
const formatToolName = (name: string) => {
  const parts = name.split("__");
  return parts.length > 2 ? parts.slice(2).join("__") : name;
};

// Multi-tool questions that require multiple Unity Catalog function calls
const MULTI_TOOL_QUESTIONS = [
  {
    id: "cowboys-3rd-down",
    question: "On 3rd-and-3 to 6, how often do the Cowboys pass vs run, and when they pass what formations/personnel do they use most?",
    team: "Dallas Cowboys",
    expectedTools: ["tendencies_by_down_distance", "who_got_ball_by_down_distance", "tendencies_by_offense_formation"]
  },
  {
    id: "seahawks-turnover",
    question: "After a turnover, what's the Seahawks most common first play (run vs pass, personnel, and which player usually gets the ball)?",
    team: "Seattle Seahawks",
    expectedTools: ["first_play_after_turnover", "who_got_ball_by_down_distance"]
  }
];

interface ToolCall {
  tool: string;
  arguments: Record<string, any>;
  status: "pending" | "success" | "error";
  result?: string;
}

export function MultiToolDemo() {
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [currentTraceId, setCurrentTraceId] = useState<string | null>(null);
  const [traceUrlTemplate, setTraceUrlTemplate] = useState<string>("");
  const [feedbackRating, setFeedbackRating] = useState<"up" | "down" | null>(null);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  // Fetch experiment info on mount
  React.useEffect(() => {
    fetch('/api/tracing_experiment')
      .then(res => res.json())
      .then(data => {
        setTraceUrlTemplate(data.trace_url_template);
      })
      .catch(err => console.error('Failed to fetch experiment info:', err));
  }, []);

  const selectedQuestionData = MULTI_TOOL_QUESTIONS.find(q => q.id === selectedQuestion);

  const handleAnalyze = async () => {
    if (!selectedQuestion) {
      setError("Please select a multi-tool question");
      return;
    }

    const questionData = MULTI_TOOL_QUESTIONS.find(q => q.id === selectedQuestion);
    if (!questionData) return;

    setLoading(true);
    setIsStreaming(true);
    setError(null);
    setStreamingContent("");
    setToolCalls([]);
    setCurrentTraceId(null);
    setFeedbackRating(null);
    setFeedbackComment("");
    setFeedbackSubmitted(false);

    const requestData = {
      question: questionData.question
    };

    try {
      const response = await fetch('/api/dc-assistant/analyze-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";

      if (!reader) {
        throw new Error("No response body");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "token") {
                accumulatedContent += data.content;
                setStreamingContent(accumulatedContent);
              } else if (data.type === "tool_call") {
                // Clear accumulated filler text when a new tool call arrives
                accumulatedContent = "";
                setStreamingContent("");
                const toolCall: ToolCall = {
                  tool: data.tool.name || data.tool.function_name || "Unknown",
                  arguments: data.tool.arguments ? JSON.parse(data.tool.arguments) : {},
                  status: "success"
                };
                setToolCalls(prev => [...prev, toolCall]);
              } else if (data.type === "done") {
                setCurrentTraceId(data.trace_id || null);
                console.log("Received trace_id:", data.trace_id);
                if (data.tool_calls && Array.isArray(data.tool_calls)) {
                  const calls = data.tool_calls.map((tc: any) => ({
                    tool: tc.name || tc.function_name || "Unknown",
                    arguments: tc.arguments ? JSON.parse(tc.arguments) : {},
                    status: "success" as const
                  }));
                  setToolCalls(calls);
                }
              } else if (data.type === "error") {
                setError(data.error);
                setToolCalls(prev => prev.map(tc => ({ ...tc, status: "error" as const })));
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Error analyzing:", err);
      setError(err.message || "Failed to analyze");
      setToolCalls(prev => prev.map(tc => ({ ...tc, status: "error" as const })));
    } finally {
      setLoading(false);
      setIsStreaming(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackRating || !currentTraceId) return;

    try {
      const response = await fetch("/api/dc-assistant/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          trace_id: currentTraceId,
          rating: feedbackRating,
          comment: feedbackComment || undefined,
          user_name: "Coach",
        }),
      });

      const result = await response.json();

      if (result.success) {
        setFeedbackSubmitted(true);
      } else {
        setError(result.message);
      }
    } catch (err) {
      console.error("Error submitting feedback:", err);
      setError("Failed to submit feedback");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Panel - Question Selection */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Multi-Tool Question</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="multi-tool-question">Select Question</Label>
              <Select value={selectedQuestion} onValueChange={setSelectedQuestion}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a multi-tool question..." />
                </SelectTrigger>
                <SelectContent>
                  {MULTI_TOOL_QUESTIONS.map((q) => (
                    <SelectItem key={q.id} value={q.id}>
                      {q.team} - {q.id === "cowboys-3rd-down" ? "3rd Down Analysis" : "Post-Turnover Tendencies"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Display selected question */}
            {selectedQuestionData && (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                  <Label className="text-xs text-blue-600 dark:text-blue-400 font-semibold mb-2 block">
                    Question to Agent
                  </Label>
                  <p className="text-sm text-blue-900 dark:text-blue-100 italic">
                    "{selectedQuestionData.question}"
                  </p>
                </div>

              </div>
            )}

            <Button
              onClick={handleAnalyze}
              disabled={loading || !selectedQuestion}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Asking DC Assistant...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Ask DC Assistant
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Right Panel - Generated Response */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Generated Response</CardTitle>
          </CardHeader>
          <CardContent>
            {toolCalls.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-muted-foreground mb-2">Tools used by DC Assistant:</p>
                <div className="flex flex-wrap gap-2">
                  {toolCalls.filter((call, idx, arr) => arr.findIndex(c => formatToolName(c.tool) === formatToolName(call.tool)) === idx).map((call, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-full">
                      <Wrench className="h-3 w-3 text-amber-600 dark:text-amber-400 flex-shrink-0" />
                      <code className="text-xs font-medium text-amber-800 dark:text-amber-200">
                        {formatToolName(call.tool)}
                      </code>
                      <CheckCircle2 className={`h-3 w-3 flex-shrink-0 ${
                        call.status === "success" ? "text-green-600" :
                        call.status === "error" ? "text-red-600" :
                        "text-amber-600 animate-pulse"
                      }`} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Loading state while generating */}
            {isStreaming && !streamingContent ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Response generating...</p>
              </div>
            ) : null}

            {/* Show streaming content */}
            {streamingContent ? (
              <div className="space-y-4">
                <MarkdownContent content={streamingContent} />

                {/* Feedback and Trace - show after streaming completes */}
                {!isStreaming && (
                  <>
                    {/* Feedback Section */}
                    <div className="border-t pt-6">
                      <h4 className="font-medium mb-4">How is this response?</h4>

                      {feedbackSubmitted ? (
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle2 className="h-5 w-5" />
                          <span className="font-medium">
                            Thank you for your feedback!
                          </span>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="flex gap-4">
                            <Button
                              variant={feedbackRating === "up" ? "default" : "outline"}
                              size="lg"
                              onClick={() => setFeedbackRating("up")}
                              className="flex-1"
                            >
                              <ThumbsUp className="mr-2 h-5 w-5" />
                              Good
                            </Button>
                            <Button
                              variant={feedbackRating === "down" ? "default" : "outline"}
                              size="lg"
                              onClick={() => setFeedbackRating("down")}
                              className="flex-1"
                            >
                              <ThumbsDown className="mr-2 h-5 w-5" />
                              Needs Improvement
                            </Button>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="multi-feedback-comment">
                              Additional Comments (Optional)
                            </Label>
                            <Textarea
                              id="multi-feedback-comment"
                              value={feedbackComment}
                              onChange={(e) => setFeedbackComment(e.target.value)}
                              placeholder="What could be improved? What did you like?"
                              rows={3}
                            />
                          </div>

                          <Button
                            onClick={handleFeedbackSubmit}
                            disabled={!feedbackRating || !currentTraceId}
                            className="w-full"
                          >
                            Submit Feedback
                          </Button>

                          {!currentTraceId && (
                            <p className="text-xs text-muted-foreground text-center">
                              Trace ID required for feedback submission
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Trace Section - only show if we have both template and trace ID */}
                    {traceUrlTemplate && currentTraceId && (
                      <div className="border-t pt-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium">
                            See multi-tool trace in MLflow UI
                          </h4>
                          <Button
                            variant="default"
                            size="lg"
                            onClick={() => {
                              const traceUrl = `${traceUrlTemplate}${currentTraceId}`;
                              window.open(traceUrl, '_blank');
                            }}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <ExternalLink className="h-4 w-4 mr-2" />
                            View Trace
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : null}

            {/* Initial empty state */}
            {!isStreaming && !streamingContent ? (
              <div className="text-center py-12 text-muted-foreground">
                <p>Select a multi-tool question and click Analyze</p>
                <p className="text-xs mt-2">Watch how the agent orchestrates multiple UC function calls to answer complex questions</p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
