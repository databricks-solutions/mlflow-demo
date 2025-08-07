# Project Memory

## Email Generation Feature

- **LLM Model**: Uses `LLM_MODEL` environment variable (e.g., "agents-demo-gpt4o") for email generation
- **Customer Data**: Loaded from `server/input_data.jsonl` containing sample company/customer data
- **Endpoints**:
  - `/api/companies` - List all companies
  - `/api/customer/{name}` - Get customer details
  - `/api/generate-email/` - Generate email (non-streaming)
  - `/api/generate-email-stream/` - Generate email with streaming
  - `/api/feedback` - Submit user feedback with trace ID

## Package Management

- Use `uv` for Python package management instead of `pip` directly
- This project uses uv for dependency management and virtual environment handling
- When changing Python dependencies, always use `uv add` or `uv remove` commands instead of editing pyproject.toml directly
- When adding node packages use bun not npx
- **Environment Setup**: Always use `uv` to get the environment and `source .env.local` to load environment variables to run any Python code

## Frontend Setup

- **Always use Bun for frontend operations** - faster than npm/yarn and eliminates dependency conflicts
- Client uses shadcn/ui components with proper TypeScript configuration
- Development: `bun start` or `bun dev` in the client directory
- Build process: `bun run build` in the client directory
- Package management: Use `bun add` and `bun remove` instead of npm
- shadcn components can be added with: `npx shadcn@latest add <component-name>`
- **TypeScript path aliases**: Use canonical `@/` imports (e.g., `import { Button } from "@/components/ui/button"`)
- **Build system**: Vite and TypeScript are configured for "@/" alias support automatically

## Development Server Management

- Use "start server" command to run the development server using `./watch.sh` in a detached screen session
- The dev server runs both the FastAPI backend (port 8000) and React frontend (Vite dev server) with hot reload
- Server status can be checked with "server status" or "is server running" commands
- Server can be stopped with "stop server" or "kill server" commands
- Screen session is named "lha-dev" and can be accessed directly with `screen -r lha-dev`
- When server is running, you can test changes immediately without manual restarts
- The server automatically opens http://localhost:8000 when started

## API Endpoint Testing Methodology

When adding or testing endpoints, use this workflow:

1. **Test the endpoint** with curl:
   ```bash
   curl -X POST http://localhost:8000/api/agent \
     -H "Content-Type: application/json" \
     -d '{"inputs": {"messages": [{"role": "user", "content": "What is Databricks?"}]}}'
   ```
1. **Check server logs** immediately after:
   ```bash
   screen -S lha-dev -X hardcopy /tmp/server_logs.txt && tail -30 /tmp/server_logs.txt
   ```
1. **Verify response** includes expected fields (response, trace_id for agent endpoint)
1. **Confirm MLflow tracing** is working (trace_id should be present)

## Hot Reload Development Workflow

The development server supports real-time code changes:

1. **Add debug prints** to server code (e.g., `print(f"🔥 ENDPOINT HIT: {data}")`)
2. **uvicorn auto-reloads** the server when Python files change
3. **Test immediately** with curl - no manual restart needed
4. **Verify functionality** through response content and status codes
5. **Clean up debug code** when done testing
   Note: Screen capture may not always show real-time output clearly, but process monitoring and endpoint testing provide reliable verification.

## Development Server Troubleshooting

- **Profile errors in watch.sh**: The script handles optional DATABRICKS_CONFIG_PROFILE - if not set, uses default auth
- **Screen output capture**: Use `ps aux | grep uvicorn` and direct endpoint testing rather than relying solely on screen hardcopy
- **Port conflicts**: Check `lsof -i :8000` to verify server is listening correctly
- **Process verification**: Multiple uvicorn processes are normal (parent/child from --reload mode)

## Setup

- Use `./setup.sh` to interactively create/configure the .env.local file with all required environment variables

## Code Formatting

- Use `./fix.sh` to format all code according to the project's style guidelines
- This runs ruff formatting/linting for Python files and prettier for TypeScript/JavaScript files
- Run this before committing code to ensure consistent formatting

## Build System & Generated Files

- **Never commit build artifacts**: `client/build/` contains Vite build output (ignored in .gitignore)
- **API client is auto-generated**: `client/src/fastapi_client/` is generated from OpenAPI spec via `uv run python -m scripts.make_fastapi_client`
- **Lock files**: `uv.lock` should be committed to ensure reproducible dependency versions across all developers
- **Development workflow**: The `./watch.sh` script automatically regenerates the API client when backend changes
- When adding new FastAPI endpoints, the TypeScript client updates automatically

## Git Operations

- Use `git pp` instead of `git push` for pushing changes

## Deployment

- When the user says "deploy", use `./deploy.sh` command
- **Automated app.yaml configuration**: Deploy script automatically updates `app.yaml` with `MLFLOW_EXPERIMENT_ID` from `.env.local`
- **Automated verification**: After running deploy.sh, programmatically check deployment success by:
  1. Running `databricks apps list` to verify app appears
  2. Scanning deploy.sh output for success/failure indicators
  3. Checking app status and providing troubleshooting if needed
  4. Reporting deployment status back to user with specific details

