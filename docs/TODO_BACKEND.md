# DC Assistant Demo - Remaining Work TODO

**Status**: Frontend is 100% complete. Backend plumbing needs implementation for interactive demos to connect to real data.

---

## Overview

### What's Done ✅
- ✅ All 6 frontend demo sections with DC Assistant UI
- ✅ Interactive components (Run buttons, progress bars, diff viewers)
- ✅ FastAPI backend structure
- ✅ Static file serving
- ✅ Health check endpoint
- ✅ Frontend production build
- ✅ Databricks App configuration (app.yaml)
- ✅ Deployment documentation

### What Needs Work ⚠️
- ⚠️ Backend API endpoints for DC Assistant data
- ⚠️ Preloaded demo data/mock responses
- ⚠️ Validation script for deployment checks

---

## TODO #1: Create Backend API Endpoints

**Priority**: HIGH
**Estimated Effort**: 4-6 hours
**File to Create**: `server/routes/dc_assistant.py`

### Required Endpoints

Create 8 API endpoints that the frontend currently calls:

#### 1. GET `/api/dc-assistant/experiment-info`
**Purpose**: Return DC Assistant experiment metadata
**Frontend Usage**: All sections - displays experiment links
**Response**:
```json
{
  "experiment_id": "2517718719552044",
  "experiment_name": "DC Assistant Demo",
  "tracking_uri": "databricks",
  "workspace_url": "https://your-workspace.cloud.databricks.com"
}
```

**Implementation Notes**:
- Read from environment variables
- Similar to existing `/api/tracing_experiment` endpoint
- No MLflow calls needed - just env var formatting

---

