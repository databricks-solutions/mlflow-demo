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
Delivering business value with GenAI requires answering these questions:
1. Is my agent producing accurate answers?
2. How do I improve my agent's accuracy?
3. Is my agent fast and cost effective?

We know how to deliver reliable software, but GenAI's non-deterministic nature makes it difficult to directly apply software development best practices:
1. User inputs evolve without warning
2. Human expertise required to assess output quality
3. Must trade-off between quality & cost/latency

MLflow enables you to apply software development best practices to evaluate and monitor GenAI application quality:

|Software|MLflow's solution for GenAI|
|-------|------|
|Write code & debug locally| - [possible without MLflow] Prompt engineer & vibe check |
|Unit tests & QA testing| - MLflow LLM judges to replicate human expertise to automatically assess output quality <br/> - MLflow Evaluation Datasets to use actual user inputs as test cases|
|Track versions using Git| - MLflow App Versioning to link Git commits to your quality evaluation and monitoring <br/> - MLflow Prompt Registry to enable prompt changes without re-deploying|
|Production telemetry|- MLflow Tracing to observe your GenAI app with monitoring to run evals <br/> - Monitoring to your LLM judges to assess quality in production <br/> - MLflow App Versioning to link Git commits to your GenAI app|

## What you will see

- **Implement MLflow Tracing** to observe and debug your GenAI app
- **Customize MLflow's LLM judges** to create quality evaluation criteria that align with business requirements and your domain expert's judgement
- **Create MLflow Evaluation Datasets** to curate production traces into test suites
- **Use MLflow's Evaluation SDK** to iteratively test changes and check for regressions
- **Use MLflow Prompt Registry and App Versioning** to link versions to quality evaluations
- **Use Databricks AI/BI** to link GenAI observability and evaluation metrics to business KPIs

![MLflow GenAI Demo](https://i.imgur.com/MXhaayF.gif)
`;

const businessChallenges = `
## Sales Email Generation

We'll create a sales email generation system that helps account managers create personalized customer emails.  The goal is to drive business KPIs such as sales efficiency, response rate, and revenue generated.
`;

export function DemoOverview() {
  const navigate = useNavigate();
  const steps = [
    {
      number: 1,
      title: "Observe with tracing",
      icon: FlaskConical,
      description:
        "Add observability to your GenAI app so you can see what's happening and collect user feedback",
      keyFeatures: [],
    },
    {
      number: 2,
      title: "Create quality metrics",
      icon: Target,
      description:
        "Scale your expert's judgment using MLflow's LLM judges to create automated quality metrics",
      keyFeatures: [],
    },
    {
      number: 3,
      title: "Find & fix quality issues",
      icon: TrendingUp,
      description:
        "Use production traces and actual user data with evaluation metrics to iteratively test quality fixes",
      keyFeatures: [],
    },
    {
      number: 4,
      title: "Production Monitoring",
      icon: Activity,
      description:
        "Monitor GenAI quality in production with intelligent sampling",
      keyFeatures: [],
    },
    {
      number: 5,
      title: "Human Review",
      icon: UserCheck,
      description:
        "Collect expert feedback through an intuitive UI to systematically improve GenAI quality",
      keyFeatures: [],
    },
    {
      number: 6,
      title: "Link to business KPIs",
      icon: BarChart3,
      description:
        "Create business dashboards and link to KPIs using MLflow data stored in Delta Tables",
      keyFeatures: [],
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
          Follow these steps to learn MLflow GenAI evaluation best practices
          through hands-on examples.
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
                      };
                      const viewType =
                        routes[step.number] || "step5-prompt-registry";
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
              <li>Pre-configured MLflow experiment with sample data</li>
              <li>Working email generation system with fake customer data</li>
              <li>Live evaluation metrics and evaluation examples</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Get Started */}
      <div className="text-center">
        <Button
          size="lg"
          className="px-8"
          onClick={() => navigate(getPathFromViewType("step1-tracing"))}
        >
          Start Step 1: Observe with Tracing
          <ArrowRight className="ml-2 h-5 w-5" />
        </Button>
        <p className="text-sm text-muted-foreground mt-2">
          Begin your MLflow GenAI evaluation journey
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
          MLflow GenAI Monitoring & Evaluation Demo
        </h1>
        <p className="text-muted-foreground mt-2">
          This interactive demo showcases how to use MLflow to build
          high-quality GenAI applications that follow software development best
          practices: unit tests and production monitoring that measure{" "}
          <b>quality</b>.
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
