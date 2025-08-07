import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, ThumbsUp, ThumbsDown, Send } from "lucide-react";
import { CompanySearch } from "./CompanySearch";
import { CustomerForm } from "./CustomerForm";
import { CustomerDataRetriever } from "./CustomerDataRetriever";
import { EmailDisplay } from "./EmailDisplay";
import { EmailService } from "@/fastapi_client";
import type { EmailRequest, FeedbackRequest } from "@/fastapi_client/models";

interface EmailGeneratorProps {
  onTraceIdGenerated?: (traceId: string) => void;
  hideCustomerForm?: boolean;
  hideTraceSection?: boolean;
  hideFeedbackSection?: boolean;
}

export function EmailGenerator({
  onTraceIdGenerated,
  hideCustomerForm = false,
  hideTraceSection = false,
  hideFeedbackSection = false,
}: EmailGeneratorProps = {}) {
  const [companies, setCompanies] = useState<{ name: string }[]>([]);
  const [selectedCompany, setSelectedCompany] = useState("");
  const [customerData, setCustomerData] = useState<any>(null);
  const [userInstructions, setUserInstructions] = useState("");
  const [generatedEmail, setGeneratedEmail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [loadingCustomerData, setLoadingCustomerData] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [currentTraceId, setCurrentTraceId] = useState<string | null>(null);
  const [feedbackRating, setFeedbackRating] = useState<"up" | "down" | null>(
    null,
  );
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      setLoadingCompanies(true);
      const response = await EmailService.getCompaniesApiCompaniesGet();
      setCompanies(response);
    } catch (err) {
      console.error("Error loading companies:", err);
      setError("Failed to load companies");
    } finally {
      setLoadingCompanies(false);
    }
  };

  const handleCompanySelect = async (companyName: string) => {
    setSelectedCompany(companyName);
    setUserInstructions("");
    setGeneratedEmail(null);
    setFeedbackRating(null);
    setFeedbackComment("");
    setFeedbackSubmitted(false);

    if (!companyName) {
      setCustomerData(null);
      setLoadingCustomerData(false);
      return;
    }

    setLoadingCustomerData(true);
    setError(null);

    try {
      const response =
        await EmailService.getCustomerByNameApiCustomerCompanyNameGet(
          companyName,
        );
      setCustomerData(response);
      setError(null);
    } catch (err) {
      console.error("Error loading customer data:", err);
      setError("Failed to load customer data");
      setCustomerData(null);
    } finally {
      setLoadingCustomerData(false);
    }
  };

  // Customer data is now read-only since it comes from MLflow retriever
  const updateNestedField = (path: string, value: any) => {
    // No-op: Customer data is immutable when loaded via retriever
    console.log("Customer data is read-only when loaded via MLflow retriever");
  };

  const handleGenerateEmail = async () => {
    if (!selectedCompany) {
      setError("Please select a company first");
      return;
    }

    setLoading(true);
    setIsStreaming(true);
    setError(null);
    setGeneratedEmail(null);
    setStreamingContent("");
    setFeedbackRating(null);
    setFeedbackComment("");
    setFeedbackSubmitted(false);
    setCurrentTraceId(null);

    const requestData = {
      customer_name: selectedCompany,
      user_input: userInstructions || undefined,
    };

    try {
      const response = await fetch(
        "/api/generate-email-stream-with-retrieval/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestData),
        },
      );

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
              } else if (data.type === "done" && data.trace_id) {
                setCurrentTraceId(data.trace_id);
                onTraceIdGenerated?.(data.trace_id);
                // Parse the final email
                try {
                  const emailJson = JSON.parse(accumulatedContent);
                  setGeneratedEmail(emailJson);
                } catch (e) {
                  console.error("Failed to parse email JSON:", e);
                  setError("Failed to parse generated email");
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
      console.error("Error generating email:", err);
      setError(err.message || "Failed to generate email");
    } finally {
      setLoading(false);
      setIsStreaming(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackRating || !currentTraceId) return;

    try {
      const feedbackData: FeedbackRequest = {
        trace_id: currentTraceId,
        rating: feedbackRating,
        comment: feedbackComment || undefined,
        sales_rep_name: customerData?.sales_rep?.name,
      };

      const response =
        await EmailService.submitFeedbackApiFeedbackPost(feedbackData);

      if (response.success) {
        setFeedbackSubmitted(true);
      } else {
        setError(response.message);
      }
    } catch (err) {
      console.error("Error submitting feedback:", err);
      setError("Failed to submit feedback");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      {/* Left Panel - Input */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Customer Selection</CardTitle>
          </CardHeader>
          <CardContent>
            <CompanySearch
              companies={companies}
              selectedCompany={selectedCompany}
              onCompanySelect={handleCompanySelect}
              loading={loadingCompanies}
            />
          </CardContent>
        </Card>

        {selectedCompany && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Email Instructions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label htmlFor="instructions">
                    Additional Instructions (Optional)
                  </Label>
                  <Textarea
                    id="instructions"
                    value={userInstructions}
                    onChange={(e) => setUserInstructions(e.target.value)}
                    placeholder="E.g., Mention the upcoming product launch, emphasize our new pricing model, schedule a demo for next week..."
                    rows={4}
                  />
                </div>
                <Button
                  onClick={handleGenerateEmail}
                  disabled={loading || !selectedCompany}
                  className="mt-4 w-full"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : loadingCustomerData ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Loading Customer Data...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      Generate Email
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Customer Data with Loading State */}
            <CustomerDataRetriever
              customerData={customerData}
              isLoading={loadingCustomerData}
              retrievalStatus={
                loadingCustomerData
                  ? "loading"
                  : customerData
                    ? "success"
                    : "error"
              }
              dataSource="input_data.jsonl"
            />

            {!hideCustomerForm && customerData && (
              <CustomerForm
                customerData={customerData}
                updateField={updateNestedField}
              />
            )}
          </>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>

      {/* Right Panel - Output */}
      <div>
        <EmailDisplay
          email={generatedEmail}
          streamingContent={isStreaming ? streamingContent : undefined}
          isStreaming={isStreaming}
          currentTraceId={currentTraceId}
          feedbackRating={feedbackRating}
          feedbackComment={feedbackComment}
          feedbackSubmitted={feedbackSubmitted}
          onFeedbackRatingChange={setFeedbackRating}
          onFeedbackCommentChange={setFeedbackComment}
          onFeedbackSubmit={handleFeedbackSubmit}
          hideTraceSection={hideTraceSection}
          hideFeedbackSection={hideFeedbackSection}
        />
      </div>
    </div>
  );
}
