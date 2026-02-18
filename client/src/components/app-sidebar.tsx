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
  Trophy,
  HelpCircle,
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
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
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
      title: "DC Assistant",
      value: "step1-tracing",
      icon: Trophy,
    },
  ],
  mlflowSteps: [
    {
      title: "Demo Overview",
      value: "demo-overview",
      icon: PlayCircle,
      description: "Introduction to DC Assistant optimization",
    },
    {
      title: "Observe DC Analysis",
      value: "step1-tracing",
      icon: FlaskConical,
      description: "Capture agent behavior with MLflow tracing",
    },
    {
      title: "Evaluate Recommendations",
      value: "step2-evaluation",
      icon: Target,
      description:
        "Create LLM judges for defensive coordinator recommendations",
    },
    {
      title: "Collect Ground Truth Labels",
      value: "step3-improvement",
      icon: TrendingUp,
      description: "Create labeled datasets through SME review sessions",
    },
    {
      title: "Align Judges to Experts",
      value: "step4-kpis",
      icon: BarChart3,
      description:
        "Calibrate judges to match coaching expertise with SIMBA/MemAlign",
    },
    {
      title: "Optimize Prompts",
      value: "step5-monitoring",
      icon: Activity,
      description: "Automatically improve prompts with GEPA optimizer",
    },
    {
      title: "Ongoing Monitoring",
      value: "step6-human-review",
      icon: Users,
      description:
        "Self-optimizing cycle from coach feedback to improved prompts",
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
        <NavMain items={data.navMain} label="Try the DC Assistant" />
        <NavDocuments
          // selectedAgent={selectedAgent}
          // setSelectedAgent={setSelectedAgent}
          // setMessages={setMessages}
          experiment={experiment}
          experimentIsLoading={experimentIsLoading}
          // isStreamingEnabled={isStreamingEnabled}
          // setIsStreamingEnabled={setIsStreamingEnabled}
        />
        <SidebarGroup>
          <SidebarGroupLabel>Have questions or feedback?</SidebarGroupLabel>
          <SidebarGroupContent>
            <p className="px-3 text-xs text-muted-foreground">
              Reach out to Nethra Ranganathan or Austin Choi
            </p>
          </SidebarGroupContent>
        </SidebarGroup>
        <NavSecondary items={data.resources} label="Get started on your own" />
      </SidebarContent>
      {/* <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter> */}
    </Sidebar>
  );
}
