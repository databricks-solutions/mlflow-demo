import "./index.css"; // Tailwind styles
import React, { use, useEffect } from "react";
import "./App.css";
import { QueryClient, QueryClientProvider } from "react-query";
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Plus, ArrowUp } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ENDPOINTS } from "@/endpoints";
import { useQueryExperiment } from "@/queries/useQueryTracing";
import { Spinner } from "@/components/Spinner";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { EmailGenerator } from "@/components/email-generator/EmailGenerator";
import { DemoOverview } from "@/components/demo-overview";
import { TracingDemo } from "@/components/demo-pages/observe-with-tracing";
import { EvaluationBuilder } from "@/components/demo-pages/create-quality-metrics";
import { PromptTesting } from "@/components/demo-pages/find-fix-quality-issues";
import { BusinessMetrics } from "@/components/demo-pages/business-metrics";
import { MonitoringDemo } from "@/components/demo-pages/prod-monitoring";
import { HumanReview } from "@/components/demo-pages/human-review";
import { PromptRegistry } from "@/components/prompt-registry";
import { ViewType, getViewTypeFromPath, getPathFromViewType } from "@/routes";

const queryClient = new QueryClient();

export function Chat() {
  const [messages, setMessages] = useState<
    {
      role: "user" | "system" | "assistant";
      content: string;
      traceId?: string;
      isStreaming?: boolean;
    }[]
  >([]);
  const [input, setInput] = useState("");
  const lastMessageRef = React.useRef<HTMLDivElement>(null);

  const { data: experiment, isLoading: experimentIsLoading } =
    useQueryExperiment();

  const [isStreamingEnabled, setIsStreamingEnabled] = useState(true);

  const scrollToBottom = () => {
    // First try to use the ref if available
    if (lastMessageRef.current) {
      lastMessageRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }

    // Also scroll the container to ensure we're at the bottom
    setTimeout(() => {
      const scrollArea = document.querySelector(
        "[data-radix-scroll-area-viewport]",
      );
      if (scrollArea) {
        scrollArea.scrollTo({
          top: scrollArea.scrollHeight,
          behavior: "smooth",
        });
      }
    }, 0);
  };

  // Chat functionality removed - unused feature

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const [selectedAgent, setSelectedAgent] = useState(ENDPOINTS[0].endpointName);
  const location = useLocation();
  const navigate = useNavigate();
  const currentView = getViewTypeFromPath(location.pathname);

  const setCurrentView = (viewType: ViewType) => {
    navigate(getPathFromViewType(viewType));
  };

  return (
    <TooltipProvider>
      <SidebarProvider>
        <AppSidebar
          selectedAgent={selectedAgent}
          setSelectedAgent={setSelectedAgent}
          setMessages={setMessages}
          experiment={experiment}
          experimentIsLoading={experimentIsLoading}
          isStreamingEnabled={isStreamingEnabled}
          setIsStreamingEnabled={setIsStreamingEnabled}
        />
        <main className="flex-1 flex items-center justify-center p-4">
          <Routes>
            <Route
              path="/email"
              element={
                <div className="w-full h-full">
                  <EmailGenerator />
                </div>
              }
            />
            <Route
              path="/"
              element={
                <div className="w-full h-full">
                  <DemoOverview />
                </div>
              }
            />
            <Route
              path="/tracing"
              element={
                <div className="w-full h-full">
                  <TracingDemo />
                </div>
              }
            />
            <Route
              path="/evaluation"
              element={
                <div className="w-full h-full">
                  <EvaluationBuilder />
                </div>
              }
            />
            <Route
              path="/improvement"
              element={
                <div className="w-full h-full">
                  <PromptTesting />
                </div>
              }
            />
            <Route
              path="/kpis"
              element={
                <div className="w-full h-full">
                  <BusinessMetrics />
                </div>
              }
            />
            <Route
              path="/monitoring"
              element={
                <div className="w-full h-full">
                  <MonitoringDemo />
                </div>
              }
            />
            <Route
              path="/human-review"
              element={
                <div className="w-full h-full">
                  <HumanReview />
                </div>
              }
            />
            <Route
              path="/prompt-registry"
              element={
                <div className="w-full h-full">
                  <PromptRegistry />
                </div>
              }
            />
          </Routes>
        </main>
      </SidebarProvider>
    </TooltipProvider>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/*" element={<Chat />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
