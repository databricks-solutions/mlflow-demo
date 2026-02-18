import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, ThumbsUp, ThumbsDown, Send, ExternalLink } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useQueryExperiment } from "@/queries/useQueryTracing";

// Question categories and pre-defined questions
const QUESTION_CATEGORIES = [
  { id: "3rd-down", label: "3rd Down Situations" },
  { id: "red-zone", label: "Red Zone Plays" },
  { id: "two-minute", label: "Two-Minute Drill" },
  { id: "personnel", label: "Personnel Packages" },
] as const;

const QUESTIONS_BY_CATEGORY: Record<string, string[]> = {
  "3rd-down": [
    "What do the Cowboys do on 3rd and short in 11 personnel?",
    "Who gets the ball for the 49ers on 3rd and 6?",
    "What formations do the Chiefs use on 3rd and long?",
    "How do the Eagles attack the blitz on 3rd down?",
  ],
  "red-zone": [
    "What are the Packers' red zone tendencies?",
    "Who scores touchdowns for the Ravens inside the 10?",
    "What plays do the Bills run in goal-to-go situations?",
    "How do the Dolphins use motion in the red zone?",
  ],
  "two-minute": [
    "What do the Bengals do in the last 2 minutes of halves?",
    "How do the Patriots manage the clock in hurry-up?",
    "What's the Chiefs' two-minute personnel package?",
    "How do the Raiders attack prevent defense?",
  ],
  personnel: [
    "What does the Titans' 12 personnel look like?",
    "Who gets the ball in the Lions' 11 personnel?",
    "What are the Cardinals' 21 personnel tendencies?",
    "How do the Seahawks use 10 personnel formations?",
  ],
};

interface DcAssistantProps {
  onTraceIdGenerated?: (traceId: string) => void;
  hideTraceSection?: boolean;
  hideFeedbackSection?: boolean;
}

export function DcAssistant({
  onTraceIdGenerated,
  hideTraceSection = false,
  hideFeedbackSection = false,
}: DcAssistantProps = {}) {
  const { data: experiment } = useQueryExperiment();
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [customQuestion, setCustomQuestion] = useState("");
  const [analysis, setAnalysis] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentTraceId, setCurrentTraceId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"up" | "down" | null>(
    null,
  );
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    setSelectedQuestion("");
    setCustomQuestion("");
    setAnalysis("");
    setError(null);
  };

  const handleQuestionSelect = (question: string) => {
    setSelectedQuestion(question);
    setCustomQuestion("");
  };

  const handleAnalyze = async () => {
    const questionToAnalyze = customQuestion || selectedQuestion;

    if (!questionToAnalyze) {
      setError("Please select or enter a question");
      return;
    }

    setLoading(true);
    setIsStreaming(true);
    setError(null);
    setAnalysis("");
    setStreamingContent("");
    setFeedbackRating(null);
    setFeedbackComment("");
    setFeedbackSubmitted(false);
    setCurrentTraceId(null);

    const requestData = {
      question: questionToAnalyze,
    };

    try {
      const response = await fetch("/api/dc-assistant/analyze-stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
              } else if (data.type === "done") {
                // Always set the analysis when done, even without trace_id
                if (accumulatedContent) {
                  setAnalysis(accumulatedContent);
                }
                if (data.trace_id) {
                  setCurrentTraceId(data.trace_id);
                  onTraceIdGenerated?.(data.trace_id);
                }
              } else if (data.type === "error") {
                setError(data.error);
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (err: any) {
      console.error("Error analyzing question:", err);
      setError(err.message || "Failed to analyze question");
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

  const availableQuestions = selectedCategory
    ? QUESTIONS_BY_CATEGORY[selectedCategory] || []
    : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      {/* Left Panel - Input */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>NFL Defensive Coordinator Assistant</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="category">Question Category</Label>
              <Select value={selectedCategory} onValueChange={handleCategoryChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a category..." />
                </SelectTrigger>
                <SelectContent>
                  {QUESTION_CATEGORIES.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedCategory && (
              <div className="space-y-2">
                <Label htmlFor="question">Select Question</Label>
                <Select value={selectedQuestion} onValueChange={handleQuestionSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a question..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableQuestions.map((q, idx) => (
                      <SelectItem key={idx} value={q}>
                        {q}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="custom-question">Or Enter Custom Question</Label>
              <Textarea
                id="custom-question"
                value={customQuestion}
                onChange={(e) => {
                  setCustomQuestion(e.target.value);
                  if (e.target.value) {
                    setSelectedQuestion("");
                  }
                }}
                placeholder="E.g., What do the Packers do on 2nd and long?"
                rows={3}
              />
            </div>

            <Button
              onClick={handleAnalyze}
              disabled={loading || (!selectedQuestion && !customQuestion)}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Analyze
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

      {/* Right Panel - Output */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {isStreaming || analysis ? (
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <pre className="whitespace-pre-wrap font-sans text-sm">
                    {isStreaming ? streamingContent : analysis}
                  </pre>
                </div>

                {!hideTraceSection && currentTraceId && experiment && (
                  <div className="pt-4 border-t">
                    <Label className="text-xs text-muted-foreground">
                      MLflow Trace
                    </Label>
                    <div className="mt-2 flex items-center gap-2">
                      <code className="text-xs bg-muted px-2 py-1 rounded flex-1 truncate">
                        {currentTraceId}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          window.open(
                            `${experiment.trace_url_template}${currentTraceId}`,
                            "_blank",
                          )
                        }
                      >
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View in MLflow
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <p>Analysis will appear here after you submit a question</p>
              </div>
            )}
          </CardContent>
        </Card>

        {!hideFeedbackSection && analysis && currentTraceId && (
          <Card>
            <CardHeader>
              <CardTitle>Coaching Feedback</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!feedbackSubmitted ? (
                <>
                  <div className="flex gap-2">
                    <Button
                      variant={feedbackRating === "up" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setFeedbackRating("up")}
                    >
                      <ThumbsUp className="h-4 w-4 mr-2" />
                      Helpful
                    </Button>
                    <Button
                      variant={feedbackRating === "down" ? "default" : "outline"}
                      size="sm"
                      onClick={() => setFeedbackRating("down")}
                    >
                      <ThumbsDown className="h-4 w-4 mr-2" />
                      Not Helpful
                    </Button>
                  </div>

                  {feedbackRating && (
                    <>
                      <div className="space-y-2">
                        <Label htmlFor="feedback-comment">
                          Additional Comments (Optional)
                        </Label>
                        <Textarea
                          id="feedback-comment"
                          value={feedbackComment}
                          onChange={(e) => setFeedbackComment(e.target.value)}
                          placeholder="Share your thoughts on this analysis..."
                          rows={3}
                        />
                      </div>
                      <Button onClick={handleFeedbackSubmit} className="w-full">
                        Submit Feedback
                      </Button>
                    </>
                  )}
                </>
              ) : (
                <Alert>
                  <AlertDescription>
                    Thank you for your feedback! Your input helps improve the DC
                    Assistant.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
