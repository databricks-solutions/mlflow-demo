import React from "react";
import { useNavigate } from "react-router-dom";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { MarkdownContent } from "@/components/markdown-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FlaskConical,
  Target,
  TrendingUp,
  BarChart3,
  Activity,
  UserCheck,
  ArrowRight,
  AlertCircle,
  DollarSign,
  Users,
  Clock,
} from "lucide-react";
import { getPathFromViewType, ViewType } from "@/routes";

const introContent = `
Organizations are rapidly adopting GenAI, but **the real challenge isn't just deploying AI agents—it's building high-quality agents that deliver reliable, domain-specific value**.

**The key to high-quality agents is rigorous evaluation and continuous monitoring** to iteratively improve your system. **MLflow has research-backed methods baked into the underlying product** that make **domain-specific evaluation dramatically easier**. You don't need expensive fine-tuning pipelines or hundreds of labeled examples—**MLflow enables you to align judges and optimize prompts with as few as 2-10 expert feedback examples**, learning from the dense information in natural language feedback rather than relying solely on scalar labels.

**MLflow 3.0+ provides the complete toolkit**: **proper evaluation frameworks** and **ongoing monitoring** to systematically improve agent quality through domain expert feedback—**at up to 100× lower latency and 10× lower cost** compared to traditional optimization approaches.

![MLflow SLDC](https://i.imgur.com/T0uM1No.gif)

## What you will see

- **Implement MLflow Tracing** to observe and debug your GenAI agent behavior
- **Create custom LLM judges** that align with your **domain-specific quality standards** and business requirements
- **Collect ground truth labels** from domain experts via MLflow Labeling Sessions
- **Automatically align judges to expert feedback** using SIMBA/MemAlign optimizers—**scaling domain expertise without manual tuning**
- **Optimize prompts automatically** with GEPA guided by aligned judges—**achieving competitive or better quality without brittle manual engineering**
- **Build self-optimizing systems** where expert feedback continuously improves AI quality

![MLflow GenAI Demo](https://i.imgur.com/MXhaayF.gif)
`;

const businessChallenges = `
## NFL Defensive Coordinator Assistant

We'll build a **self-optimizing assistant** that helps defensive coordinators analyze opponent tendencies and plan game strategies. The agent uses **Unity Catalog tools** to query play-by-play data and provides contextualized recommendations.

### The Challenge

**Generic LLM judges** and **static, verbose prompts** fail to capture domain-specific nuance. The LLM judge isn't wrong per se—it's evaluating against **generic best practices**. But SMEs are evaluating against **domain-specific standards**, shaped by business objectives, internal policies, and hard-won lessons from production incidents.

Determining what makes an NFL defensive analysis "good" requires deep football knowledge: coverage schemes, formation tendencies, situational context, and strategic value—**knowledge unlikely to be part of an LLM's background knowledge**.

**Two critical problems prevent quality at scale:**
1. **Generic evaluations** miss the specialized expertise that defines quality in your domain
2. **Prompt engineering is brittle and doesn't scale**—you'll quickly hit context limits, introduce contradictions, and spend weeks on edge cases

### The Solution

A **self-optimizing architecture** where **coaching expertise continuously improves AI quality**:

![DC Assistant Solution Architecture](/dc-assistant-solution.png)

- **Coaches provide feedback** on agent outputs via **MLflow Labeling Sessions**
- **MLflow aligns judges** to match coaching preferences using **SIMBA/MemAlign optimizer**—learning from **small amounts of natural language feedback** instead of hundreds of labels
- **System automatically optimizes prompts** guided by aligned judges using **GEPA optimizer**
- **Agent improves without manual prompt engineering**—achieving competitive or better quality at **up to 100× lower latency and 10× lower cost**

This demo shows how to build **AI systems that encode domain expertise** and **improve continuously** as they're used.
`;

