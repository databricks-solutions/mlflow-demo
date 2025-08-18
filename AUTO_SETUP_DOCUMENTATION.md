# MLflow Demo Auto-Setup System Documentation

## Overview

The MLflow Demo auto-setup system is a comprehensive, automated deployment solution that handles the entire end-to-end setup process for the MLflow demo application. It consists of a bash wrapper script (`auto-setup.sh`) and a Python orchestrator (`auto-setup.py`) with supporting automation modules.

## Architecture

```
auto-setup.sh (Bash Wrapper)
    ├── Environment validation (uv, bun, Python, Databricks CLI)
    ├── Dependency installation
    └── Calls auto-setup.py

auto-setup.py (Main Orchestrator)
    ├── progress_tracker.py (Resume capability)
    ├── environment_detector.py (Auto-discovery)
    ├── resource_manager.py (Databricks resources)
    └── validation.py (Pre/post checks)
```

## System Components

### 1. auto-setup.sh (Bash Wrapper)

**Purpose**: Handles system-level prerequisites and environment setup before running the Python automation.

**Key Features**:
- **Tool Installation**: Automatically installs `uv` and `bun` if missing
- **Version Validation**: Ensures Python ≥3.10.16 and Databricks CLI ≥0.262.0
- **Dependency Management**: Runs `uv sync` and `bun install` with progress spinners
- **Environment Activation**: Sets up Python virtual environment and passes control to Python script

**Flow**:
1. Check and install `uv` package manager
2. Validate Python version (≥3.10.16)
3. Validate Databricks CLI version (≥0.262.0)
4. Install Python dependencies via `uv sync`
5. Install/ensure `bun` is available
6. Install frontend dependencies via `bun install`
7. Activate virtual environment and call `auto-setup.py`

### 2. auto-setup.py (Main Orchestrator)

**Purpose**: Orchestrates the complete setup workflow with intelligent discovery, user interaction, and resumable progress tracking.

**Key Features**:
- **Interactive Setup Modes**: 
  - Full App Deployment (complete web app)
  - Notebook-Only Experience (learning mode)
- **Smart Discovery**: Auto-detects workspace settings, available resources, and permissions
- **Resume Capability**: Can resume from any failed step using progress tracking
- **Permission Verification**: Tests actual CREATE/MANAGE permissions, not just read access
- **Dry Run Mode**: Shows what would be created without executing

**Workflow Steps**:
1. **validate_prerequisites** - CLI auth, tools, workspace connectivity
2. **detect_environment** - Auto-discover workspace URL, catalogs, schemas
3. **collect_user_input** - Interactive selection of deployment mode, resources, models
4. **validate_config** - Validate user configuration
5. **create_catalog_schema** - Create Unity Catalog resources if needed
6. **create_experiment** - Create MLflow experiment for tracking
7. **create_app** - Create Databricks App resource
8. **generate_env_file** - Generate `.env.local` with complete configuration
9. **install_dependencies** - Install Python and frontend dependencies
10. **load_sample_data** - Run setup scripts (1-5) to populate data
11. **validate_local_setup** - Test local development server
12. **deploy_app** - Deploy application using `./deploy.sh`
13. **setup_permissions** - Configure app service principal permissions
14. **validate_deployment** - Test deployed app functionality
15. **run_integration_tests** - End-to-end functionality tests

## Supporting Modules

### progress_tracker.py

**Purpose**: Provides resumable setup with persistent progress tracking.

**Key Features**:
- **Step Dependencies**: Enforces proper execution order
- **State Persistence**: Saves progress to `.setup_progress.json`
- **Resume Logic**: Can restart from any failed step
- **Detailed Reporting**: Shows step duration, errors, and overall progress

**Step States**:
- `PENDING` - Not yet started
- `IN_PROGRESS` - Currently executing
- `COMPLETED` - Successfully finished
- `FAILED` - Encountered error
- `SKIPPED` - Intentionally bypassed

### environment_detector.py

