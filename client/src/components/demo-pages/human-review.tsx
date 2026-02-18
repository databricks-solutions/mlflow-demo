import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { NotebookReference } from "@/components/notebook-reference";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Shield,
  Eye,
  RefreshCw,
} from "lucide-react";

const introContent = `
# Production Monitoring: Closing the Loop

You've aligned judges, optimized prompts, and collected expert labels. Now you need **continuous monitoring** to keep quality high as production traffic evolves.

## How It Works

MLflow 3 lets you **register scorers directly to an experiment** and run them automatically against production traces with configurable sampling rates. Assessments are attached to the traces they evaluate — everything lives in one place.

Separately, you can **export traces to Unity Catalog** (Public Preview) by linking an experiment to a UC schema via **set_experiment_trace_location()**. This creates three OpenTelemetry-format Delta tables (spans, logs, metrics) in your schema — in our case under **nethra_ranganathan.mlflow_dc_2**. Once linked, every trace and scorer assessment is SQL-queryable, ideal for dashboards, trend analysis, and feeding low-scoring traces back into labeling sessions.

## The Monitoring Loop
1. **Register & start scorers** with sampling rates (safety at 100%, expensive judges at 5-20%)
2. **Scorers run automatically** on production traces — assessments attach to the trace
3. **Query the trace table** for trends, failing traces, drift detection
4. **Flag low-scoring traces** → labeling sessions → re-align judges → re-optimize prompts
5. **Backfill** new scorers on historical traces when you add new quality dimensions

Up to 20 scorers can run per experiment. Use **backfill_scorers()** to retroactively apply new scorers.
`;

const setupMonitoringCode = `import mlflow
from mlflow.entities import UCSchemaLocation
from mlflow.genai.scorers import Safety, Guidelines
from mlflow.genai.scorer_utils import ScorerSamplingConfig

# 1. Export traces to Unity Catalog (Public Preview)
#    Creates 3 OTEL Delta tables: spans, logs, metrics
set_experiment_trace_location(
    location=UCSchemaLocation(
        catalog_name="nethra_ranganathan",
        schema_name="mlflow_dc_2"
    ),
    experiment_id=EXPERIMENT_ID,
)

# 2. Register scorers to the experiment (up to 20)
safety_scorer = Safety()
safety_scorer.register(
    name="safety_monitor",
    experiment_id=EXPERIMENT_ID,
    sampling_config=ScorerSamplingConfig(sample_rate=1.0),  # 100%
)

football_language = Guidelines(
    name="football_language",
    guidelines="Use proper football terminology..."
)
football_language.register(
    name="football_language_monitor",
    experiment_id=EXPERIMENT_ID,
    sampling_config=ScorerSamplingConfig(sample_rate=0.15),  # 15%
)

# 3. Start the scorers — they run on every new trace
safety_scorer.start()
football_language.start()`;

const manageScorerCode = `from mlflow.genai.scorer_utils import list_scorers, get_scorer, delete_scorer

# List all registered scorers for this experiment
scorers = list_scorers(experiment_id=EXPERIMENT_ID)
for s in scorers:
    print(f"{s.name}  rate={s.sampling_config.sample_rate}  status={s.status}")

# Update sampling rate on an existing scorer
scorer = get_scorer(name="football_language_monitor", experiment_id=EXPERIMENT_ID)
scorer.update(sampling_config=ScorerSamplingConfig(sample_rate=0.30))  # increase to 30%

# Stop a scorer temporarily (e.g., during maintenance)
scorer.stop()

# Restart when ready
scorer.start()

# Delete a scorer you no longer need
delete_scorer(name="old_scorer", experiment_id=EXPERIMENT_ID)`;

const queryTraceTableCode = `# Query the OTEL trace tables in Unity Catalog
# set_experiment_trace_location() creates these automatically:
#   - mlflow_experiment_trace_otel_spans
#   - mlflow_experiment_trace_otel_logs
#   - mlflow_experiment_trace_otel_metrics

UC_SCHEMA = "nethra_ranganathan.mlflow_dc_2"

# Trace volume over the last 30 days
trace_trends = spark.sql(f"""
SELECT
    DATE(start_time) as date,
    COUNT(DISTINCT trace_id) as trace_count
FROM {UC_SCHEMA}.mlflow_experiment_trace_otel_spans
WHERE start_time >= CURRENT_DATE - INTERVAL 30 DAYS
GROUP BY DATE(start_time)
ORDER BY date
""")

# Join spans with scorer assessments to find low-scoring traces
# (scorer results are logged as OTEL span attributes)
failing_traces = spark.sql(f"""
SELECT trace_id, start_time, attributes
FROM {UC_SCHEMA}.mlflow_experiment_trace_otel_spans
WHERE start_time >= CURRENT_DATE - INTERVAL 7 DAYS
ORDER BY start_time DESC
LIMIT 20
""")`;

const backfillCode = `from mlflow.genai.scorer_utils import backfill_scorers

# Backfill a new scorer on historical traces
# Useful when you add a new quality dimension after launch
backfill_scorers(
    scorer_names=["strategic_soundness_monitor"],
    experiment_id=EXPERIMENT_ID,
)`;

