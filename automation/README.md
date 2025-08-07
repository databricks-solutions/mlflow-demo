# MLflow Demo Automation System

This directory contains the automated setup system that streamlines the entire MLflow demo installation process using the Databricks Workspace SDK.

## Overview

The automation system reduces the manual setup from 30+ steps across multiple scripts to a single command that handles:

- **Resource Creation**: Databricks Apps, MLflow experiments, Unity Catalog schemas
- **Permission Management**: Automatic configuration of service principal permissions  
- **Environment Detection**: Auto-discovery of workspace settings and intelligent defaults
- **Progress Tracking**: Resume capability and detailed progress reporting
- **Validation**: Pre/post setup validation and integration testing

## Components

### Core Modules

- **`resource_manager.py`** - Databricks SDK operations for resource creation
- **`environment_detector.py`** - Workspace auto-discovery and intelligent defaults
- **`validation.py`** - Pre/post setup validation and health checks
- **`progress_tracker.py`** - Progress tracking and resume functionality

### Main Script

- **`auto-setup.py`** - Main orchestration script that coordinates all automation

## Usage

### Basic Setup

```bash
# Run complete automated setup
python auto-setup.py

# Dry run to see what would be created
python auto-setup.py --dry-run

# Resume from previous failed setup
python auto-setup.py --resume
```

### Advanced Options

```bash
# Reset progress and start fresh
python auto-setup.py --reset

# Only run validation checks
python auto-setup.py --validate-only

# Show current progress status
python auto-setup.py --status

# Clean up progress file
python auto-setup.py --cleanup
```

## Setup Steps

The automation system executes these steps in order:

1. **Validate Prerequisites** - CLI auth, tools, workspace connectivity
2. **Detect Environment** - Auto-discover catalogs, schemas, workspace settings
3. **Collect User Input** - Minimal configuration prompts with intelligent defaults
4. **Validate Configuration** - Ensure all settings are valid
5. **Create Catalog & Schema** - Unity Catalog resource creation
6. **Create MLflow Experiment** - Experiment for tracking and evaluation
7. **Create Databricks App** - App resource for deployment
8. **Setup Permissions** - Configure service principal permissions
9. **Generate Environment File** - Create `.env.local` with all settings
10. **Install Dependencies** - Python (uv) and frontend (bun) dependencies
11. **Load Sample Data** - Run existing setup scripts for data loading
12. **Validate Local Setup** - Test local development server
13. **Deploy Application** - Build and deploy to Databricks Apps
14. **Validate Deployment** - Test deployed app functionality
15. **Integration Tests** - End-to-end functionality verification

## Resume Functionality

If setup fails or is interrupted:

- Progress is automatically saved to `.setup_progress.json`
- Use `--resume` to continue from the last successful step
- Use `--status` to see detailed progress information
- Failed steps can be retried individually

## Error Handling

- **Graceful Degradation** - Non-critical failures don't stop setup
- **Resource Cleanup** - Automatic rollback of partially created resources
- **Detailed Logging** - Comprehensive error messages and troubleshooting hints
- **Permission Fallbacks** - Continues with manual permission setup if automation fails

## Configuration

### Minimal Required Input

- Databricks workspace URL (auto-detected if possible)
- Personal access token
- Confirmation of suggested Unity Catalog settings

### Auto-Detected Settings

- Available catalogs and schemas
- Workspace user information
- Unique resource names
- Optimal configurations

### Environment Variables Generated

All standard environment variables from the manual setup process, plus additional automation-specific settings.

## Validation System

### Prerequisites Validation

- Databricks CLI authentication
- Required tools (uv, bun, databricks CLI)
- Workspace connectivity
- Unity Catalog access
- MLflow permissions
- Apps functionality

### Post-Setup Validation

- Resource accessibility
- Permission verification
- Health endpoint testing
- Basic functionality testing
- Integration test suite

## Progress Tracking

### Features

- **Step Dependencies** - Ensures correct execution order
- **Time Tracking** - Duration measurement for each step
- **Result Storage** - Preserves important data between steps
- **Status Reporting** - Detailed progress visualization
- **Resume Points** - Smart continuation from failures

### Progress File

The `.setup_progress.json` file contains:
- Step status and timing information
- Error messages and results
- Session metadata
- Resource creation details

## Error Recovery

### Common Scenarios

1. **Permission Errors** - Provides manual permission setup instructions
2. **Network Issues** - Retry logic with exponential backoff
3. **Resource Conflicts** - Automatic name collision resolution
4. **Tool Missing** - Clear installation instructions
5. **Partial Deployment** - Resume from deployment step

### Rollback Capability

- Automatic cleanup of partially created resources
- Safe rollback without affecting existing workspace resources
- Option to retry individual steps after fixing issues

## Development

### Adding New Steps

1. Add step definition to `ProgressTracker._initialize_steps()`
2. Implement step handler in `AutoSetup.run_setup()`
3. Add validation logic if needed
4. Update dependencies between steps

### Testing

Each module can be tested independently:

```bash
# Test resource manager
python -c "from automation.resource_manager import DatabricksResourceManager; rm = DatabricksResourceManager()"

# Test environment detection
python -c "from automation.environment_detector import EnvironmentDetector; ed = EnvironmentDetector()"
```

## Architecture

The system follows a modular architecture:

```
auto-setup.py (Orchestrator)
├── ProgressTracker (State Management)
├── ResourceManager (Databricks SDK)
├── EnvironmentDetector (Auto-Discovery)
└── SetupValidator (Validation & Testing)
```

Each component is designed to be:
- **Independent** - Can be used standalone
- **Testable** - Clear interfaces and error handling
- **Extensible** - Easy to add new functionality
- **Reliable** - Comprehensive error handling and recovery