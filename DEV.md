# Development guide

## Development

### Prerequisites

```
brew install uv bun
```

### Environment setup

Run the interactive setup script to create your `.env.local` file:

```bash
./setup.sh
```

Or manually clone `.env.template` to `.env.local`.

## Running the app locally

See `./setup/use_app_locally.py` for how to run a local Python script that calls the email generation app.

## Tech Stack

**🖥️ Frontend (Port 3000)**

- **[React](https://react.dev/)** + **[TypeScript](https://www.typescriptlang.org/)** for the UI framework
- **[Vite](https://vitejs.dev/)** for fast development and hot module replacement
- **[shadcn/ui](https://ui.shadcn.com/)** for beautiful, accessible components built on Radix UI
- **[Tailwind CSS](https://tailwindcss.com/)** for styling
- **[Bun](https://bun.sh/)** as the package manager and dev server

**⚙️ Backend (Port 8000)**

- **[FastAPI](https://fastapi.tiangolo.com/)** for the Python API server with auto-docs
- **[uvicorn](https://www.uvicorn.org/)** with hot reload for development
- **[OpenAI Python SDK](https://github.com/openai/openai-python)** for Databricks model serving endpoints

**📊 Observability & Deployment**

- **[MLflow](https://mlflow.org/)** for experiment tracking and [agent monitoring/evaluation](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- **[Lakehouse Apps](https://www.databricks.com/product/databricks-apps)** for production deployment

**🔧 Development Tools**

- **Fast edit-refresh cycle**: `./watch.sh` runs both servers with hot reload
- **Frontend proxy**: In dev mode, port 8000 proxies non-API requests to port 3000
- **Auto-reloading**: Backend reloads on Python changes, frontend on React/CSS changes

### Adding UI Components

The template uses **shadcn/ui** for consistent, accessible components:

```bash
# Add a new component (run from project root)
bunx --bun shadcn@latest add button
bunx --bun shadcn@latest add dialog
bunx --bun shadcn@latest add form

# Browse available components
bunx --bun shadcn@latest add
```

Components are installed to `client/src/components/ui/` and use the canonical "@/" import pattern:

```tsx
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

function MyComponent() {
  return (
    <Card>
      <CardHeader>My Card</CardHeader>
      <CardContent>
        <Button variant="outline">Click me</Button>
      </CardContent>
    </Card>
  );
}
```

**Styling approach:**

- shadcn/ui components use **CSS variables** for theming (see `client/src/index.css`)
- **Tailwind classes** for custom styling and layout
- **Responsive design** built-in with Tailwind's breakpoint system

A simple system-prompt agent is defined in `server/agents/databricks_assisstant.py` that calls OpenAI with a system prompt, which can be further customized.

## Quick Start

Get the template running in 3 commands:

```bash
git clone <this-repo>
./setup.sh                 # Interactive environment setup
./load_sample_data.sh      # Load sample data to MLflow
./watch.sh                 # Start development server
```

🎉 **Open http://localhost:8000** - You'll have a working chat interface with Databricks agent!

**What you get:**

- 🤖 Chat interface with AI agent responses (~5-10s response time)
- 📊 MLflow experiment tracking with trace IDs
- 🔥 Hot reload for both frontend and backend changes
- 🧪 Built-in testing and formatting tools

## Project Structure

```
├── server/                 # FastAPI backend
│   ├── agents/            # Agent implementations
│   │   ├── databricks_assistant.py  # Main agent (customize this!)
│   │   └── model_serving.py         # Direct model endpoint calls
│   ├── app.py             # FastAPI routes and setup
│   └── tracing.py         # MLflow integration
├── client/                # React frontend
│   ├── src/components/    # UI components (shadcn/ui based)
│   ├── src/queries/       # API client and React Query hooks
│   └── build/             # Production build output
├── scripts/               # Build and utility scripts
├── *.sh                   # Development automation scripts
└── .env.local            # Environment configuration (create with ./setup.sh)
```

### Development scripts

**Setup and configuration:**

- `./setup.sh` - Interactive setup to create `.env.local` file
- `./load_sample_data.sh` - Loads sample data to the experiment that powers the demo
- `./fix.sh` - Format all code (ruff for Python, prettier for TypeScript)
- `./check.sh` - Run code quality checks

**Development and testing:**

- `./watch.sh` - Run fast-edit refresh python + typescript locally
- `./start_prod.sh` - Run the production server locally
- `./test_agent.sh` - Test agent directly without starting full web app

## Claude Code Integration

This project includes configuration for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) to help with development tasks. See [CLAUDE.md](./CLAUDE.md) for detailed project instructions and context.

**Key Claude commands:**

- "setup" - Run the interactive environment setup script
- "deploy" - Deploy the application using the deploy script
- "fix" - Format all code according to project style guidelines
- "test agent" - Test the agent directly without starting the full web application

Claude Code understands the project structure and can help with development tasks while following the established patterns and conventions.

## Troubleshooting

### Common Issues

**❌ "Profile error" when running `./watch.sh`**

- **Solution**: The script handles optional `DATABRICKS_CONFIG_PROFILE` - if not set, it uses default auth
- **Check**: Ensure your `.env.local` has valid `DATABRICKS_HOST` and `DATABRICKS_TOKEN`

**❌ Port 8000 already in use**

- **Check**: `lsof -i :8000` to see what's using the port
- **Solution**: Kill the process or change `UVICORN_PORT` in your environment

**❌ Frontend not loading/502 errors**

- **Check**: Both uvicorn (backend) and bun (frontend) processes are running
- **Solution**: Run `./watch.sh` again - it starts both servers

**❌ Agent responses are slow (>30s)**

- **Expected**: 5-10s response time is normal for LLM calls
- **Check**: Your `DATABRICKS_HOST` network connectivity
- **Monitor**: Use the MLflow experiment link to see trace details

**❌ MLflow tracing not working**

- **Check**: `MLFLOW_EXPERIMENT_ID` is set in `.env.local`
- **Verify**: Visit the tracing experiment URL from `/api/tracing_experiment`

### Development Tips

- **Hot reload issues**: If changes aren't picked up, restart `./watch.sh`
- **Screen session stuck**: Use `screen -list` and `screen -X -S lha-dev quit` to force-kill
- **API testing**: Use the built-in curl commands from [CLAUDE.md](./CLAUDE.md)
- **Debug mode**: Add `print()` statements in Python code - they'll show in the uvicorn output

## Contributing

Found a bug or want to improve the template?

1. **Test your changes** with `./watch.sh` and `./fix.sh` and ensure they deploy to a Databricks app
2. **Update documentation** if you add new features
3. **Follow the development patterns** established in [CLAUDE.md](./CLAUDE.md)
4. **Submit a PR** to this repo
