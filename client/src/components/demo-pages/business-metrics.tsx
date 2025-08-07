import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  ExternalLink,
  BarChart3,
  DollarSign,
  Users,
  Clock,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { NotebookReference } from "@/components/notebook-reference";

const introContent = `
# Linking Technical Metrics to Business KPIs

The ultimate goal of GenAI optimization is business impact. Since MLflow is part of the Databricks platform, all trace and evaluation data can be synced to a Delta Table.

This lets your Business Analysts who only know SQL leverage trace and evaluation data for analytics and business processes, linking GenAI interactions to business KPIs to create performance dashboards, reports, and queries with Databricks AI/BI and SQL that show the ROI of your GenAI apps.

![demo-kpis-uc](https://i.imgur.com/tz6CCFL.gif)
`;

export function BusinessMetrics() {
  const [selectedTimeframe, setSelectedTimeframe] = React.useState("30d");

  // Real data from WORKING_DASH_CODE analysis
  const kpiData = {
    "7d": { revenue: 1800000, responseRate: 21.2, timeSaved: 61, roi: 3770 },
    "30d": { revenue: 7220000, responseRate: 21.2, timeSaved: 182, roi: 15086 },
    "90d": { revenue: 7220000, responseRate: 21.2, timeSaved: 182, roi: 15086 },
  };

  const introSection = <MarkdownContent content={introContent} />;

  const demoSection = (
    <div className="space-y-6">
      {/* <NotebookReference
        notebookPath="mlflow_demo/notebooks/6_business_metrics.ipynb"
        notebookName="6_business_metrics.ipynb"
        description="Connect GenAI quality metrics to business outcomes and calculate ROI"
      /> */}

      <MarkdownContent content="The dashboard below shows an illustrative example of what could be built by joining your MLflow Trace data (that is available in Unity Catalog) with other data already available in your UC.  Here, we demonstrate linking actual email replies to the MLflow traces." />

      {/* <Card>
        <CardHeader>
          <CardTitle>📊 Production Query Results</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm space-y-2">
            <div>
              <strong>Query 1 (Executive KPIs):</strong> AI vs Manual email
              performance comparison
            </div>
            <div>
              <strong>Query 4 (Quality Impact):</strong> Business outcomes by
              quality score buckets (8.0+, 6.0-8.0, {"<"}6.0)
            </div>
            <div>
              <strong>Query 5 (Sales Rep Performance):</strong> Individual rep
              improvements ranked by revenue
            </div>
            <div>
              <strong>Query 10 (Cost Analysis):</strong> Cost per email,
              response, meeting, and deal metrics
            </div>
            <div className="text-muted-foreground mt-2">
              All data reflects actual production analytics framework with real
              trace IDs and business outcomes.
            </div>
          </div>
        </CardContent>
      </Card> */}

      {/* MLflow Trace Examples */}
      {/* <Card>
        <CardHeader>
          <CardTitle>MLflow Trace → Business Outcome Examples</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm font-mono">
            <div className="p-3 border rounded bg-green-50">
              <div className="font-medium text-green-800">
                Perfect Quality Score Example:
              </div>
              <div>Trace ID: tr-2614e1880d674cd0a16648b808154e67</div>
              <div>
                Quality Scores: Accuracy: 1.0 | Relevance: 1.0 | Personalized:
                1.0 | Safety: 1.0
              </div>
              <div className="text-green-700 font-medium">
                → Result: Response ✓ | Meeting ✓ | Deal Closed ✓ | Revenue:
                $250,000
              </div>
            </div>
            <div className="p-3 border rounded bg-red-50">
              <div className="font-medium text-red-800">
                Poor Quality Score Example:
              </div>
              <div>Trace ID: tr-b0e7233d2f564746b20b42aee199c67d</div>
              <div>
                Quality Scores: Accuracy: 0.0 | Relevance: 0.0 | Personalized:
                0.0 | Safety: 1.0
              </div>
              <div className="text-red-700 font-medium">
                → Result: No Response ✗ | No Meeting ✗ | No Deal ✗ | Revenue: $0
              </div>
            </div>
          </div>
        </CardContent>
      </Card> */}

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold">$7.22M</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +1,197% vs manual
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Response Rate
                </p>
                <p className="text-2xl font-bold">21.2%</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +5.8 pts vs manual
                </p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Time Saved
                </p>
                <p className="text-2xl font-bold">182h</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  182 hours total
                </p>
              </div>
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">ROI</p>
                <p className="text-2xl font-bold">15,086%</p>
                <p className="text-xs text-green-600 flex items-center mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  vs $479 investment
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quality Score Impact Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>MLflow Quality Score Business Impact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 border rounded bg-green-50">
                <div>
                  <div className="font-medium">High Quality (8.0-10.0)</div>
                  <div className="text-sm text-muted-foreground">
                    Response: 26.5% • Meeting: 21.3% • Avg Deal: $31K
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="default" className="bg-green-600">
                    $4.8M Revenue
                  </Badge>
                  <div className="text-sm text-muted-foreground">
                    Best Performance
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded bg-blue-50">
                <div>
                  <div className="font-medium">Medium Quality (6.0-8.0)</div>
                  <div className="text-sm text-muted-foreground">
                    Response: 22.4% • Meeting: 10.3% • Avg Deal: $16K
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="secondary">$1.9M Revenue</Badge>
                  <div className="text-sm text-muted-foreground">
                    Good Performance
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 border rounded bg-gray-50">
                <div>
                  <div className="font-medium">Low Quality (0.0-6.0)</div>
                  <div className="text-sm text-muted-foreground">
                    Response: 12.9% • Meeting: 10.3% • Avg Deal: $5K
                  </div>
                </div>
                <div className="text-right">
                  <Badge variant="outline">$0.6M Revenue</Badge>
                  <div className="text-sm text-muted-foreground">
                    Needs Improvement
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Sales Rep Success Stories */}
        <Card>
          <CardHeader>
            <CardTitle>Top Sales Rep Success Stories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="text-center p-3 border rounded bg-green-50">
                  <div className="text-lg font-bold text-green-600">
                    Peter Thompson
                  </div>
                  <div className="text-sm text-muted-foreground">
                    +8.6% Response Rate • +$735K Revenue
                  </div>
                </div>
                <div className="text-center p-3 border rounded bg-blue-50">
                  <div className="text-lg font-bold text-blue-600">
                    Emily White
                  </div>
                  <div className="text-sm text-muted-foreground">
                    +21.5% Response Rate • +$787.5K Revenue
                  </div>
                </div>
                <div className="text-center p-3 border rounded bg-purple-50">
                  <div className="text-lg font-bold text-purple-600">
                    Oliver King
                  </div>
                  <div className="text-sm text-muted-foreground">
                    +2.7% Response Rate • +$500K Revenue
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>AI vs Manual Response Rate</span>
                  <span>21.2% vs 15.4%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: "42%" }}
                  ></div>
                </div>

                <div className="flex justify-between text-sm">
                  <span>Total Emails Analyzed</span>
                  <span>543 records</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>

                <div className="flex justify-between text-sm">
                  <span>Sales Reps Improved</span>
                  <span>42 analyzed</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Production SQL Query Results */}
      <Card>
        <CardHeader>
          <CardTitle>AI vs Manual Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Metric Category</th>
                  <th className="text-left p-2">Total Emails</th>
                  <th className="text-left p-2">Response Rate</th>
                  <th className="text-left p-2">Total Revenue</th>
                  <th className="text-left p-2">Total Cost</th>
                  <th className="text-left p-2">ROI Ratio</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b bg-green-50">
                  <td className="p-2 font-medium">AI Generated Emails</td>
                  <td className="p-2">387</td>
                  <td className="p-2">21.2%</td>
                  <td className="p-2">$7,220,000</td>
                  <td className="p-2">$479.00</td>
                  <td className="p-2 font-bold text-green-600">586x</td>
                </tr>
                <tr className="border-b bg-gray-50">
                  <td className="p-2 font-medium">Manual Emails</td>
                  <td className="p-2">156</td>
                  <td className="p-2">15.4%</td>
                  <td className="p-2">$557,500</td>
                  <td className="p-2">$0.00</td>
                  <td className="p-2">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Cost Analysis Query Results */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Efficiency Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 border rounded">
              <div className="text-lg font-bold text-blue-600">$1.24</div>
              <div className="text-sm text-muted-foreground">
                Cost per Email
              </div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-lg font-bold text-green-600">$5.84</div>
              <div className="text-sm text-muted-foreground">
                Cost per Response
              </div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-lg font-bold text-purple-600">$17.32</div>
              <div className="text-sm text-muted-foreground">
                Cost per Meeting
              </div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-lg font-bold text-orange-600">$69.29</div>
              <div className="text-sm text-muted-foreground">Cost per Deal</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Success Stories */}
      <Card>
        <CardHeader>
          <CardTitle>Implementation Success Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 border rounded-lg bg-green-50">
              <div className="text-3xl font-bold text-green-600">586%</div>
              <div className="text-sm text-muted-foreground">Overall ROI</div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-blue-50">
              <div className="text-3xl font-bold text-blue-600">5.8%</div>
              <div className="text-sm text-muted-foreground">
                Response Rate Increase
              </div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-purple-50">
              <div className="text-3xl font-bold text-purple-600">182</div>
              <div className="text-sm text-muted-foreground">Hours Saved</div>
            </div>
            <div className="text-center p-4 border rounded-lg bg-orange-50">
              <div className="text-3xl font-bold text-orange-600">$7.22M</div>
              <div className="text-sm text-muted-foreground">
                Revenue Generated
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <StepLayout
      title="Link to business KPIs"
      intro={introSection}
      demoSection={demoSection}
    />
  );
}