export function DemoOverview() {
  const navigate = useNavigate();
  const steps = [
    {
      number: 1,
      title: "Observe DC Analysis",
      icon: FlaskConical,
      description:
        "Capture agent behavior with MLflow tracing: see tool calls, data queries, and final recommendations",
      keyFeatures: ["MLflow Tracing", "Tool call tracking", "Span visualization"],
    },
    {
      number: 2,
      title: "Evaluate Recommendations",
      icon: Target,
      description:
        "Create domain-specific LLM judges for defensive coordinator recommendations: relevance, football language, strategic value",
      keyFeatures: ["Custom judges", "Domain-specific criteria", "Third-party judges"],
    },
    {
      number: 3,
      title: "Collect Ground Truth Labels",
      icon: TrendingUp,
      description:
        "Collect expert coaching feedback via MLflow Labeling Sessions to create labeled datasets for judge alignment",
      keyFeatures: ["Labeling Sessions", "Expert feedback", "Trace linking"],
    },
    {
      number: 4,
      title: "Align Judges to Experts",
      icon: BarChart3,
      description:
        "Automatically calibrate judges to match coaching expertise using SIMBA/MemAlign—scale domain knowledge without manual tuning",
      keyFeatures: ["SIMBA/MemAlign optimizer", "Judge alignment", "Small data learning"],
    },
    {
      number: 5,
      title: "Optimize Prompts",
      icon: Activity,
      description:
        "Automatically improve prompts with GEPA optimizer guided by aligned judges—no brittle manual prompt engineering",
      keyFeatures: ["GEPA optimizer", "Automatic optimization", "Prompt registry"],
    },
    {
      number: 6,
      title: "Continuous Loop",
      icon: Users,
      description:
        "Self-optimizing cycle: coaches use the assistant, provide feedback, judges align, prompts improve automatically—continuous quality improvement",
      keyFeatures: ["Full automation", "Continuous improvement", "Compound gains"],
    },
  ];

  const introSection = (
    <div className="space-y-6">
      <MarkdownContent content={introContent} />
    </div>
  );

  const codeSection = (
    <div className="space-y-6">
      <MarkdownContent content={businessChallenges} />

      {/* <MarkdownContent content="" /> */}

      {/* Business Impact Dashboard */}
      {/* <BusinessDashboard /> */}
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-xl font-semibold mb-2">
          Interactive Demo Walkthrough
        </h3>
        <p className="text-muted-foreground mb-6">
          Follow these steps to learn <strong>MLflow's approach to building high-quality agents</strong> through
          <strong>proper evaluation</strong> and <strong>continuous monitoring</strong>.
        </p>
      </div>

      {/* Step Cards */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <Card key={index} className="hover:shadow-md transition-shadow">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                    <step.icon className="h-6 w-6 text-primary" />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    {/* <Badge variant="outline">{step.number}</Badge> */}
                    <h4 className="text-lg font-semibold">{step.title}</h4>
                  </div>

                  <p className="text-muted-foreground mb-3">
                    {step.description}
                  </p>

                  <div className="flex flex-wrap gap-2">
                    {step.keyFeatures.map((feature, featureIndex) => (
                      <Badge
                        key={featureIndex}
                        variant="secondary"
                        className="text-xs"
                      >
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="flex-shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const routes: Record<number, ViewType> = {
                        1: "step1-tracing",
                        2: "step2-evaluation",
                        3: "step3-improvement",
                        4: "step4-kpis",
                        5: "step5-monitoring",
                        6: "step6-human-review",
                      };
                      const viewType =
                        routes[step.number] || "step1-tracing";
                      navigate(getPathFromViewType(viewType));
                    }}
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Prerequisites */}
      <Card className="border-orange-200 bg-orange-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-orange-800">
            <AlertCircle className="h-5 w-5" />
            Prerequisites & Setup
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-orange-700 space-y-2">
            <p>
              <strong>No setup required!</strong> This is a fully interactive
              demo with:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Pre-configured MLflow experiment with sample traces</li>
              <li>Working DC Assistant with NFL play-by-play data</li>
              <li>Live evaluation metrics and judge examples</li>
              <li>Coaching feedback and prompt optimization workflows</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Get Started */}
      <div className="text-center">
        <Button
          size="lg"
          className="px-8"
          onClick={() => navigate(getPathFromViewType("dc-assistant"))}
        >
          Try the DC Assistant
          <ArrowRight className="ml-2 h-5 w-5" />
        </Button>
        <p className="text-sm text-muted-foreground mt-2">
          Ask questions about opponent tendencies and see MLflow tracing in action
        </p>
      </div>
    </div>
  );

  const descriptionContent =
    "This interactive demo showcases how to use MLflow to build high-quality GenAI applications that follow software development best practices: unit tests and production monitoring that measure **quality**.";

  return (
    <div className="w-full h-full flex flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 p-6">
        <h1 className="text-3xl font-bold tracking-tight">
          Self-Optimizing AI: NFL Defensive Coordinator Assistant
        </h1>
        <p className="text-muted-foreground mt-2">
          Learn how to build <strong>high-quality AI agents</strong> that <strong>continuously improve through domain expert feedback</strong>.
          This demo shows MLflow's full optimization cycle: <strong>observability with tracing</strong>, <strong>evaluation with custom LLM judges</strong>,
          <strong>judge alignment to expert feedback</strong>, and <strong>automatic prompt optimization</strong>.
        </p>
      </div>

      {/* Main Content */}
      <ScrollArea className="flex-1">
        <div className="p-6 space-y-8">
          {/* Introduction Section */}
          <Card>
            <CardHeader>
              <CardTitle>Introduction</CardTitle>
            </CardHeader>
            <CardContent>{introSection}</CardContent>
          </Card>

          <Separator />

          {/* Business Impact Section */}
          <Card>
            <CardHeader>
              <CardTitle>Use case overview</CardTitle>
            </CardHeader>
            <CardContent>{codeSection}</CardContent>
          </Card>

          <Separator />

          {/* Demo Section */}
          <Card>
            <CardHeader>
              <CardTitle>Demo</CardTitle>
            </CardHeader>
            <CardContent>{demoSection}</CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