**Purpose**: Auto-discovers optimal Databricks workspace settings and suggests configurations.

**Discovery Capabilities**:
- **Workspace URL**: From CLI config, environment variables, or SDK
- **Available Catalogs**: Lists accessible Unity Catalog catalogs
- **Schema Permissions**: Checks read/write/manage access levels
- **Existing Apps**: Discovers manageable Databricks Apps
- **LLM Models**: Auto-detects available chat completion endpoints
- **Unique Naming**: Generates conflict-free resource names

**Smart Suggestions**:
- Prioritizes common patterns (workspace.default, main.default)
- Avoids hive_metastore for Unity Catalog features
- Generates unique names with timestamp suffixes

### resource_manager.py

**Purpose**: Creates and configures all Databricks resources with proper error handling.

**Resource Management**:
- **Unity Catalog**: Creates catalogs and schemas with permission checks
- **MLflow Experiments**: Uses workspace-scoped experiments (/Shared/{app_name})
- **Databricks Apps**: Creates apps with proper source code paths
- **Permission Grants**: Uses SQL GRANT statements for catalog/schema permissions
- **Service Principal Integration**: Maps display names to application IDs

**Permission Strategy**:
- **Catalog**: USE CATALOG permissions
- **Schema**: ALL_PRIVILEGES + MANAGE permissions
- **Experiments**: CAN_MANAGE permissions using application_id
- **Model Serving**: CAN_QUERY permissions (Foundation Models get default access)

### validation.py

**Purpose**: Comprehensive validation for prerequisites, configuration, and deployment health.

**Validation Phases**:
- **Prerequisites**: CLI auth, required tools, workspace connectivity
- **Environment Config**: Required variables, URL formats, ID validation
- **Resource Creation**: Verifies created resources are accessible
- **Deployment Health**: App status, health endpoints, basic functionality
- **Integration Tests**: End-to-end workflow validation

## Interactive Features

### Deployment Mode Selection
```
🚀 Choose Your Experience
1. 📱 Full App Deployment
   • Complete web application with interactive UI
   • Deployed as Databricks App for sharing
   • Requires app deployment permissions

2. 📓 Notebook-Only Experience  
   • Interactive Jupyter notebooks in workspace
   • No app deployment required
   • Perfect for learning and experimentation
```

### Permission-Verified Resource Selection

The system performs **actual permission testing**, not just listing:

- **Catalog Selection**: Tests CREATE SCHEMA permission by creating/deleting test schemas
- **Schema Selection**: Verifies MANAGE + CREATE TABLE permissions
- **App Management**: Confirms actual MANAGE permissions on existing apps
- **Model Access**: Detects available chat completion endpoints

### Authentication Management

Enforces DEFAULT profile usage for consistency:
- Lists available authentication profiles
- Validates DEFAULT profile exists and is authenticated
- Guides users through profile setup if needed
- Tests authentication before proceeding

## Error Handling & Recovery

### Resume Capability
```bash
# Resume from last successful step
python auto-setup.py --resume

# Reset all progress and start fresh  
python auto-setup.py --reset

# Show current setup status
python auto-setup.py --status
```

### Graceful Degradation
- **Permission Failures**: Falls back to manual instructions with step-by-step guides
- **Tool Missing**: Offers installation prompts with fallback options
- **Resource Conflicts**: Provides options to update existing or create new resources
- **Service Errors**: Captures detailed error information for troubleshooting

### Manual Fallback Instructions
When automated steps fail, the system provides detailed manual instructions:
```
📋 Manual steps:
   1. Go to Unity Catalog → {catalog} → Permissions tab
   2. Grant CREATE SCHEMA to service principal: {principal}
   
⏸️  Please complete the manual setup, then press Enter to continue...
```

## Command Line Interface

### Available Options
```bash
# Normal setup
./auto-setup.sh

# Python script options
python auto-setup.py --dry-run          # Show what would be created
python auto-setup.py --resume           # Resume from previous failure
python auto-setup.py --reset            # Reset all progress
python auto-setup.py --validate-only    # Only run validation checks
python auto-setup.py --status           # Show current progress
python auto-setup.py --cleanup          # Clean up progress file
```

