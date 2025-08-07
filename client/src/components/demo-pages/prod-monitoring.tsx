import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { useQueryExperiment } from "@/queries/useQueryTracing";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { NotebookReference } from "@/components/notebook-reference";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ExternalLink,
  Activity,
  Shield,
  Target,
  Clock,
  Database,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Settings,
} from "lucide-react";

const introContent = `
# Production Monitoring: Automated Quality at Scale

MLflow's production monitoring automatically runs quality assessments on a sample of your production traffic, ensuring your GenAI app maintains high quality standards without manual intervention.  MLflow lets you use the **same** metrics you defined for offline evaluation in production, enabling you to have consistent quality evaluation across your entire application lifecycle - dev to prod.

Key benefits:
- **Automated evaluation** - Run LLM judges on production traces with configurable sampling rates
- **Continuous quality assessment** - Monitor quality metrics in real-time without disrupting user experience
- **Cost-effective monitoring** - Smart sampling strategies to balance coverage with computational cost

Production monitoring enables you to deploy confidently, knowing that you will proactively detect issues so you can address them before they cause a major impact to your users.

![monitoring-overview](https://i.imgur.com/wv4p562.gif)
`;

const setupMonitoringCode = `
from mlflow.genai.scorers import Guidelines

# Tone of voice Guideline - Ensure professional tone
tone = Guidelines(
  name='tone',
  guidelines="""The response maintains a professional tone.""")

tone.register()
tone.start(sampling_config=ScorerSamplingConfig(sample_rate=1)) # run on 100% of productions traces
print('✅ Tone scorer registered and started!')
`;

export function MonitoringDemo() {
  const { data: experiment, isLoading: experimentIsLoading } =
    useQueryExperiment();

  const [monitoringConfig, setMonitoringConfig] = React.useState({
    catalogName: "workspace",
    schemaName: "genai_monitoring",
    sampleRate: 1.0,
    costOptimization: true,
  });

  const [judges, setJudges] = React.useState([
    {
      name: "Safety",
      type: "builtin",
      enabled: true,
      sampleRate: 1.0,
      description: "Detect harmful or toxic content",
    },
    {
      name: "Relevance to Query",
      type: "builtin",
      enabled: true,
      sampleRate: 1.0,
      description: "Ensure responses address user queries",
    },
    {
      name: "Groundedness",
      type: "builtin",
      enabled: true,
      sampleRate: 0.4,
      description: "Verify responses are grounded in provided context",
    },
    {
      name: "Professionalism",
      type: "custom",
      enabled: true,
      sampleRate: 0.8,
      description: "Maintain professional communication standards",
    },
    {
      name: "Brand Voice",
      type: "custom",
      enabled: false,
      sampleRate: 0.6,
      description: "Align with company brand and tone",
    },
  ]);

  const [monitoringStatus, setMonitoringStatus] = React.useState("active");
  const [mockMetrics, setMockMetrics] = React.useState({
    tracesMonitored: 1247,
    avgSafetyScore: 0.94,
    avgProfessionalismScore: 0.87,
    avgGroundedness: 0.91,
    alerts: 2,
    costSavings: "34%",
  });

  const handleJudgeToggle = (index: number) => {
    const newJudges = [...judges];
    newJudges[index].enabled = !newJudges[index].enabled;
    setJudges(newJudges);
  };

  const handleSampleRateChange = (index: number, value: string) => {
    const newJudges = [...judges];
    newJudges[index].sampleRate = parseFloat(value);
    setJudges(newJudges);
  };

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="1. Setup Production Monitoring"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring"
      >
        <div className="space-y-4">
          <MarkdownContent content="Configure automated monitoring to run LLM judges on production traces. Smart sampling reduces costs while maintaining quality coverage." />
          <CodeSnippet
            code={setupMonitoringCode}
            title="Create External Monitor"
          />
        </div>
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/5_production_monitoring.ipynb"
        notebookName="5_production_monitoring"
        description="Learn how to set up and analyze production monitoring for continuous quality assessment"
      />
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="See the MLflow UI for production monitoring settings.  This demo has preconfigured monitoring for the email generator based on the metrics defined in the create quality metrics section." />
      <div className="flex gap-2 flex-wrap">
        <Button
          variant="open_mlflow_ui"
          size="lg"
          onClick={() =>
            window.open(
              experiment?.monitoring_url || (experimentIsLoading ? "#" : ""),
              "_blank",
            )
          }
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          Monitoring configuration
        </Button>
      </div>
    </div>
  );

  return (
    <StepLayout
      title="Production Monitoring"
      description="Continuously monitor GenAI quality in production"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
