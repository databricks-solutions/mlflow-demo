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

// NFL Teams
const NFL_TEAMS = [
  "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
  "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
  "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
  "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
  "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
  "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
  "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
  "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
];

// Analysis types - each maps to a single UC function tool call
const ANALYSIS_TYPES = [
  {
    id: "down-distance",
    label: "Down & Distance Tendencies",
    tool: "tendencies_by_down_distance",
    parameters: ["distance"],
    options: { distance: ["short", "medium", "long"] }
  },
  {
    id: "post-turnover",
    label: "Post-Turnover Offense",
    tool: "first_play_after_turnover",
    parameters: [],
    options: {}
  },
  {
    id: "end-of-halves",
    label: "End of Halves",
    tool: "tendencies_two_minute_drill",
    parameters: [],
    options: {}
  },
];

interface ToolCall {
  tool: string;
  arguments: Record<string, any>;
  status: "pending" | "success" | "error";
  result?: string;
}

interface DcTracingDemoProps {
  onTraceGenerated?: (traceId: string) => void;
}

const QUICK_SELECT_QUESTIONS = [
  {
    id: "panthers-2nd-short",
    label: "Panthers 2nd & Short",
    question: "How do the 2024 Carolina Panthers run vs. pass on 2nd and short?",
  },
  {
    id: "chargers-turnover",
    label: "Chargers Post-Turnover",
    question: "How do the 2023 Chargers handle offense after a turnover?",
  },
];

