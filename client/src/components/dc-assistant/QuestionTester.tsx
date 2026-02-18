import React, { useState, useRef, useEffect } from "react";
import { MarkdownContent } from "@/components/markdown-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Send, RefreshCw, FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";

interface Turn {
  question: string;
  response: string;
  traceId: string | null;
}

export function QuestionTester() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns, loading, pendingQuestion]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    setInput("");
    setLoading(true);
    setPendingQuestion(question);
    setError(null);

    try {
      const response = await fetch("/api/dc-assistant/multi-turn", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          is_first_turn: turns.length === 0,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      setTurns((prev) => [
        ...prev,
        {
          question,
          response: data.response,
          traceId: data.trace_id,
        },
      ]);
    } catch (err: any) {
      console.error("Error sending question:", err);
      setError(err.message || "Failed to send question");
    } finally {
      setLoading(false);
      setPendingQuestion(null);
    }
  };

  const handleNewSession = () => {
    setTurns([]);
    setSessionId(null);
    setInput("");
    setPendingQuestion(null);
    setError(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card className="mt-8 border-dashed border-yellow-400">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <FlaskConical className="h-5 w-5 text-yellow-600" />
              Question Tester
              <Badge variant="outline" className="text-xs text-yellow-600 border-yellow-400">
                Testing Only
              </Badge>
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Free-form multi-turn testing for curating session-level evaluation questions
            </p>
          </div>
          {sessionId && (
            <Badge variant="outline" className="text-xs font-mono">
              Session: {sessionId.slice(0, 8)}...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Conversation history */}
        {(turns.length > 0 || pendingQuestion) && (
          <div
            ref={scrollRef}
            className="space-y-3 max-h-96 overflow-y-auto rounded-lg border bg-muted/20 p-3"
          >
            {turns.map((turn, idx) => (
              <div key={idx} className="space-y-2">
                {/* User question */}
                <div className="flex justify-end">
                  <div className="max-w-[85%] p-3 rounded-lg bg-blue-600 text-white text-sm">
                    {turn.question}
                  </div>
                </div>
                {/* Agent response */}
                <div className="flex justify-start">
                  <div className="max-w-[85%] p-3 rounded-lg bg-background border text-sm">
                    <MarkdownContent content={turn.response} />
                    {turn.traceId && (
                      <code className="block mt-2 text-[10px] text-muted-foreground">
                        trace: {turn.traceId.slice(0, 16)}...
                      </code>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {pendingQuestion && (
              <>
                <div className="flex justify-end">
                  <div className="max-w-[85%] p-3 rounded-lg bg-blue-600 text-white text-sm">
                    {pendingQuestion}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="p-3 rounded-lg bg-background border text-sm flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Thinking...
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Input area */}
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a question... (Enter to send, Shift+Enter for newline)"
            rows={2}
            className="resize-none flex-1"
            disabled={loading}
          />
          <div className="flex flex-col gap-2">
            <Button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              size="icon"
              className="h-full"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* New Session button */}
        <Button
          onClick={handleNewSession}
          variant="outline"
          size="sm"
          className="w-full"
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          New Session
        </Button>
      </CardContent>
    </Card>
  );
}
