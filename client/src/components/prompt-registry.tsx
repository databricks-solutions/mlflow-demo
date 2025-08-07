import React from "react";
import { StepLayout } from "@/components/step-layout";
import { CodeSnippet } from "@/components/code-snippet";
import { CollapsibleSection } from "@/components/collapsible-section";
import { MarkdownContent } from "@/components/markdown-content";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ExternalLink,
  Save,
  GitBranch,
  History,
  FileText,
  Play,
  Tag,
  Package,
} from "lucide-react";

const introContent = `
# MLflow Prompt Registry

The MLflow Prompt Registry provides centralized prompt management with version control for your GenAI applications:

- **Version Control** - Track prompt changes over time with Git-like versioning
- **Unity Catalog Integration** - Store and govern prompts in Unity Catalog schemas.  Share with others on your team or across your organization.
- **Alias Management** - Use aliases like "production" or "staging" to deploy prompt versions to production without redeploying the application

This demonstration shows how to create, version, and deploy prompts using MLflow's prompt registry.

![prompt-registry](https://i.imgur.com/6C1SsY4.gif)


`;

const createEditPromptsCode = `import mlflow
import mlflow

# Unity Catalog schema to store the prompt in
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Example prompt
prompt = """You are an expert sales communication assistant for CloudFlow Inc. Your task is to generate a personalized, professional follow-up email for our sales representatives to send to their customers at the end of the day.

## INPUT DATA
You will be provided with a JSON object containing:

{{my_data}}
... cut off ...
"""

mlflow.genai.register_prompt(
  name=f'{UC_CATALOG}.{UC_SCHEMA}.email_generation_demo',
  template=prompt,
  commit_message='Initial email generation template',
)
`;

const usePromptsProductionCode = `import mlflow

# Unity Catalog schema to store the prompt in
UC_CATALOG = os.environ.get('UC_CATALOG')
UC_SCHEMA = os.environ.get('UC_SCHEMA')

# Set an alias for the prompt version
mlflow.genai.set_prompt_alias(
  name=f'{UC_CATALOG}.{UC_SCHEMA}.email_generation_demo',
  alias='production',
  version='1',
)

# Use the prompt in your application

prompt_uri = f"prompts:/{UC_CATALOG}.{UC_SCHEMA}.email_generation_demo@production"

prompt = mlflow.genai.load_prompt(prompt_uri)

# Use the prompt in your application

my_data = "some data"

client.chat.completions.create(
    messages=[{"role": "user", "content": prompt.format(my_data=my_data)}],
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=2000,
)

`;

