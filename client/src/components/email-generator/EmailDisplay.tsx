import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ThumbsUp, ThumbsDown, CheckCircle, ExternalLink } from "lucide-react";
import { useQueryExperiment } from "@/queries/useQueryTracing";

interface EmailDisplayProps {
  email?: {
    subject_line: string;
    body: string;
    isPartial?: boolean;
  };
  streamingContent?: string;
  isStreaming?: boolean;
  currentTraceId: string | null;
  feedbackRating: "up" | "down" | null;
  feedbackComment: string;
  feedbackSubmitted: boolean;
  onFeedbackRatingChange: (rating: "up" | "down") => void;
  onFeedbackCommentChange: (comment: string) => void;
  onFeedbackSubmit: () => void;
  hideTraceSection?: boolean;
  hideFeedbackSection?: boolean;
}

// Helper function to try parsing partial JSON and extract readable content
function parsePartialEmail(content: string): {
  subject_line?: string;
  body?: string;
  isPartial: boolean;
} {
  if (!content) return { isPartial: true };

  try {
    // Try to parse complete JSON
    const parsed = JSON.parse(content);
    return { ...parsed, isPartial: false };
  } catch {
    // If that fails, try to extract partial information
    const result: { subject_line?: string; body?: string; isPartial: boolean } =
      { isPartial: true };

    // Try to extract subject line
    const subjectMatch = content.match(/"subject_line"\s*:\s*"([^"]*)"/);
    if (subjectMatch) {
      result.subject_line = subjectMatch[1];
    }

    // Try to extract body (including incomplete streaming content)
    // Look for the body field and capture everything after it, even if incomplete
    const bodyFieldStart = content.indexOf('"body"');
    if (bodyFieldStart !== -1) {
      // Find the start of the body value
      const bodyValueStart = content.indexOf('"', bodyFieldStart + 6); // Skip past "body":
      if (bodyValueStart !== -1) {
        // Get everything from the opening quote to the end of available content
        let bodyContent = content.substring(bodyValueStart + 1);

        // Handle the case where the JSON string is still being streamed
        // If it ends with a complete quote and closing brace, it's complete
        if (bodyContent.endsWith('"}')) {
          bodyContent = bodyContent.slice(0, -2); // Remove the closing quote and brace
        } else if (bodyContent.endsWith('"')) {
          bodyContent = bodyContent.slice(0, -1); // Remove just the closing quote
        }
        // If it doesn't end with a quote, it's still streaming

        // Process escape sequences
        result.body = bodyContent
          .replace(/\\n/g, "\n")
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, "\\");
      }
    }

    return result;
  }
}

