# MLflow 3 GenAI Demo

A comprehensive demonstration of **MLflow 3's GenAI capabilities** for observability and evaluating, monitoring, and improving GenAI application quality. This interactive demo showcases a sales email generation use case with end-to-end quality assessment workflows.

This interactive demo is deployed as a Databricks app in your Databricks workspace. There is a guided UI experience that's accompanied by Notebooks that show you how to do the end-to-end workflow of evaluating quality, iterating to improve quality, and monitoring quality in production.

**Learn more about MLflow 3:**

- Read the [blog post](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance)
- View our [website](https://www.managed-mlflow.com/genai)
- Get started via the [documentation](https://docs.databricks.com/aws/en/mlflow3/genai/)

<img width="1723" alt="image" src="https://i.imgur.com/MXhaayF.gif" />

## Installing the demo

Choose your installation method:

### 🤖 Option A: Automated Setup (Recommended)

**Estimated time: 5 minutes user input + 15 minutes automated setup**

The automated setup handles resource creation, configuration, and deployment for you using the Databricks Workspace SDK.

#### Prerequisites
- [ ] **Databricks workspace access** - [Create one here](https://signup.databricks.com/?destination_url=/ml/experiments-signup?source=TRY_MLFLOW&dbx_source=TRY_MLFLOW&signup_experience_step=EXPRESS&provider=MLFLOW&utm_source=email_demo_github) if needed
- [ ] **Databricks CLI installed and authenticated** - Run `databricks auth login`

#### Run Automated Setup
```bash
# Clone the repository and run automation
git clone https://github.com/databricks-solutions/mlflow-demo.git
cd mlflow-demo
./auto-setup
```

The automation will:
- ✅ Auto-detect workspace settings and suggest configurations
- ✅ Create Databricks App, MLflow experiment, and Unity Catalog resources
- ✅ Configure permissions automatically 
- ✅ Install dependencies and load sample data
- ✅ Deploy and validate the application

**Automation Features:**
- **Resume capability** - Continue from interruptions with `python auto-setup.py --resume`
- **Dry run mode** - Preview changes with `python auto-setup.py --dry-run`
- **Progress tracking** - See status with `python auto-setup.py --status`
- **Intelligent defaults** - Minimal user input required

---

### 🔧 Option B: Manual Setup

**Estimated time: 10 minutes work + 10 minutes waiting for scripts to run**

For step-by-step manual installation instructions, see **[MANUAL_SETUP.md](MANUAL_SETUP.md)**.

The manual setup includes:
- Phase 1: Prerequisites setup (workspace, app creation, MLflow experiment, etc.)
- Phase 2: Local installation and testing
- Phase 3: Deployment and permission configuration

---

## MLflow 3 overview

MLflow 3.0 has been redesigned for the GenAI era. If your team is building GenAI-powered apps, this update makes it dramatically easier to evaluate, monitor, and improve them in production.

### Key capabilities

- **🔍 GenAI Observability at Scale:** Monitor & debug GenAI apps anywhere \- deployed on Databricks or ANY cloud \- with production-scale real-time tracing and enhanced UIs. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/)
- 📊 **Revamped GenAI Evaluation:** Evaluate app quality using a brand-new SDK, simpler evaluation interface and a refreshed UI. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/)
- ⚙️ **Customizable Evaluation:** Tailor AI judges or custom metrics to your use case. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/custom-judge/)
- 👀 **Monitoring:** Schedule automatic quality evaluations (beta). [Link](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/run-scorer-in-prod)
- 🧪 **Leverage Production Logs to Improve Quality:** Turn real user traces into curated, versioned evaluation datasets to continuously improve app performance . [Link](https://docs.databricks.com/aws/en/mlflow3/genai/eval-monitor/build-eval-dataset)
- 📝 **Close the Loop with** **Feedback:** Capture end-user feedback from your app’s UI. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/tracing/collect-user-feedback/)
- **👥 Domain Expert Labeling:** Send traces to human experts for ground truth or target output labeling. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces)
- 📁 **Prompt Management:** Prompt Registry for versioning. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/create-and-edit-prompts)
- 🧩 **App Version Tracking:** Link app versions to quality evaluations. [Link](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/version-tracking/track-application-versions-with-mlflow)