export function PromptRegistry() {
  const [selectedPrompt, setSelectedPrompt] = React.useState(
    "sales_email_generator",
  );
  const [selectedAlias, setSelectedAlias] = React.useState("production");
  const [promptVersion, setPromptVersion] = React.useState("v2");
  const [newAlias, setNewAlias] = React.useState("");
  const [commitMessage, setCommitMessage] = React.useState("");

  const promptVersions = [
    {
      version: "v1",
      description: "Initial version of sales email prompt",
      created: "2024-01-15",
      tags: { use_case: "email_generation", team: "sales" },
    },
    {
      version: "v2",
      description: "Added sender details and pain points, improved structure",
      created: "2024-01-18",
      tags: {
        use_case: "email_generation",
        team: "sales",
        improvement: "enhanced_personalization",
      },
    },
    {
      version: "v3",
      description: "Refined tone and added industry-specific language",
      created: "2024-01-20",
      tags: {
        use_case: "email_generation",
        team: "sales",
        improvement: "industry_focus",
      },
    },
  ];

  const aliases = [
    {
      alias: "production",
      version: "v2",
      description: "Current stable version",
    },
    {
      alias: "staging",
      version: "v3",
      description: "Testing new improvements",
    },
    { alias: "champion", version: "v2", description: "Current best performer" },
    {
      alias: "challenger",
      version: "v3",
      description: "A/B testing candidate",
    },
  ];

  const introSection = <MarkdownContent content={introContent} />;

  const codeSection = (
    <div className="space-y-6">
      <CollapsibleSection
        title="Section 1: Create and Edit Prompts"
        variant="simple"
        defaultOpen
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/create-and-edit-prompts"
      >
        <div className="space-y-4">
          <MarkdownContent content="Let's first create the prompt for our email generation in MLflow. Below, you see how to do this via the SDK, but you can also do this via the UI.  Prompts use double-brace syntax for variables and support Git-like versioning." />
          <CodeSnippet
            code={createEditPromptsCode}
            title="Create Prompt"
            filename="create_prompts.py"
          />
        </div>
      </CollapsibleSection>

      <CollapsibleSection
        title="Section 2: Use Prompts in Production"
        variant="simple"
        docsUrl="https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/use-prompts-in-deployed-apps"
      >
        <div className="space-y-4">
          <MarkdownContent content="Load prompts dynamically using aliases, implement A/B testing, and follow production best practices. Prompts are referenced via URI format: `prompts:/catalog.schema.name@alias`" />
          <CodeSnippet
            code={usePromptsProductionCode}
            title="Production Usage Patterns"
            filename="production_prompts.py"
          />
        </div>
      </CollapsibleSection>
    </div>
  );

  const demoSection = (
    <div className="space-y-6">
      <MarkdownContent content="Manage prompt versions and aliases in Unity Catalog. Test different prompt versions and configure deployment stages." />

      <div className="flex gap-4 mb-4">
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-2" />
          View in Unity Catalog
        </Button>
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-2" />
          MLflow Experiments
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Prompt Version Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Prompt Versions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="prompt-select">Select Prompt</Label>
              <Select value={selectedPrompt} onValueChange={setSelectedPrompt}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sales_email_generator">
                    workspace.default.sales_email_generator
                  </SelectItem>
                  <SelectItem value="follow_up_email">
                    workspace.default.follow_up_email
                  </SelectItem>
                  <SelectItem value="demo_invitation">
                    workspace.default.demo_invitation
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>Version History</Label>
              {promptVersions.map((version, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{version.version}</span>
                    <span className="text-sm text-muted-foreground">
                      {version.created}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    {version.description}
                  </p>
                  <div className="flex gap-1 flex-wrap">
                    {Object.entries(version.tags).map(([key, value]) => (
                      <Badge key={key} variant="outline" className="text-xs">
                        {key}: {value}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2 mt-2">
                    <Button size="sm" variant="outline">
                      <Play className="h-3 w-3 mr-1" />
                      Test
                    </Button>
                    <Button size="sm" variant="outline">
                      View Template
                    </Button>
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Label htmlFor="commit-message">Commit Message</Label>
              <Textarea
                id="commit-message"
                placeholder="Describe your changes..."
                value={commitMessage}
                onChange={(e) => setCommitMessage(e.target.value)}
                className="h-20"
              />
              <Button className="w-full">
                <Save className="h-4 w-4 mr-2" />
                Create New Version
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Alias Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              Alias Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <Label>Current Aliases</Label>
              {aliases.map((alias, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{alias.alias}</span>
                    <Badge variant="secondary">{alias.version}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {alias.description}
                  </p>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-alias">Create/Update Alias</Label>
              <Input
                id="new-alias"
                placeholder="e.g., production, staging"
                value={newAlias}
                onChange={(e) => setNewAlias(e.target.value)}
              />
              <Select value={promptVersion} onValueChange={setPromptVersion}>
                <SelectTrigger>
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="v1">v1</SelectItem>
                  <SelectItem value="v2">v2</SelectItem>
                  <SelectItem value="v3">v3</SelectItem>
                </SelectContent>
              </Select>
              <Button className="w-full">
                <GitBranch className="h-4 w-4 mr-2" />
                Set Alias
              </Button>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <Package className="h-4 w-4" />
                Production URI
              </h4>
              <code className="text-sm bg-background px-2 py-1 rounded">
                prompts:/workspace.default.{selectedPrompt}@{selectedAlias}
              </code>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* A/B Test Results */}
      <Card>
        <CardHeader>
          <CardTitle>A/B Test Comparison (Champion vs Challenger)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-blue-600">v2</div>
              <div className="text-sm text-muted-foreground">Champion</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-green-600">v3</div>
              <div className="text-sm text-muted-foreground">Challenger</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-gray-600">1,250</div>
              <div className="text-sm text-muted-foreground">Emails Sent</div>
            </div>
            <div className="text-center p-4 border rounded-lg">
              <div className="text-2xl font-bold text-purple-600">7 days</div>
              <div className="text-sm text-muted-foreground">Test Duration</div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-medium text-blue-800 mb-2">
                  Champion (v2) Metrics
                </h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Open Rate: 42%</li>
                  <li>• Click Rate: 8.5%</li>
                  <li>• Response Rate: 3.2%</li>
                  <li>• Average Score: 8.1/10</li>
                </ul>
              </div>
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">
                  Challenger (v3) Metrics
                </h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Open Rate: 45% (+3%)</li>
                  <li>• Click Rate: 9.2% (+0.7%)</li>
                  <li>• Response Rate: 3.8% (+0.6%)</li>
                  <li>• Average Score: 8.6/10 (+0.5)</li>
                </ul>
              </div>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Recommendation</h4>
              <p className="text-sm text-muted-foreground">
                Challenger (v3) shows consistent improvements across all
                metrics. Consider promoting to production after additional
                validation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <StepLayout
      title="Step 5: Prompt Registry"
      description="Centralized prompt management with Unity Catalog integration for version control and deployment"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