## Reading Databricks Apps Logs

- **Log Access Method**: Databricks Apps logs require OAuth authentication and are accessible through:
  1. Web UI: `https://{app-url}/logz` (requires browser authentication)
  2. WebSocket stream: `wss://{app-url}/logz/stream` (requires authenticated session)
- **Authentication**: Apps use OAuth2 flow redirecting to Databricks workspace for authentication
- **Error Detection Strategy**: Since programmatic log access requires auth, use deployment output and app status:
  1. Check `databricks apps list` for app status (ACTIVE/FAILED)
  2. Monitor deploy.sh output for "Error installing requirements" messages
  3. Use app HTTP response codes (302 = running, 500 = error)
- **Dependency Conflict Resolution**: When pip dependency conflicts occur (e.g., "but you have xyz version"), pin the conflicting packages in pyproject.toml to the exact versions that are already installed in Databricks Apps
- **Common Conflicts**: Packages like tenacity, pillow, websockets, pyarrow, markupsafe, werkzeug, and flask often conflict with pre-installed versions
- **Python Version Requirements**: If databricks-connect version conflicts occur, ensure the requires-python version in pyproject.toml matches the requirements (e.g., databricks-connect==16.2.0 requires Python>=3.12)

## Adding Sidebar Sections

Note: this has not been human reviewed so may have errors or bugs!

### Quick Reference Checklist

When adding a new sidebar section, modify these 4 files in order:

1. **Create component file**: Clone existing step component (e.g., copy `step2-evaluation.tsx`)
2. **Update sidebar**: Add entry to `client/src/components/app-sidebar.tsx`
3. **Update routing**: Add view type and routing case to `client/src/App.tsx`
4. **Test**: Verify navigation, fix TypeScript errors, test form controls

### Step-by-Step Process

#### 1. Create New Component (Clone Existing)

**Best approach**: Copy an existing step component rather than creating from scratch.

```bash
# Copy an existing step component as starting point
cp client/src/components/step2-evaluation.tsx client/src/components/my-new-section.tsx
```

**Required modifications to your new component**:

- Change the function name: `export function MyNewSection()`
- Update the title in StepLayout: `title="Step X: My Feature"`
- Update the description: `description="Description of what this step demonstrates"`
- Modify content variables (`introContent`, code examples, etc.)

**Standard component structure to maintain**:

```tsx
export function MyNewSection() {
  // State management (if needed)
  const [someState, setSomeState] = React.useState("default");

  // Content sections
  const introSection = <MarkdownContent content={introContent} />;
  const codeSection = (/* code examples with CollapsibleSection */);
  const demoSection = (/* interactive demo content */);

  return (
    <StepLayout
      title="Step X: My Feature"
      description="Description of this step"
      intro={introSection}
      codeSection={codeSection}
      demoSection={demoSection}
    />
  );
}
```

#### 2. Update Sidebar Navigation

**File**: `client/src/components/app-sidebar.tsx`

**Add to `mlflowSteps` array** (around line 75):

```tsx
{
  title: "Step X: My Feature",
  value: "stepX-my-feature",
  icon: SomeIcon,  // Import from lucide-react
  description: "Brief description for tooltips"
},
```

**Required**: Ensure icon is imported at top of file:

```tsx
import { ..., SomeIcon } from "lucide-react";
```

**Critical**: All mlflowSteps entries MUST have `title`, `value`, `icon`, and `description` properties to satisfy TypeScript interface.

#### 3. Update App Routing

**File**: `client/src/App.tsx`

**Step 3a**: Add to ViewType union (around line 51):

```tsx
type ViewType =
  | "chat"
  | "email"
  | "demo-overview"
  | "step1-tracing"
  | "step2-evaluation"
  | "step3-improvement"
  | "step4-kpis"
  | "stepX-my-feature";
```

**Step 3b**: Import your component (top of file):

```tsx
import { MyNewSection } from "@/components/my-new-section";
```

**Step 3c**: Add routing case (around line 390):

```tsx
) : currentView === 'stepX-my-feature' ? (
  <div className="w-full h-full">
    <MyNewSection />
  </div>
```

#### 4. Test and Fix Common Issues

**Start dev server to test**:

```bash
bun dev  # In client directory
```

**Common TypeScript errors and fixes**:

1. **Missing description property**:

   ```
   Error: Property 'description' is missing
   Fix: Add description: "..." to sidebar entry
   ```

2. **Controlled component without onChange**:

   ```
   Error: You provided a `value` prop to a form field without an `onChange` handler
   Fix: Add state management and onChange handlers to Input components
   ```

3. **Unused imports**:
   ```
   Error: 'SomeImport' is declared but its value is never read
   Fix: Remove unused imports from component file
   ```

### Component Cloning Templates