#### 2. GET `/api/dc-assistant/traces`
**Purpose**: Return sample traces for "Observe with Tracing" section
**Frontend Usage**: `observe-with-tracing.tsx` - displays trace examples
**Response**:
```json
{
  "traces": [
    {
      "trace_id": "tr-abc123",
      "question": "Who gets the ball for Cowboys in 11 personnel on 3rd and 6?",
      "response": "Historically, the Cowboys target CeeDee Lamb...",
      "tools_used": ["get_target_stats", "get_play_success_rate"],
      "timestamp": "2024-01-24T10:30:00Z",
      "mlflow_url": "https://workspace.databricks.com/ml/experiments/.../traces?selectedEvaluationId=tr-abc123"
    }
  ]
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded sample traces
- **Option B (Real)**: Query MLflow: `mlflow.search_traces(experiment_ids=[exp_id], max_results=5)`

---

#### 3. GET `/api/dc-assistant/judges`
**Purpose**: Return created LLM judge configurations
**Frontend Usage**: `create-quality-metrics.tsx` - displays judge results
**Response**:
```json
{
  "judges": [
    {
      "name": "football_language",
      "title": "Football Language Judge",
      "description": "Evaluates use of correct NFL terminology",
      "pass_rate": 0.72,
      "sample_evaluations": [
        {"input": "...", "output": "...", "score": "pass", "reasoning": "..."}
      ],
      "mlflow_url": "https://workspace.databricks.com/ml/experiments/.../judges/football_language"
    },
    {
      "name": "data_grounded",
      "title": "Data Grounded Judge",
      "description": "Checks if response uses actual data from tools",
      "pass_rate": 0.85,
      "sample_evaluations": []
    }
  ]
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded judge configs
- **Option B (Real)**: Load from Unity Catalog: `mlflow.genai.judges.load("catalog.schema.judge_name")`

---

#### 4. GET `/api/dc-assistant/labeling-sessions`
**Purpose**: Return labeling session data for SME review
**Frontend Usage**: `find-fix-quality-issues.tsx` - displays labeling workflow
**Response**:
```json
{
  "sessions": [
    {
      "session_id": "ls-xyz789",
      "name": "DC Assistant Expert Review - Week 1",
      "traces_count": 50,
      "completed_labels": 32,
      "schemas": ["football_language", "data_grounded", "strategic_soundness"],
      "created_at": "2024-01-20T08:00:00Z",
      "mlflow_url": "https://workspace.databricks.com/ml/experiments/.../labeling-sessions?selectedLabelingSessionId=ls-xyz789"
    }
  ],
  "sample_labels": [
    {
      "trace_id": "tr-abc123",
      "schema": "football_language",
      "label": "fail",
      "feedback": "Used 'defense' instead of specific coverage type (Cover 2, Cover 3, etc.)"
    }
  ]
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded session data
- **Option B (Real)**: Query MLflow labeling API

---

#### 5. GET `/api/dc-assistant/alignment-results`
**Purpose**: Return SIMBA/MemAlign optimization results
**Frontend Usage**: `business-metrics.tsx` - displays before/after judge prompts
**Response**:
```json
{
  "optimizer": "memalign",
  "judge_name": "football_language",
  "baseline_accuracy": 0.72,
  "aligned_accuracy": 0.91,
  "before_prompt": "Evaluate if the response uses correct football terminology...",
  "after_prompt": "Evaluate if the response uses correct football terminology. Focus on:\n- Specific coverage schemes (Cover 2, Cover 3, etc.)\n- Formation names (11 personnel, 12 personnel)\n- Route terminology (post, corner, slant)\n...",
  "diff_lines": [
    {"type": "added", "content": "- Specific coverage schemes (Cover 2, Cover 3, etc.)"},
    {"type": "added", "content": "- Formation names (11 personnel, 12 personnel)"}
  ],
  "learned_rules": [
    "Judge now requires specific coverage scheme names instead of generic 'defense'",
    "Added validation for formation terminology accuracy"
  ]
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded optimization diff
- **Option B (Real)**: Load aligned judge and compare prompts

---

#### 6. GET `/api/dc-assistant/gepa-results`
**Purpose**: Return GEPA prompt optimization results
**Frontend Usage**: `prod-monitoring.tsx` - displays baseline vs optimized prompts
**Response**:
```json
{
  "baseline_prompt": {
    "name": "dc_assistant_baseline_v1",
    "content": "You are an NFL defensive coordinator assistant...",
    "accuracy": 0.78
  },
  "optimized_prompt": {
    "name": "dc_assistant_optimized_v2",
    "content": "You are an NFL defensive coordinator assistant. When answering:\n1. Always cite specific play data\n2. Reference formation and personnel\n3. Compare to league averages\n...",
    "accuracy": 0.89
  },
  "diff_lines": [
    {"type": "added", "content": "1. Always cite specific play data"},
    {"type": "added", "content": "2. Reference formation and personnel"}
  ],
  "improvements": [
    "Added requirement to cite specific play data",
    "Included formation context in responses",
    "Added league average comparisons",
    "Improved reasoning structure"
  ],
  "mlflow_url": "https://workspace.databricks.com/ml/experiments/.../prompts"
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded prompt comparison
- **Option B (Real)**: Load prompts from UC and compare

---

#### 7. GET `/api/dc-assistant/monitoring-metrics`
**Purpose**: Return production monitoring dashboard data
**Frontend Usage**: `human-review.tsx` - displays monitoring metrics
**Response**:
```json
{
  "time_period": "last_7_days",
  "metrics": {
    "total_requests": 1247,
    "avg_response_time_ms": 2340,
    "judge_pass_rates": {
      "football_language": 0.91,
      "data_grounded": 0.88,
      "strategic_soundness": 0.85,
      "overall_quality": 0.82
    },
    "user_feedback": {
      "thumbs_up": 892,
      "thumbs_down": 38,
      "satisfaction_rate": 0.959
    }
  },
  "alerts": [
    {
      "severity": "warning",
      "metric": "data_grounded",
      "message": "Pass rate dropped from 0.92 to 0.88 in last 24h",
      "detected_at": "2024-01-24T14:30:00Z"
    }
  ],
  "lakehouse_monitor_url": "https://workspace.databricks.com/ml/lakehouse-monitoring/..."
}
```

**Implementation Options**:
- **Option A (Demo)**: Return hardcoded metrics
- **Option B (Real)**: Query Lakehouse Monitoring tables

---

#### 8. GET `/api/dc-assistant/notebook-links`
**Purpose**: Return Databricks notebook URLs for each demo section
**Frontend Usage**: All sections - "View Notebook" buttons
**Response**:
```json
{
  "observe_tracing": "https://workspace.databricks.com/notebooks/01_observe_dc_assistant",
  "create_judges": "https://workspace.databricks.com/notebooks/02_create_judges",
  "collect_labels": "https://workspace.databricks.com/notebooks/03_labeling_sessions",
  "align_judges": "https://workspace.databricks.com/notebooks/04_judge_alignment",
  "optimize_prompts": "https://workspace.databricks.com/notebooks/05_gepa_optimization",
  "production_monitoring": "https://workspace.databricks.com/notebooks/06_production_monitoring"
}
```

**Implementation Notes**:
- Can hardcode these URLs
- Or read from environment variable: `NOTEBOOK_BASE_PATH`

---

### How to Implement Endpoints

**File Structure**:
```python
# server/routes/dc_assistant.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix='/api/dc-assistant', tags=['dc-assistant'])

# Response models
class ExperimentInfo(BaseModel):
    experiment_id: str
    experiment_name: str
    tracking_uri: str
    workspace_url: str

class Trace(BaseModel):
    trace_id: str
    question: str
    response: str
    tools_used: list[str]
    timestamp: str
    mlflow_url: str

# ... more models

@router.get('/experiment-info', response_model=ExperimentInfo)
async def get_experiment_info():
    """Return DC Assistant experiment metadata."""
    return ExperimentInfo(
        experiment_id=os.getenv('MLFLOW_EXPERIMENT_ID'),
        experiment_name="DC Assistant Demo",
        tracking_uri="databricks",
        workspace_url=os.getenv('DATABRICKS_HOST')
    )

@router.get('/traces')
async def get_traces():
    """Return sample traces."""
    # Option A: Hardcoded demo data
    return {"traces": PRELOADED_TRACES}

    # Option B: Real MLflow query
    # import mlflow
    # traces = mlflow.search_traces(...)
    # return format_traces(traces)

# ... implement other endpoints
```

**Then update** `server/app.py`:
```python
from .routes import email, helper, dc_assistant  # Add dc_assistant

app.include_router(dc_assistant.router)  # Add this line
```

---

## TODO #2: Create Preloaded Demo Data

**Priority**: HIGH
**Estimated Effort**: 2-3 hours
**File to Create**: `server/data/dc_assistant_preloaded.py`

### Purpose
Store hardcoded sample data for demo purposes (Option A above)

### Structure
```python
# server/data/dc_assistant_preloaded.py

PRELOADED_TRACES = [
    {
        "trace_id": "tr-sample-001",
        "question": "Who gets the ball for Cowboys in 11 personnel on 3rd and 6?",
        "response": "Historically, the Cowboys target CeeDee Lamb in 11 personnel on 3rd and medium situations...",
        "tools_used": ["get_target_stats", "get_play_success_rate", "get_formation_tendencies"],
        "timestamp": "2024-01-24T10:30:00Z",
        "mlflow_url": "https://e2-demo-field-eng.cloud.databricks.com/ml/experiments/2517718719552044/traces?selectedEvaluationId=tr-sample-001"
    },
    # ... 4-5 more traces
]

PRELOADED_JUDGES = [
    {
        "name": "football_language",
        "title": "Football Language Judge",
        "description": "Evaluates use of correct NFL terminology",
        "pass_rate": 0.72,
        "sample_evaluations": [
            {
                "input": "What defense should we run?",
                "output": "You should run a Cover 2 defense with outside leverage",
                "score": "pass",
                "reasoning": "Uses specific coverage terminology (Cover 2) and technical concepts (outside leverage)"
            }
        ]
    },
    # ... more judges
]

# ... more preloaded data structures
```

### Import in routes:
```python
# In server/routes/dc_assistant.py
from server.data.dc_assistant_preloaded import (
    PRELOADED_TRACES,
    PRELOADED_JUDGES,
    PRELOADED_LABELING_SESSIONS,
    # ...
)
```

---

## TODO #3: Create Validation Script

**Priority**: MEDIUM
**Estimated Effort**: 1-2 hours
**File to Create**: `server/validate_setup.py`

### Purpose
Verify all configuration and resources before deployment

### Implementation
```python
# server/validate_setup.py

import os
import sys
import mlflow
from databricks.sdk import WorkspaceClient

def validate_environment():
    """Check all required environment variables are set."""
    required_vars = [
        'MLFLOW_EXPERIMENT_ID',
        'UC_CATALOG',
        'UC_SCHEMA',
        'MODEL_ENDPOINT_NAME',
        'DATABRICKS_HOST',
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False

    print("✅ All required environment variables set")
    return True

def validate_mlflow_access():
    """Test MLflow experiment access."""
    try:
        exp_id = os.getenv('MLFLOW_EXPERIMENT_ID')
        mlflow.set_experiment(experiment_id=exp_id)
        print(f"✅ MLflow experiment accessible: {exp_id}")
        return True
    except Exception as e:
        print(f"❌ MLflow experiment access failed: {e}")
        return False

def validate_model_endpoint():
    """Check if model endpoint exists and is serving."""
    try:
        w = WorkspaceClient()
        endpoint_name = os.getenv('MODEL_ENDPOINT_NAME')
        endpoint = w.serving_endpoints.get(endpoint_name)

        if endpoint.state.ready == "READY":
            print(f"✅ Model endpoint ready: {endpoint_name}")
            return True
        else:
            print(f"⚠️  Model endpoint exists but not ready: {endpoint.state.ready}")
            return False
    except Exception as e:
        print(f"❌ Model endpoint check failed: {e}")
        return False

def validate_uc_resources():
    """Validate Unity Catalog access."""
    try:
        w = WorkspaceClient()
        catalog = os.getenv('UC_CATALOG')
        schema = os.getenv('UC_SCHEMA')

        # Check catalog exists
        w.catalogs.get(catalog)
        print(f"✅ Unity Catalog accessible: {catalog}")

        # Check schema exists
        w.schemas.get(f"{catalog}.{schema}")
        print(f"✅ Schema accessible: {catalog}.{schema}")

        return True
    except Exception as e:
        print(f"❌ Unity Catalog access failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Validating DC Assistant Demo Setup...\n")

    checks = [
        validate_environment(),
        validate_mlflow_access(),
        validate_model_endpoint(),
        validate_uc_resources(),
    ]

    if all(checks):
        print("\n✅ All validations passed! Ready to deploy.")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed. Fix issues before deploying.")
        sys.exit(1)
```

**Run before deployment**:
```bash
python server/validate_setup.py
```

---

## TODO #4: Update README Documentation

**Priority**: LOW
**Estimated Effort**: 30 minutes
**File**: `README.md`

### Updates Needed
- [ ] Replace email demo references with DC Assistant
- [ ] Update setup instructions for DC Assistant use case
- [ ] Add link to CONFIGURATION_GUIDE.md
- [ ] Add link to TODO_REMAINING_WORK.md
- [ ] Update screenshots (if any)

---

## TODO #5: Clean Up Old Email Demo Code (Optional)

**Priority**: LOW
**Estimated Effort**: 1 hour

### Files to Consider
- `server/routes/email.py` - Keep or remove? (Not breaking anything)
- `mlflow_demo/agent/email_generator.py` - Email-specific code
- `mlflow_demo/data/input_data.jsonl` - Email customer data

**Recommendation**: Leave for now - not hurting anything, can remove later

---

## Implementation Priority Order

### Phase 1: Minimum Viable Demo (Must Have)
1. ✅ Create `server/routes/dc_assistant.py` with hardcoded responses
2. ✅ Create `server/data/dc_assistant_preloaded.py` with sample data
3. ✅ Update `server/app.py` to include DC Assistant routes
4. ✅ Test locally
5. ✅ Deploy to Databricks App

**Result**: App works end-to-end with mock data

### Phase 2: Real Data Integration (Should Have)
6. 🔄 Update endpoints to query real MLflow data
7. 🔄 Add error handling for missing resources
8. 🔄 Create validation script

**Result**: App shows actual experiment data

### Phase 3: Polish (Nice to Have)
9. 🔄 Update README
10. 🔄 Clean up old email code
11. 🔄 Add more sample traces/data

---

## Quick Start for Colleague

If your colleague needs to implement the backend:

### 1. Start with Endpoint Stubs (30 minutes)
```bash
# Create file
touch server/routes/dc_assistant.py

# Copy endpoint structure from email.py
# Replace with DC Assistant endpoints
# Return hardcoded JSON for now
```

### 2. Add Preloaded Data (1 hour)
```bash
# Create file
mkdir -p server/data
touch server/data/dc_assistant_preloaded.py

# Add sample traces, judges, sessions as Python dicts
# Copy examples from this TODO document
```

### 3. Wire Up Routes (5 minutes)
```python
# In server/app.py
from .routes import email, helper, dc_assistant
app.include_router(dc_assistant.router)
```

### 4. Test (15 minutes)
```bash
# Start backend
uvicorn server.app:app --reload

# Test endpoint
curl http://localhost:8000/api/dc-assistant/traces

# Should return JSON
```

### 5. Deploy
```bash
git add .
git commit -m "Add DC Assistant backend endpoints"
git push origin ui-dev
# Create Databricks App
```

**Total time**: ~3-4 hours for basic working demo

---

## Questions / Blockers?

If you hit issues:
1. Check CONFIGURATION_GUIDE.md for environment setup
2. Look at `server/routes/email.py` for endpoint pattern examples
3. Frontend expects specific JSON response shapes (see endpoint docs above)
4. Test locally before deploying to Databricks

---

## Summary Checklist

**Before deployment, verify**:
- [ ] `server/routes/dc_assistant.py` exists with 8 endpoints
- [ ] `server/data/dc_assistant_preloaded.py` has sample data
- [ ] `server/app.py` includes DC Assistant router
- [ ] All endpoints return valid JSON
- [ ] Local testing passes (frontend + backend)
- [ ] `app.yaml` has correct environment variables
- [ ] Frontend build is up to date (`client/build/`)

**When all checked**: Ready to deploy! 🚀
