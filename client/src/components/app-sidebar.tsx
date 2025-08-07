"use client";

import * as React from "react";
import {
  Settings,
  Bot,
  Database,
  Link,
  MessageSquare,
  Mail,
  FlaskConical,
  Target,
  TrendingUp,
  BarChart3,
  PlayCircle,
  FileText,
  Activity,
  Users,
  ExternalLink,
  BookOpen,
  Globe,
} from "lucide-react";

import { NavMain } from "@/components/nav-main";
import { NavDocuments } from "@/components/nav-documents";
import { NavSecondary } from "@/components/nav-secondary";
import { NavSteps } from "@/components/nav-steps";
import { NavUser } from "@/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const data = {
  user: {
    name: "Developer",
    email: "dev@databricks.com",
    avatar: "/avatars/assistant.png",
  },
  navMain: [
    // {
    //   title: "Chat Assistant",
    //   value: "chat",
    //   icon: MessageSquare,
    // },

    {
      title: "Sales email generator",
      value: "email",
      icon: Mail,
    },
  ],
  mlflowSteps: [
    {
      title: "Demo Overview",
      value: "demo-overview",
      icon: PlayCircle,
      description: "Introduction",
    },
    {
      title: "Observe with tracing",
      value: "step1-tracing",
      icon: FlaskConical,
      description: "Capture every app execution and attach user feedback",
    },
    {
      title: "Create quality metrics",
      value: "step2-evaluation",
      icon: Target,
      description:
        "Create automated quality metrics that align with domain experts",
    },
    {
      title: "Find & fix quality issues",
      value: "step3-improvement",
      icon: TrendingUp,
      description: "Use production traces to test and improve quality",
    },

    {
      title: "Production Monitoring",
      value: "step5-monitoring",
      icon: Activity,
      description: "Continuously monitor GenAI quality in production",
    },
    {
      title: "Human Review",
      value: "step6-human-review",
      icon: Users,
      description:
        "Collect expert feedback to improve GenAI quality through structured labeling",
    },
    {
      title: "Link to business KPIs",
      value: "step4-kpis",
      icon: BarChart3,
      description:
        "Link GenAI usage data to business KPIs to show ROI from GenAI apps",
    },
    // {
    //   title: "Step 5: Prompt Registry",
    //   value: "step5-prompt-registry",
    //   icon: FileText,
    //   description: "Centralized prompt management and version control",
    // },
    // {
    //   title: "Prompt Registry Demo",
    //   value: "prompt-registry",
    //   icon: PlayCircle,
    //   description: "Interactive prompt management and A/B testing demo",
    // },
  ],
  navSecondary: [
    {
      title: "Settings",
      url: "#",
      icon: Settings,
    },
  ],
  documents: [
    {
      name: "Agent Configuration",
      url: "#",
      icon: Bot,
    },
    {
      name: "MLFlow Experiment",
      url: "#",
      icon: Database,
    },
    {
      name: "API Endpoints",
      url: "#",
      icon: Link,
    },
  ],
  resources: [
    {
      title: "MLflow Documentation",
      url: "https://docs.databricks.com/aws/en/mlflow3/genai/",
      icon: BookOpen,
    },
    {
      title: "MLflow Website",
      url: "https://mlflow.org/",
      icon: Globe,
    },
    {
      title: "MLflow Quickstart",
      url: "https://docs.databricks.com/aws/en/mlflow3/genai/getting-started",
      icon: ExternalLink,
    },
  ],
};

export function AppSidebar({
  children,
  selectedAgent,
  setSelectedAgent,
  setMessages,
  experiment,
  experimentIsLoading,
  isStreamingEnabled,
  setIsStreamingEnabled,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  children?: React.ReactNode;
  selectedAgent: string;
  setSelectedAgent: (value: string) => void;
  setMessages: (value: any) => void;
  experiment: any;
  experimentIsLoading: boolean;
  isStreamingEnabled: boolean;
  setIsStreamingEnabled: (value: boolean) => void;
}) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild size="lg">
              <a href="#">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <Bot className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">
                    MLflow 3.0 GenAI Demo
                  </span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {children}

        <NavSteps items={data.mlflowSteps} />
        <NavMain items={data.navMain} label="Use the sample app" />
        <NavDocuments
          // selectedAgent={selectedAgent}
          // setSelectedAgent={setSelectedAgent}
          // setMessages={setMessages}
          experiment={experiment}
          experimentIsLoading={experimentIsLoading}
          // isStreamingEnabled={isStreamingEnabled}
          // setIsStreamingEnabled={setIsStreamingEnabled}
        />
        <NavSecondary items={data.resources} label="Get started on your own" />
      </SidebarContent>
      {/* <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter> */}
    </Sidebar>
  );
}
