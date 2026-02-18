import React, { useState } from "react";
import { MarkdownContent } from "@/components/markdown-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Send, ExternalLink, MessageCircle, ArrowDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useQueryExperiment } from "@/queries/useQueryTracing";

// NFL Teams for comparison
const NFL_TEAMS = [
  "Dallas Cowboys",
  "San Francisco 49ers",
  "Kansas City Chiefs",
  "Buffalo Bills",
  "Philadelphia Eagles",
  "Green Bay Packers",
  "Miami Dolphins",
  "Baltimore Ravens",
];

interface ConversationTurn {
  question: string;
  response: string;
  traceId: string | null;
}

export function MultiTurnDemo() {
  const { data: experiment } = useQueryExperiment();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentTurn, setCurrentTurn] = useState(0);
  const [compareTeam, setCompareTeam] = useState<string>("Dallas Cowboys");

  // Build conversation flow dynamically based on selected team
  const getConversationFlow = () => [
    {
      question: "What do raiders in 2024 typically do after turnovers?",
      isFollowUp: false,
    },
    {
      question: `Compare them to the ${compareTeam}`,
      isFollowUp: true,
    },
  ];

  const handleRunDemo = async () => {
    setLoading(true);
    setError(null);
    setTurns([]);
    setCurrentTurn(0);
    setSessionId(null);

    const conversationFlow = getConversationFlow();

    try {
      // Run through all conversation turns
      for (let i = 0; i < conversationFlow.length; i++) {
        setCurrentTurn(i);
        const turn = conversationFlow[i];

        // Simulate streaming delay for better UX
        await new Promise((resolve) => setTimeout(resolve, 500));

        const response = await fetch("/api/dc-assistant/multi-turn", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: turn.question,
            session_id: sessionId,
            is_first_turn: i === 0,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update session ID from first response
        if (i === 0 && data.session_id) {
          setSessionId(data.session_id);
        }

        // Add turn to conversation
        setTurns((prev) => [
          ...prev,
          {
            question: turn.question,
            response: data.response,
            traceId: data.trace_id,
          },
        ]);

        // Delay between turns for readability
        if (i < conversationFlow.length - 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      }
    } catch (err: any) {
      console.error("Error running multi-turn demo:", err);
      setError(err.message || "Failed to run demo");
    } finally {
      setLoading(false);
      setCurrentTurn(-1);
    }
  };

  const handleReset = () => {
    setTurns([]);
    setSessionId(null);
    setCurrentTurn(0);
    setError(null);
  };

  return (
    <Card className="mt-8">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Multi-Turn Conversations
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-2">
              See how MLflow tracks entire conversation sessions, maintaining context across multiple turns
            </p>
          </div>
          {sessionId && (
            <Badge variant="outline" className="text-xs">
              Session: {sessionId.slice(0, 8)}...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Info Section */}
        <Alert>
          <AlertDescription className="text-sm">
            <strong>Why Multi-Turn Tracking Matters:</strong> Real conversations aren't
            single questions—coaches ask follow-ups that reference previous context. MLflow's
            session tracking captures the entire conversation flow in one unified trace view,
            making it easy to debug and evaluate conversational AI quality.
          </AlertDescription>
        </Alert>

        {/* Configuration */}
        {turns.length === 0 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="compare-team">Team to Compare</Label>
              <Select value={compareTeam} onValueChange={setCompareTeam}>
                <SelectTrigger>
                  <SelectValue placeholder="Select team..." />
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

            <div className="text-sm font-medium">Demo Conversation Flow:</div>
            <div className="space-y-3">
              {getConversationFlow().map((turn, idx) => (
                <div key={idx} className="space-y-2">
                  <div
                    className={`p-3 rounded-lg border ${
                      turn.isFollowUp
                        ? "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800"
                        : "bg-muted/50"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <Badge variant={turn.isFollowUp ? "default" : "secondary"} className="text-xs">
                        Turn {idx + 1}
                      </Badge>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{turn.question}</p>
                      </div>
                    </div>
                  </div>
                  {idx < getConversationFlow().length - 1 && (
                    <div className="flex justify-center">
                      <ArrowDown className="h-4 w-4 text-muted-foreground" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Live Conversation Display */}
        {turns.length > 0 && (
          <div className="space-y-4">
            {turns.map((turn, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-start gap-3">
                  <Badge variant="secondary" className="text-xs mt-1">
                    Turn {idx + 1}
                  </Badge>
                  <div className="flex-1 space-y-2">
                    {/* Question */}
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        {turn.question}
                      </p>
                    </div>

                    {/* Response */}
                    <div className="p-3 bg-muted/50 rounded-lg border">
                      <MarkdownContent content={turn.response} className="text-sm" />
                    </div>

                    {/* Trace Link */}
                    {turn.traceId && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <code className="bg-muted px-2 py-1 rounded">
                          {turn.traceId.slice(0, 16)}...
                        </code>
                      </div>
                    )}
                  </div>
                </div>

                {idx < turns.length - 1 && (
                  <div className="flex justify-center py-2">
                    <ArrowDown className="h-4 w-4 text-muted-foreground" />
                  </div>
                )}
              </div>
            ))}

            {/* Loading indicator for next turn */}
            {loading && currentTurn >= 0 && turns.length < getConversationFlow().length && (
              <>
                <div className="flex justify-center py-2">
                  <ArrowDown className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex items-center gap-2 p-3 rounded-lg border border-dashed text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Sending follow-up (Turn {turns.length + 1})...</span>
                </div>
              </>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {turns.length === 0 ? (
            <Button onClick={handleRunDemo} disabled={loading} className="flex-1">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Asking DC Assistant (Turn {currentTurn + 1}/{getConversationFlow().length})...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Ask DC Assistant
                </>
              )}
            </Button>
          ) : (
            <>
              <Button onClick={handleReset} variant="outline" className="flex-1">
                Reset Demo
              </Button>
              {sessionId && experiment?.session_url_template && (
                <Button
                  onClick={() => {
                    const sessionUrl = experiment.session_url_template.replaceAll('{sessionId}', sessionId);
                    window.open(sessionUrl, "_blank");
                  }}
                  className="flex-1"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View Session in MLflow
                </Button>
              )}
            </>
          )}
        </div>

        {/* Educational Footer */}
        {sessionId && (
          <Alert>
            <AlertDescription className="text-xs">
              <strong>🎯 Session Tracking:</strong> Both turns share session ID{" "}
              <code className="bg-muted px-1 py-0.5 rounded">{sessionId.slice(0, 12)}...</code>.
              View the complete conversation flow in MLflow's session trace to see how the agent
              maintains context across multiple turns and makes comparative analysis.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