export function DcTracingDemo({ onTraceGenerated }: DcTracingDemoProps = {}) {
  const [quickSelect, setQuickSelect] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedSeasons, setSelectedSeasons] = useState<string[]>(["2024"]);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState("");
  const [parameters, setParameters] = useState<Record<string, string>>({});

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [currentTraceId, setCurrentTraceId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"up" | "down" | null>(null);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [traceUrlTemplate, setTraceUrlTemplate] = useState<string>("");

  // Fetch experiment info on mount
  React.useEffect(() => {
    fetch('/api/tracing_experiment')
      .then(res => res.json())
      .then(data => {
        setTraceUrlTemplate(data.trace_url_template);
      })
      .catch(err => console.error('Failed to fetch experiment info:', err));
  }, []);

  const selectedAnalysis = ANALYSIS_TYPES.find(a => a.id === selectedAnalysisType);

  const handleAnalysisTypeChange = (type: string) => {
    setSelectedAnalysisType(type);
    setParameters({});
  };

  // Generate question text based on selections
  const generateQuestionText = (): string => {
    if (!selectedTeam || !selectedAnalysisType) {
      return "Select team and analysis type to generate question...";
    }

    const yearText = selectedSeasons.length > 0
      ? selectedSeasons.length === 1
        ? selectedSeasons[0]
        : selectedSeasons.join(" and ")
      : "";

    switch (selectedAnalysisType) {
      case "down-distance":
        const distance = parameters.distance || "medium";
        return `How do the ${yearText} ${selectedTeam} offense handle 3rd and ${distance} situations?`;
      case "post-turnover":
        return `How do the ${yearText} ${selectedTeam} handle offense after a turnover?`;
      case "end-of-halves":
        return `How do the ${yearText} ${selectedTeam} handle the end of halves?`;
      default:
        return "Select analysis type to generate question...";
    }
  };

  const questionText = generateQuestionText();

  const handleAnalyze = async () => {
    const quickSelectData = QUICK_SELECT_QUESTIONS.find(q => q.id === quickSelect);
    const activeQuestion = quickSelectData ? quickSelectData.question : questionText;

    if (!quickSelect && (!selectedTeam || !selectedAnalysisType)) {
      setError("Please select a quick question or configure one below");
      return;
    }

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
      question: activeQuestion
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
                // Add tool call to the list
                const toolCall: ToolCall = {
                  tool: data.tool.name || data.tool.function_name || "Unknown",
                  arguments: data.tool.arguments ? JSON.parse(data.tool.arguments) : {},
                  status: "success"
                };
                setToolCalls(prev => [...prev, toolCall]);
              } else if (data.type === "done") {
                // Set trace ID even if it's null (allows feedback section to show)
                setCurrentTraceId(data.trace_id || null);
                console.log("Received trace_id:", data.trace_id);
                // Process any tool calls from the done event
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
      {/* Left Panel - Quick Select + Question Configuration */}
      <div className="space-y-4">
        <Card>
          <CardContent className="pt-6 space-y-4">
            {/* Quick Select */}
            <div className="space-y-2">
              <Label htmlFor="quick-select" className="font-semibold">Quick Select</Label>
              <Select value={quickSelect} onValueChange={(val) => {
                setQuickSelect(val);
                // Clear manual config when quick select is chosen
                setSelectedTeam("");
                setSelectedAnalysisType("");
                setParameters({});
              }}>
                <SelectTrigger>
                  <SelectValue placeholder="Pick a pre-built question..." />
                </SelectTrigger>
                <SelectContent>
                  {QUICK_SELECT_QUESTIONS.map((q) => (
                    <SelectItem key={q.id} value={q.id}>
                      {q.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Show selected quick question */}
            {quickSelect && (
              <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                <Label className="text-xs text-blue-600 dark:text-blue-400 font-semibold mb-2 block">
                  Question to Agent
                </Label>
                <p className="text-sm text-blue-900 dark:text-blue-100 italic">
                  "{QUICK_SELECT_QUESTIONS.find(q => q.id === quickSelect)?.question}"
                </p>
              </div>
            )}

            <Button
              onClick={handleAnalyze}
              disabled={loading || (!quickSelect && (!selectedTeam || !selectedAnalysisType))}
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

            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">or configure your own</span>
              </div>
            </div>

            {/* Team Selector */}
            <div className="space-y-2">
              <Label htmlFor="team">Team</Label>
              <Select value={selectedTeam} onValueChange={(val) => { setSelectedTeam(val); setQuickSelect(""); }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select NFL team..." />
                </SelectTrigger>
                <SelectContent>
                  {NFL_TEAMS.map((team) => (
                    <SelectItem key={team} value={team}>
                      {team}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Season Selector */}
            <div className="space-y-2">
              <Label htmlFor="season">Season</Label>
              <div className="flex gap-2">
                <Button
                  variant={selectedSeasons.includes("2023") ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    if (selectedSeasons.includes("2023")) {
                      setSelectedSeasons(prev => prev.filter(s => s !== "2023"));
                    } else {
                      setSelectedSeasons(prev => [...prev, "2023"]);
                    }
                  }}
                >
                  2023
                </Button>
                <Button
                  variant={selectedSeasons.includes("2024") ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    if (selectedSeasons.includes("2024")) {
                      setSelectedSeasons(prev => prev.filter(s => s !== "2024"));
                    } else {
                      setSelectedSeasons(prev => [...prev, "2024"]);
                    }
                  }}
                >
                  2024
                </Button>
              </div>
            </div>

            {/* Analysis Type */}
            <div className="space-y-2">
              <Label htmlFor="analysis-type">Analysis Type</Label>
              <Select value={selectedAnalysisType} onValueChange={(val) => { handleAnalysisTypeChange(val); setQuickSelect(""); }}>
                <SelectTrigger>
                  <SelectValue placeholder="Select analysis type..." />
                </SelectTrigger>
                <SelectContent>
                  {ANALYSIS_TYPES.map((type) => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Dynamic Parameters */}
            {selectedAnalysis && selectedAnalysis.parameters.map((param) => (
              <div key={param} className="space-y-2">
                <Label htmlFor={param}>{param.charAt(0).toUpperCase() + param.slice(1)}</Label>
                <Select
                  value={parameters[param] || ""}
                  onValueChange={(value) => setParameters(prev => ({ ...prev, [param]: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={`Select ${param}...`} />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedAnalysis.options[param]?.map((option: string) => (
                      <SelectItem key={option} value={option}>
                        {option}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            ))}

            {/* Generated Question Display */}
            {selectedTeam && selectedAnalysisType && (
              <>
                <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                  <Label className="text-xs text-blue-600 dark:text-blue-400 font-semibold mb-2 block">
                    Question to Agent
                  </Label>
                  <p className="text-sm text-blue-900 dark:text-blue-100 italic">
                    "{questionText}"
                  </p>
                </div>

                <Button
                  onClick={handleAnalyze}
                  disabled={loading}
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
              </>
            )}
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

                {/* Show feedback and trace button only after streaming completes */}
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
                            <Label htmlFor="feedback-comment">
                              Additional Comments (Optional)
                            </Label>
                            <Textarea
                              id="feedback-comment"
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
                            See trace & feedback in MLflow UI
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
                <p>Configure your question and click Analyze to see the agent in action</p>
                <p className="text-xs mt-2">Tool calls and streaming response will appear here</p>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