export function HumanReview() {
  const [mockMetrics] = React.useState({
    avgFootballLanguage: 0.78,
    avgDataGrounded: 0.82,
    avgStrategicSoundness: 0.75,
    failureRate: 0.08,
    tracesMonitored: 1247,
    trendDirection: "stable" as "up" | "down" | "stable",
  });

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="1. Register & start scorers on an experiment"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring"
      >
        <CodeSnippet code={setupMonitoringCode} title="Register Production Scorers" />
      </CollapsibleSection>

      <CollapsibleSection
        title="2. Manage scorers (list, update, stop)"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring"
      >
        <CodeSnippet code={manageScorerCode} title="Manage Registered Scorers" />
      </CollapsibleSection>

      <CollapsibleSection
        title="3. Query the trace archive table"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring#view-results"
      >
        <CodeSnippet code={queryTraceTableCode} title="Query Trace Table" />
      </CollapsibleSection>

      <CollapsibleSection
        title="4. Backfill new scorers on historical traces"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/production-monitoring"
      >
        <CodeSnippet code={backfillCode} title="Backfill Scorers" />
      </CollapsibleSection>

      <NotebookReference
        notebookPath="mlflow_demo/notebooks/6_production_monitoring.ipynb"
        notebookName="6_production_monitoring"
        description="Set up production monitoring with registered scorers and trace archival"
      />
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      {/* Monitoring Overview */}
      <Card className="border-2 border-blue-200 bg-blue-50/30 dark:border-blue-800 dark:bg-blue-950/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-900 dark:text-blue-100">
            <Activity className="h-5 w-5" />
            Production Monitoring Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: Eye, iconClass: "text-blue-600", valueClass: "text-blue-600", value: mockMetrics.tracesMonitored, label: "Traces Monitored (7d)" },
              { icon: CheckCircle2, iconClass: "text-green-600", valueClass: "text-green-600", value: `${(mockMetrics.avgFootballLanguage * 100).toFixed(0)}%`, label: "Avg Football Language" },
              { icon: Shield, iconClass: "text-purple-600", valueClass: "text-purple-600", value: `${(mockMetrics.avgDataGrounded * 100).toFixed(0)}%`, label: "Avg Data Grounded" },
              { icon: AlertTriangle, iconClass: "text-orange-600", valueClass: "text-orange-600", value: `${(mockMetrics.failureRate * 100).toFixed(1)}%`, label: "Failure Rate" },
            ].map(({ icon: Icon, iconClass, valueClass, value, label }) => (
              <div key={label} className="text-center p-3 border rounded-lg bg-white dark:bg-gray-900">
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Icon className={`h-4 w-4 ${iconClass}`} />
                  <div className={`text-2xl font-bold ${valueClass}`}>{value}</div>
                </div>
                <div className="text-xs text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>

          <div className="p-4 bg-white dark:bg-gray-900 rounded-lg border">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-sm">Quality Trends (30 days)</h4>
              <Badge variant="outline" className="text-green-600 border-green-600">
                {mockMetrics.trendDirection === "up" && <TrendingUp className="h-3 w-3 mr-1" />}
                {mockMetrics.trendDirection === "down" && <TrendingDown className="h-3 w-3 mr-1" />}
                {mockMetrics.trendDirection === "stable" && <Activity className="h-3 w-3 mr-1" />}
                {mockMetrics.trendDirection.toUpperCase()}
              </Badge>
            </div>
            <div className="space-y-3">
              {[
                { label: "Football Language Score", value: mockMetrics.avgFootballLanguage },
                { label: "Data Grounded Score", value: mockMetrics.avgDataGrounded },
                { label: "Strategic Soundness Score", value: mockMetrics.avgStrategicSoundness },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span>{label}</span>
                    <span className="font-medium">{(value * 100).toFixed(0)}%</span>
                  </div>
                  <Progress value={value * 100} className="h-2" />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Continuous Improvement Loop — condensed */}
      <Card className="border-2 border-green-200 bg-green-50/30 dark:border-green-800 dark:bg-green-950/20">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-green-900 dark:text-green-100 text-base">
            <RefreshCw className="h-5 w-5" />
            The Continuous Improvement Loop
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { n: "1", title: "Low scores detected", desc: "Scorer flags failing traces" },
              { n: "2", title: "Labeling session", desc: "SMEs review flagged traces" },
              { n: "3", title: "Re-align judges", desc: "Run alignment with new labels" },
              { n: "4", title: "Re-optimize prompts", desc: "GEPA with refined judges" },
              { n: "5", title: "Deploy & monitor", desc: "Cycle repeats automatically" },
              { n: "6", title: "Backfill", desc: "New scorers on historical traces" },
            ].map(({ n, title, desc }) => (
              <div key={n} className="flex gap-2 items-start">
                <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center text-xs font-semibold text-green-700 dark:text-green-300 flex-shrink-0">
                  {n}
                </div>
                <div>
                  <p className="font-semibold text-xs text-green-900 dark:text-green-100">{title}</p>
                  <p className="text-xs text-green-800 dark:text-green-200">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <StepLayout
      title="Production Monitoring & Continuous Improvement"
      description="Close the loop with automated quality monitoring and continuous optimization"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
