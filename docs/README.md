# DC Assistant Demo - Complete Guide

**Quick Summary**: Frontend is 100% done. Backend needs API endpoints (4-6 hours work). App will deploy and show UI, but won't connect to real data yet.

---

## Table of Contents
1. [What's Done & What's Not](#whats-done--whats-not)
2. [How to Deploy (5 minutes)](#how-to-deploy)
3. [How to Configure for Your Experiment](#how-to-configure-for-your-experiment)
4. [Local Development Setup](#local-development-setup)
5. [What Needs to be Built (Backend)](#what-needs-to-be-built)

---

## What's Done & What's Not

### ✅ Complete - Ready to Deploy

**Frontend (100%)**
- ✅ All 6 demo sections rebuilt for DC Assistant
- ✅ Interactive components (Run buttons, progress bars, diff viewers)
- ✅ DC Assistant branding and content
- ✅ Production build ready (`client/build/`)

**Backend Structure**
- ✅ FastAPI app configured (`server/app.py`)
- ✅ Static file serving works
- ✅ Health check endpoint
- ✅ Experiment info endpoint (reads from env vars)

**Deployment**
- ✅ `app.yaml` configured for Databricks App
- ✅ All dependencies in `requirements.txt`
- ✅ Python version fixed (3.10+)

### ⚠️ Not Done - Needs Backend Work

**Missing API Endpoints**
- ⚠️ No DC Assistant data endpoints (traces, judges, sessions, etc.)
- ⚠️ Demo buttons show hardcoded/mock results
- ⚠️ Can't pull real data from your MLflow experiment yet

**See [TODO_BACKEND.md](TODO_BACKEND.md) for implementation details** (4-6 hours work)

---

## How to Deploy

### Step 1: Configure Your Experiment (2 minutes)

Edit `app.yaml` in project root:

```yaml
env:
  - name: 'MLFLOW_EXPERIMENT_ID'
    value: '/Users/your.email@databricks.com/dc-assistant-demo'  # ← CHANGE THIS

  - name: 'UC_CATALOG'
    value: 'main'  # ← CHANGE THIS

  - name: 'UC_SCHEMA'
    value: 'dc_assistant'  # ← CHANGE THIS

  - name: 'MODEL_ENDPOINT_NAME'
    value: 'dc-assistant-endpoint'  # ← CHANGE THIS if different
```

**That's it!** Everything else auto-configures from these 4 variables.

### Step 2: Push to Git (1 minute)

```bash
git add app.yaml
git commit -m "Configure for my experiment"
git push origin ui-dev
```

### Step 3: Deploy Databricks App (2 minutes)

1. Go to Databricks workspace → **Apps**
2. Click **Create App from Git**
3. Settings:
   - Repository: `https://github.com/auschoi96/end-to-end-mlflow-genai.git`
   - Branch: `ui-dev`
4. Click **Create**
5. Wait 2-3 minutes for deployment

### Step 4: Verify (1 minute)

**What should work:**
- ✅ App loads and displays all 6 sections
- ✅ "View Experiment in MLflow UI" opens YOUR experiment
- ✅ Interactive UI (buttons, tabs, cards)
- ✅ Code examples displayed correctly

**What won't work yet:**
- ⚠️ "Run Optimization" shows mock results (not real data)
- ⚠️ Sample traces are hardcoded examples
- ⚠️ No connection to your actual MLflow traces/judges

**To get real data**: Implement backend endpoints (see [TODO_BACKEND.md](TODO_BACKEND.md))

---

## How to Configure for Your Experiment

### Where Experiment IDs Are Used

#### 1. Environment Variables (PRIMARY - Edit These)

**File**: `app.yaml` (for Databricks App)

```yaml
env:
  - name: 'MLFLOW_EXPERIMENT_ID'
    value: '/Users/your.email/dc-assistant'  # ← Your experiment path or ID

  - name: 'UC_CATALOG'
    value: 'main'  # ← Where your judges/prompts are stored

  - name: 'UC_SCHEMA'
    value: 'dc_assistant'  # ← Schema in Unity Catalog

  - name: 'MODEL_ENDPOINT_NAME'
    value: 'dc-assistant-endpoint'  # ← Your model serving endpoint
```

**File**: `.env.local` (for local development - create this)

```bash
# MLflow Configuration
MLFLOW_TRACKING_URI=databricks
MLFLOW_EXPERIMENT_ID=/Users/your.email@databricks.com/dc-assistant

# Unity Catalog
UC_CATALOG=main
UC_SCHEMA=dc_assistant

# Model Serving
MODEL_ENDPOINT_NAME=dc-assistant-endpoint

# Databricks Authentication (local dev only)
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef  # Your PAT

# Optional: For demo trace links
SAMPLE_TRACE_ID=tr-your-trace-id-here
SAMPLE_LABELING_SESSION_ID=ls-your-session-id
```

#### 2. Backend Code (AUTO-READS from env vars - Don't Edit)

**File**: `server/app.py` (lines 115-127)

```python
@app.get(f'{API_PREFIX}/tracing_experiment')
async def experiment():
  return ExperimentInfo(
    experiment_id=get_mlflow_experiment_id(),  # ← Reads MLFLOW_EXPERIMENT_ID
    link=f'{databricks_host}/ml/experiments/{get_mlflow_experiment_id()}...',
    # ... URLs auto-constructed from env vars
  )
```

**No code changes needed** - it automatically uses your environment variables.

**File**: `mlflow_demo/utils/mlflow_helpers.py`

Helper functions that read env vars:
- `get_mlflow_experiment_id()` → Returns `MLFLOW_EXPERIMENT_ID`
- `generate_trace_links()` → Constructs URLs using experiment ID
- `generate_prompt_link()` → Uses `UC_CATALOG.UC_SCHEMA`

**No code changes needed** - all env var based.

#### 3. Frontend Display (HARDCODED - Safe to Ignore)

**Files**: `client/src/components/demo-pages/*.tsx`

These have hardcoded values in code examples shown to users:

```typescript
// Example code displayed to user (NOT executed)
mlflow.set_experiment(experiment_id=MLFLOW_EXPERIMENT_ID)
experiment_ids=[EXPERIMENT_ID]
```

**No configuration needed** - these are just example snippets for display purposes.

### How to Switch Experiments

**Scenario: Colleague wants to use their own experiment**

1. Edit `app.yaml` (4 lines)
2. Push to git
3. Redeploy app

**Time**: 5 minutes

**Scenario: Testing different experiments locally**

1. Update `.env.local`:
   ```bash
   MLFLOW_EXPERIMENT_ID=/Users/me/experiment-2
   ```
2. Restart backend server
3. Refresh frontend

**Time**: 1 minute

### What Each Variable Controls

| Variable | What It Affects | Example Value |
|----------|----------------|---------------|
| `MLFLOW_EXPERIMENT_ID` | Which experiment's traces/runs are shown | `/Users/me/dc-assistant` or `2517718719552044` |
| `UC_CATALOG` | Where judges/prompts are registered | `main` or `your_catalog` |
| `UC_SCHEMA` | Schema for storing MLflow artifacts | `dc_assistant` or `genai_demo` |
| `MODEL_ENDPOINT_NAME` | Which model serving endpoint to call | `dc-assistant-endpoint` |
| `DATABRICKS_HOST` | Which workspace (for URL generation) | `https://workspace.cloud.databricks.com` |

---

## Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Databricks workspace access
- MLflow experiment created

### Setup Steps

```bash
# 1. Clone repository
git clone https://github.com/auschoi96/end-to-end-mlflow-genai.git
cd end-to-end-mlflow-genai
git checkout ui-dev

# 2. Create .env.local (see template above)
# Copy the template from "How to Configure" section

# 3. Install backend dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. Install frontend dependencies
cd client
npm install
cd ..
```

### Run Locally

```bash
# Terminal 1 - Backend
source .venv/bin/activate
uvicorn server.app:app --reload --port 8000

# Terminal 2 - Frontend
cd client
npm run dev
```

Open http://localhost:3000

### Build for Production

```bash
cd client
npm run build
# Output: client/build/
```

---

## What Needs to be Built

### Backend API Endpoints (Missing)

The frontend expects 8 API endpoints that don't exist yet:

1. `GET /api/dc-assistant/experiment-info` - Experiment metadata
2. `GET /api/dc-assistant/traces` - Sample traces
3. `GET /api/dc-assistant/judges` - Judge configurations
4. `GET /api/dc-assistant/labeling-sessions` - Labeling data
5. `GET /api/dc-assistant/alignment-results` - SIMBA/MemAlign results
6. `GET /api/dc-assistant/gepa-results` - GEPA optimization results
7. `GET /api/dc-assistant/monitoring-metrics` - Production metrics
8. `GET /api/dc-assistant/notebook-links` - Notebook URLs

**See [TODO_BACKEND.md](TODO_BACKEND.md) for**:
- Complete endpoint specifications with response formats
- Implementation guide
- Quick start (3-4 hours to get working)

### Why App Works Without These

The app deploys successfully because:
- Frontend is pre-built static files (doesn't need backend to load)
- UI components render without data
- Interactive features show placeholder/mock data
- "View Experiment" buttons work (use env var endpoint)

But to show REAL data from your experiment, you need to implement those endpoints.

---

## Troubleshooting

### App fails to deploy

**Error**: "Python version mismatch"
- **Fix**: Already fixed - `pyproject.toml` now requires Python 3.10+

**Error**: "Module not found: mlflow_demo"
- **Check**: `mlflow_demo/` folder exists in git
- **Check**: `requirements.txt` has all dependencies

### App deploys but shows blank page

**Check**:
1. Browser console for errors
2. Verify `client/build/` exists in git repo
3. Check Databricks App logs for backend errors

### "View Experiment" opens wrong experiment

**Fix**: Update `MLFLOW_EXPERIMENT_ID` in `app.yaml` and redeploy

### Local dev: Can't connect to MLflow

**Check**:
1. `.env.local` has `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
2. Token is valid (not expired)
3. Test: `databricks auth login --host https://your-workspace.cloud.databricks.com`

---

## Files You MUST Edit

| File | What to Change | When |
|------|----------------|------|
| `app.yaml` | 4 environment variables | Before first deployment |
| `.env.local` | Same 4 variables + auth | For local development |

## Files That Auto-Configure (Don't Edit)

| File | Purpose | Why No Edit Needed |
|------|---------|-------------------|
| `server/app.py` | Backend app | Reads from env vars |
| `mlflow_demo/utils/mlflow_helpers.py` | MLflow utilities | Reads from env vars |
| `client/src/components/demo-pages/*.tsx` | Frontend UI | Already complete |
| `requirements.txt` | Python dependencies | Already configured |

---

## Quick Reference

### Deploy to Databricks (5 min)
1. Edit `app.yaml` (4 variables)
2. `git push origin ui-dev`
3. Create Databricks App from Git

### Configure for Different Experiment (5 min)
1. Edit `app.yaml` → `MLFLOW_EXPERIMENT_ID`
2. Edit `app.yaml` → `UC_CATALOG`, `UC_SCHEMA`
3. Redeploy

### Run Locally (1 min)
```bash
# Terminal 1
uvicorn server.app:app --reload --port 8000

# Terminal 2
cd client && npm run dev
```

### Implement Backend (4-6 hours)
See [TODO_BACKEND.md](TODO_BACKEND.md)

---

## Summary

**What you have**: Fully functional frontend UI ready to deploy

**What you need**:
1. Configure 4 environment variables in `app.yaml`
2. Deploy to Databricks App (5 min)
3. *(Optional)* Implement backend endpoints for real data (4-6 hours)

**App will work without backend**, just won't show your actual MLflow data yet.