#### For Interactive Demo Components (with forms):

**Clone source**: `client/src/components/prompt-registry.tsx`
**Good for**: Components with user inputs, interactive elements

#### For Code-Heavy Educational Components:

**Clone source**: `client/src/components/step2-evaluation.tsx`
**Good for**: Components focused on showing implementation patterns

#### For Overview/Introduction Components:

**Clone source**: `client/src/components/demo-overview.tsx`
**Good for**: High-level explanatory content with step navigation

### Form Component Best Practices

**Always use controlled components with proper state**:

```tsx
// ❌ Wrong: Controlled component without onChange
<Input value="50" />;

// ✅ Correct: Properly controlled component
const [value, setValue] = React.useState(50);
<Input value={value} onChange={(e) => setValue(Number(e.target.value))} />;
```

### Navigation Flow

The navigation system works as follows:

1. **User clicks sidebar item** → `setCurrentView(value)` called
2. **App.tsx routing** → Renders component based on `currentView` state
3. **Component loaded** → Uses StepLayout for consistent presentation
4. **Internal navigation** → Components can call `setCurrentView()` to navigate

### File Naming Conventions

- **Component files**: `kebab-case.tsx` (e.g., `my-new-section.tsx`)
- **Component functions**: `PascalCase` (e.g., `MyNewSection`)
- **View values**: `kebab-case` (e.g., `stepX-my-feature`)
- **Sidebar titles**: `"Step X: Feature Name"` format for consistency

This process ensures consistent patterns and reduces errors when adding new demonstration sections to the application.

## Adding React Query Helpers

Note: this has not been human reviewed so may have errors or bugs!

When you need to create React Query hooks for existing FastAPI endpoints that don't have frontend integration yet:

### Quick Reference Pattern

1. **Check if API client method exists**: Look in `client/src/fastapi_client/services/ChatService.ts` for the method
2. **Add helper to query file**: Add new function to appropriate file in `client/src/queries/`
3. **Import and use in component**: Add import and create data/loading variables
4. **Use in component**: Replace hardcoded values with query data

### Step-by-Step Process

#### 1. Verify API Client Method Exists

First, check if the FastAPI endpoint is already available in the generated client:

```bash
# Search for the endpoint method
rg "your-endpoint-name" client/src/fastapi_client/services/ChatService.ts
```

If the method exists (like `getCurrentProductionPromptApiCurrentProductionPromptGet()`), proceed. If not, the API client needs regeneration via `./watch.sh`.

#### 2. Add Helper Function

Add to the appropriate query file (or create new one following the pattern):

**Example in `client/src/queries/useQueryFixedPrompt.tsx`**:

```tsx
export function useQueryCurrentProductionPrompt() {
  return useQuery({
    queryKey: ["current-production-prompt"],
    queryFn: async () => {
      return ChatService.getCurrentProductionPromptApiCurrentProductionPromptGet();
    },
  });
}
```

**Key patterns**:

- Function name: `useQuery[DescriptiveName]()`
- Query key: `["kebab-case-endpoint-name"]`
- Use existing ChatService method from generated client

#### 3. Import and Use in Component

```tsx
// Add to imports
import {
  useQueryFixedPrompt,
  useQueryCurrentProductionPrompt,
} from "@/queries/useQueryFixedPrompt";

// Add in component function
const {
  data: currentProductionPromptData,
  isLoading: isCurrentProductionPromptLoading,
} = useQueryCurrentProductionPrompt();

// Create variable with fallback
const currentProductionPrompt =
  currentProductionPromptData?.prompt ||
  (isCurrentProductionPromptLoading
    ? "Loading current production prompt..."
    : "Default fallback text here");
```

**Naming patterns**:

- Data variable: `[endpoint]Data`
- Loading variable: `is[Endpoint]Loading`
- Final variable: `[descriptiveName]` (matches what you're replacing)

#### 4. Replace Usage

```tsx
// Before
<Textarea value={fixedPromptText} />

// After
<Textarea value={currentProductionPrompt} />
```

### Common Use Cases

- **Prompt templates**: `/api/fixed-prompt`, `/api/current-production-prompt`
- **Configuration data**: `/api/settings`, `/api/config`
- **Status endpoints**: `/api/health`, `/api/system-status`
- **Data lists**: `/api/companies`, `/api/customers`

### File Organization

- **Single endpoint**: Add to existing related query file
- **Multiple related endpoints**: Create new file like `useQuerySettings.tsx`
- **Follow import pattern**: Use existing query files as templates

This pattern enables quick integration of existing backend endpoints with React components without planning overhead.

## MLflow Reference

- When using MLflow SDKs and thinking about MLflow features and value props to help write demo prose and MLflow code, use this docs site as reference: https://docs.databricks.com/aws/en/mlflow3/genai/
- Full SDK references are linked from here: https://docs.databricks.com/aws/en/mlflow3/genai/api-reference
- For any code you generate, make sure it complies with the SDK reference