### Progress Tracking
The system maintains detailed progress in `.setup_progress.json`:
```json
{
  "session_id": "20241216_143022",
  "last_updated": "2024-12-16T14:32:45.123456",
  "current_step": "create_experiment",
  "steps": {
    "validate_prerequisites": {
      "status": "completed",
      "duration_seconds": 12.3,
      "result_data": {"config": {...}}
    }
  }
}
```

## Configuration Generation

The system generates a complete `.env.local` file with all required configuration:

```bash
# Generated by auto-setup.py on 2024-12-16 14:32:45

DATABRICKS_HOST="https://workspace.cloud.databricks.com"
UC_CATALOG="workspace"
UC_SCHEMA="default"
DATABRICKS_APP_NAME="mlflow_demo_app"
MLFLOW_EXPERIMENT_ID="123456789"
LLM_MODEL="databricks-claude-3-7-sonnet"
DEPLOYMENT_MODE="full_deployment"

# Fixed configuration values
MLFLOW_ENABLE_ASYNC_TRACE_LOGGING="false"
PROMPT_NAME="email_generation"
PROMPT_ALIAS="production"
MLFLOW_TRACKING_URI="databricks"
```

## Sample Data Loading

The system executes setup scripts in sequence:
1. `1_load_prompts.py` - Load prompt templates
2. `2_load_sample_traces.py` - Generate sample MLflow traces
3. `3_run_evals_for_sample_traces.py` - Run evaluations on traces
4. `4_setup_monitoring.py` - Configure monitoring dashboards
5. `5_setup_labeling_session.py` - Set up human labeling workflows

Each script runs with real-time output streaming and proper error handling.

## Security Considerations

### Permission Principle
- **Least Privilege**: Only grants minimum required permissions
- **Service Principal Focus**: Uses app service principals, not user accounts
- **Permission Verification**: Tests actual permissions before proceeding
- **Manual Fallback**: Provides manual steps when automated grants fail

### Sensitive Data Handling
- **No Hardcoded Secrets**: All authentication uses Databricks CLI profiles
- **Environment Isolation**: Uses virtual environments and workspace-scoped resources
- **Cleanup Capability**: Can remove created resources for rollback

## Success Indicators

### Full App Deployment Success
```
🎉 Setup completed successfully!

📋 Summary:
   • MLflow Experiment ID: 123456789
   • Databricks App: mlflow_demo_app
   • Unity Catalog: workspace.default

🚀 Next steps:
   1. Your app is now deployed and ready to use
   2. Check the Databricks Apps section in your workspace
   3. Test the email generation functionality
   4. Explore the MLflow experiment for traces and evaluations
```

### Notebook-Only Success
```
🚀 Next steps:
   1. Open the demo notebook: 0_demo_overview.ipynb in your Databricks workspace
   2. Navigate to mlflow_demo/notebooks/ in your workspace
   3. Follow the interactive notebook guide to learn MLflow evaluation
   4. Explore the MLflow experiment for traces and evaluations
   5. Workspace path: /Workspace/Users/{user}/mlflow_demo_app
```

## Troubleshooting

### Common Issues & Solutions

**CLI Authentication**:
```bash
databricks auth login --profile DEFAULT
```

**Permission Denied**:
- Check Unity Catalog permissions (CREATE SCHEMA required)
- Verify workspace admin privileges for catalog creation
- Use existing catalogs/schemas with proper permissions

**Tool Installation Failures**:
```bash
# Manual uv installation
curl -LsSf https://astral.sh/uv/install.sh | sh

# Manual bun installation  
curl -fsSL https://bun.sh/install | bash
```

**Resume After Failures**:
```bash
python auto-setup.py --resume
```

The auto-setup system is designed to be robust, user-friendly, and capable of handling complex Databricks workspace configurations while providing clear feedback and recovery options throughout the process.