export function EmailDisplay({
  email,
  streamingContent,
  isStreaming = false,
  currentTraceId,
  feedbackRating,
  feedbackComment,
  feedbackSubmitted,
  onFeedbackRatingChange,
  onFeedbackCommentChange,
  onFeedbackSubmit,
  hideTraceSection = false,
  hideFeedbackSection = false,
}: EmailDisplayProps) {
  // Fetch experiment data for trace links
  const { data: experiment } = useQueryExperiment();

  // Determine what to display - either final email or parsed streaming content
  const displayEmail =
    email || (streamingContent ? parsePartialEmail(streamingContent) : null);
  const showRawJson =
    isStreaming &&
    streamingContent &&
    !displayEmail?.subject_line &&
    !displayEmail?.body;
  return (
    <Card className="h-full animate-in fade-in-50 duration-500">
      <CardHeader>
        <CardTitle>Generated Email</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isStreaming && !streamingContent ? (
          /* Show initial loading state when streaming starts but no content yet */
          <div className="text-center py-12">
            <div className="inline-flex items-center gap-2 text-muted-foreground">
              <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full"></div>
              <span>Generating email...</span>
            </div>
          </div>
        ) : showRawJson ? (
          /* Show raw JSON during early streaming when we can't parse structure */
          <div>
            <Label className="text-sm font-medium text-muted-foreground">
              Generating Email...
            </Label>
            <div className="mt-2 p-4 bg-muted rounded-lg">
              <pre className="whitespace-pre-wrap font-mono text-xs text-muted-foreground">
                {streamingContent}
                {isStreaming && <span className="animate-pulse">▊</span>}
              </pre>
            </div>
          </div>
        ) : displayEmail ? (
          <>
            {/* Subject Line */}
            <div>
              <Label className="text-sm font-medium text-muted-foreground">
                Subject{" "}
                {displayEmail.isPartial && (
                  <Badge variant="secondary" className="ml-2">
                    Generating...
                  </Badge>
                )}
              </Label>
              {displayEmail.subject_line ? (
                <h3 className="text-lg font-semibold mt-1">
                  {displayEmail.subject_line}
                  {displayEmail.isPartial && isStreaming && (
                    <span className="animate-pulse ml-1">▊</span>
                  )}
                </h3>
              ) : (
                <div className="mt-1 h-7 bg-muted rounded animate-pulse" />
              )}
            </div>

            {/* Email Body */}
            <div>
              <Label className="text-sm font-medium text-muted-foreground">
                Body{" "}
                {displayEmail.isPartial && (
                  <Badge variant="secondary" className="ml-2">
                    Generating...
                  </Badge>
                )}
              </Label>
              {displayEmail.body !== undefined ? (
                <div className="mt-2 p-4 bg-muted rounded-lg">
                  <pre className="whitespace-pre-wrap font-sans text-sm">
                    {displayEmail.body || ""}
                    {displayEmail.isPartial && isStreaming && (
                      <span className="animate-pulse ml-1">▊</span>
                    )}
                  </pre>
                </div>
              ) : (
                <div className="mt-2 p-4 bg-muted rounded-lg">
                  <div className="space-y-2">
                    <div className="h-4 bg-slate-300 rounded animate-pulse" />
                    <div className="h-4 bg-slate-300 rounded animate-pulse w-4/5" />
                    <div className="h-4 bg-slate-300 rounded animate-pulse w-3/5" />
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            Select a company and generate an email to see it here
          </div>
        )}

        {/* Feedback Section - Only show when email is complete */}
        {!hideFeedbackSection && displayEmail && !displayEmail.isPartial && (
          <div className="border-t pt-6">
            <h4 className="font-medium mb-4">How is this email?</h4>

            {feedbackSubmitted ? (
              <div className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
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
                    onClick={() => onFeedbackRatingChange("up")}
                    className="flex-1"
                  >
                    <ThumbsUp className="mr-2 h-5 w-5" />
                    Good
                  </Button>
                  <Button
                    variant={feedbackRating === "down" ? "default" : "outline"}
                    size="lg"
                    onClick={() => onFeedbackRatingChange("down")}
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
                    onChange={(e) => onFeedbackCommentChange(e.target.value)}
                    placeholder="What could be improved? What did you like?"
                    rows={3}
                  />
                </div>

                <Button
                  onClick={onFeedbackSubmit}
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
        )}

        {/* Trace Section - Only show when email is complete and trace ID exists */}
        {!hideTraceSection &&
          displayEmail &&
          !displayEmail.isPartial &&
          currentTraceId &&
          experiment && (
            <div className="border-t pt-6">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-medium">
                  See trace & feedback in MLflow UI
                </h4>
                <Button
                  variant="open_mlflow_ui"
                  size="lg"
                  onClick={() =>
                    window.open(
                      `${experiment.trace_url_template}${currentTraceId}`,
                      "_blank",
                    )
                  }
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View Trace
                </Button>
              </div>
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-2">
                  What to Look For in MLflow:
                </h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>
                    • Each email generation creates a new trace with unique ID
                  </li>
                  <li>
                    • Input parameters (customer data) are captured
                    automatically
                  </li>
                  <li>• Output (generated email) is logged for review</li>
                  <li>• User feedback (👍/👎) is linked to specific traces</li>
                  <li>• Execution time and token usage are tracked</li>
                </ul>
              </div>
            </div>
          )}
      </CardContent>
    </Card>
  );
}
