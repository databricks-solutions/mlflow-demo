# MLflow 3 GenAI Demo — DC Assistant

A comprehensive demonstration of **MLflow 3's GenAI capabilities** for observing, evaluating, monitoring, and improving GenAI application quality. This interactive demo showcases an NFL Defensive Coordinator (DC) Assistant that analyzes play-calling tendencies using Unity Catalog tools, with end-to-end quality assessment workflows powered by MLflow.

The demo is deployed as a **Databricks App** with a guided UI experience. Companion **notebooks** walk through the full workflow — from tracing agent behavior, to evaluating quality with LLM judges, to aligning judges with domain experts, to optimizing prompts automatically.

**Learn more about MLflow 3:**

- Read the [blog post](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance)
- View our [website](https://www.managed-mlflow.com/genai)
- Get started via the [documentation](https://docs.databricks.com/aws/en/mlflow3/genai/)

## What's included

| Component | Description |
|-----------|-------------|
| **DC Assistant Agent** | Tool-calling agent that queries NFL play-by-play data via Unity Catalog functions |
| **Interactive Web UI** | React + FastAPI app with a guided walkthrough of MLflow's GenAI capabilities |
| **Notebooks** | Step-by-step notebooks covering tracing, evaluation, labeling, judge alignment, prompt optimization, and monitoring |
| **Setup Scripts** | Automated and manual setup for loading prompts, sample traces, evaluation runs, and monitoring |

### Demo walkthrough steps

1. **Observe DC Analysis** — Capture agent behavior with MLflow tracing (single-tool and multi-tool queries)
2. **Evaluate Recommendations** — Create LLM judges for single-turn and multi-turn (session-level) evaluation
3. **Collect Ground Truth Labels** — Build labeled datasets through SME review sessions
4. **Align Judges to Experts** — Calibrate judges to match coaching expertise with SIMBA/MemAlign
5. **Optimize Prompts** — Automatically improve prompts with GEPA optimizer
6. **Ongoing Monitoring** — Self-optimizing cycle from coach feedback to improved prompts

## Project structure

```
├── mlflow_demo/
│   ├── agent/            # DC Assistant agent (ToolCallingAgent + ResponsesAgent)
│   │   └── config/       # Agent config (UC tools, workspace settings)
│   └── notebooks/        # Step-by-step demo notebooks (0–5)
├── server/               # FastAPI backend (routes, SSE streaming)
├── client/               # React frontend (Vite + shadcn/ui)
├── setup/                # Data loading scripts (prompts, traces, evals, monitoring)
├── docs/                 # Reference notebooks (judge alignment, prompt optimization)
├── auto-setup.sh         # Automated one-command setup
├── setup.sh              # Interactive environment configuration
├── load_sample_data.sh   # Load sample traces, evals, and prompts
├── deploy.sh             # Deploy to Databricks Apps
└── start_server.sh       # Local development server
```

### Notebooks

Located in `mlflow_demo/notebooks/`:

| Notebook | Topic |
|----------|-------|
| `0_demo_overview` | Introduction and setup |
| `1_observe_with_traces` | MLflow tracing for agent observability |
| `2_create_quality_metrics` | Building LLM judges and running evaluations |
| `3_find_fix_quality_issues` | Identifying and fixing quality issues from eval results |
| `4_human_review` | Expert labeling sessions for ground truth |
| `5_production_monitoring` | Scheduled evaluation monitoring in production |

## Installing the demo

Choose your installation method:

### Option A: Automated Setup (Recommended)

**Estimated time: 2 minutes input + 15 minutes for scripts to run**

The automated setup handles resource creation, configuration, and deployment using the Databricks Workspace SDK.

#### Prerequisites

- [ ] **Databricks workspace access** — [Create one here](https://signup.databricks.com/?destination_url=/ml/experiments-signup?source=TRY_MLFLOW&dbx_source=TRY_MLFLOW&signup_experience_step=EXPRESS&provider=MLFLOW&utm_source=email_demo_github) if needed
- [ ] **Python >= 3.10.16**
- [ ] **Databricks CLI >= 0.262.0** — [Installation guide](https://docs.databricks.com/aws/en/dev-tools/cli/install)

#### Run automated setup

```bash
git clone https://github.com/databricks-solutions/mlflow-demo.git
cd mlflow-demo
databricks auth login   # Authenticate with your workspace
./auto-setup.sh
```

The script will:
1. Check and install prerequisites (uv, bun)
2. Initialize Python and TypeScript environments
3. Prompt you for workspace configuration (experiment ID, UC schema, app name, etc.)
4. Load sample data (prompts, traces, evaluation runs, monitoring)
5. Deploy the app

### Option B: Manual Setup

**Estimated time: 10 minutes work + 15 minutes for scripts to run**

For step-by-step manual installation, see **[MANUAL_SETUP.md](MANUAL_SETUP.md)**.

The manual setup covers:
- Phase 1: Prerequisites (workspace, MLflow experiment, Unity Catalog schema, CLI)
- Phase 2: Choose deployment mode (full app vs. notebooks only)
- Phase 3: Environment configuration and sample data loading
- Phase 4: Deployment and permissions

## Local development

To run the app locally after setup:

```bash
# Start the backend (FastAPI on port 8000)
./start_server.sh

# In a separate terminal, start the frontend (Vite on port 3000)
cd client && npm run dev
```

Visit `http://localhost:3000` to use the demo.

## Configuration

Environment variables are configured in `.env` (created by the setup script). Key variables:

| Variable | Description |
|----------|-------------|
| `DATABRICKS_HOST` | Your Databricks workspace URL |
| `MLFLOW_EXPERIMENT_ID` | MLflow experiment for tracing and evaluation |
| `UC_CATALOG` / `UC_SCHEMA` | Unity Catalog location for agent tools and prompts |
| `LLM_MODEL` | Model serving endpoint (e.g., `databricks-claude-3-7-sonnet`) |
| `PROMPT_NAME` | Prompt Registry name (`dc_assistant_system_prompt`) |

## MLflow 3 capabilities demonstrated

- **GenAI Observability** — Production-scale tracing for agent tool calls, LLM responses, and session context. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/)
- **Evaluation with LLM Judges** — Built-in and custom scorers for single-turn and multi-turn (session-level) quality. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- **Custom Judges** — Tailor AI judges to your domain (e.g., football coaching accuracy). [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-judge/)
- **Production Monitoring** — Scheduled automatic quality evaluations. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/run-scorer-in-prod)
- **Evaluation Datasets** — Turn production traces into curated, versioned datasets. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/build-eval-dataset)
- **User Feedback** — Capture end-user feedback (thumbs up/down + comments) on traces. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/)
- **Expert Labeling** — Send traces to domain experts for ground truth labeling. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces)
- **Prompt Registry** — Version and manage prompts centrally. [Docs](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/create-and-edit-prompts)

## Questions or feedback?

Reach out to Nethra Ranganathan or Austin Choi.
