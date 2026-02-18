# Manual Setup Guide

**Estimated time:**
- **Full App Deployment**: 15-20 minutes work + 15 minutes waiting for scripts to run
- **Notebook-Only**: 10-15 minutes work + 15 minutes waiting for scripts to run

## 🔧 Phase 1: Prerequisites Setup

> ⚠️ **IMPORTANT**: Complete ALL items in this phase before proceeding to Phase 2. Each prerequisite is required for the demo to work properly.

### 1.1 Databricks Workspace

- [ ] **Create or access a Databricks workspace**
  - If you don't have one, [create a workspace here](https://signup.databricks.com/?destination_url=/ml/experiments-signup?source=TRY_MLFLOW&dbx_source=TRY_MLFLOW&signup_experience_step=EXPRESS&provider=MLFLOW&utm_source=email_demo_github)
  - Verify access by logging into your workspace

### 1.2 Create MLflow Experiment

- [ ] **Create a new MLflow Experiment** in your workspace
- [ ] **Complete IDE setup** to get API credentials
  - Follow the [IDE setup guide](https://docs.databricks.com/aws/en/mlflow3/genai/getting-started/connect-environment)
  - You'll need these credentials for `setup.sh`

### 1.3 Unity Catalog Schema

- [ ] **Create or select a Unity Catalog schema** with proper permissions
  - You need **ALL** and **MANAGE** permissions on the schema
  - See [Unity Catalog schema documentation](https://docs.databricks.com/aws/en/schemas/create-schema)
  - **Quick option**: If you created a workspace in step 1.1, you can use the `workspace.default` schema

### 1.4 Install & Connect Databricks CLI

- [ ] **Install the Databricks CLI**
  - Follow the [installation guide](https://docs.databricks.com/aws/en/dev-tools/cli/install)
  - **Verify installation**: Run `databricks --version` to confirm it's installed
- [ ] **Authenticate with your workspace**
  - Run `databricks auth login` and follow the prompts

### ✅ Prerequisites Checkpoint

Before proceeding to Phase 2, verify you have:

- [ ] Access to a Databricks workspace
- [ ] An MLflow experiment and API credentials
- [ ] A Unity Catalog schema with proper permissions
- [ ] Databricks CLI installed and authenticated

---

## 🚀 Phase 2: Choose Your Experience

> ⚠️ **IMPORTANT**: Choose your deployment mode before proceeding. This determines which steps you'll follow.

Both options include the complete MLflow evaluation setup:
• MLflow Experiment with sample traces, evaluation runs, prompts, and production monitoring
• DC Assistant agent code with NFL play-by-play sample data
• Interactive notebooks that walk you through using MLflow to improve GenAI quality

**Choose how you want to interact with the demo:**

### Option 1: 📱 Full Databricks App (Recommended)
- **Best for**: Workspaces where Databricks Apps are enabled
- **What you get**:
  - User-friendly web UI for exploring MLflow workflows
  - Interactive DC Assistant demo for trying the agent
  - All notebooks for deeper exploration
- **Requirements**: Databricks Apps enabled in your workspace
- **Continue to**: Phase 3.1 (Full App Setup)

### Option 2: 📓 Notebooks Only
- **Best for**: Workspaces where Databricks Apps are restricted/disabled
- **What you get**:
  - Step-by-step interactive notebooks for learning
  - All MLflow evaluation features
  - Complete demo functionality via notebooks
- **Requirements**: Basic workspace access
- **Continue to**: Phase 3.2 (Notebook-Only Setup)

---

## ⚙️ Phase 3: Setup & Configuration

### 3.1 Full App Setup Path

> ⚠️ **Only follow this section if you chose Option 1 (Full Databricks App) above**

#### 3.1.1 Create Databricks App

- [ ] **Create a new Databricks App** using the custom app template
  - Follow the [Databricks Apps getting started guide](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started)
  - **Important**: Note down the app name and workspace directory (you'll need these for `setup.sh`)

**Continue to Phase 4: Environment Setup**

### 3.2 Notebook-Only Setup Path

> ⚠️ **Only follow this section if you chose Option 2 (Notebooks Only) above**

#### 3.2.1 Choose Workspace Location

- [ ] **Decide on notebook location**: `/Workspace/Users/[your-email]/mlflow-demo/`
- [ ] **No app creation needed** - notebooks will be synced directly to your workspace

#### 3.2.2 MLflow Experiment Ready

- [ ] **✅ MLflow experiment already created** in Phase 1 prerequisites
- [ ] **✅ API credentials already configured** for setup script

#### 3.2.3 Skip App-Specific Steps

- [ ] ✅ No Databricks App to create
- [ ] ✅ No app permissions to configure
- [ ] ✅ Simplified deployment process

**Continue to Phase 4: Environment Setup**

---

## 🔧 Phase 4: Environment Setup

> ⚠️ **STOP**: Only proceed if you've completed Phase 3 for your chosen deployment mode.

Run these commands in order from the project root directory:

### 4.1 Setup Environment & Configure Environment Variables

```bash
./setup.sh
```

**What this script does:**
1. **Checks prerequisites** - Validates Python ≥3.10.16, uv, Databricks CLI ≥0.262.0, and bun
2. **Installs missing tools** - Automatically installs uv and bun if not present (asks for confirmation first)
3. **Configures environment** - Prompts you for deployment mode and configuration
4. **Installs dependencies** - Sets up Python packages with uv and frontend packages with bun

**What the script will ask for:**
- Your deployment mode choice (full app vs notebook-only)
- App name (if full deployment) or workspace path (if notebook-only)
- MLflow experiment ID (from Phase 1 prerequisites)
- Unity Catalog schema information
- LLM model selection

### 4.2 Load Sample Data

```bash
./load_sample_data.sh
```

**Both deployment modes get:**
- ✅ MLflow experiment with sample data
- ✅ Evaluation datasets and prompts
- ✅ Trace examples and monitoring setup
- ✅ Sample customer data for the demo

### 4.3 Test Local Development Server

```bash
./watch.sh
```

- Starts both backend (port 8000) and frontend development servers
- Visit `http://localhost:8000` to verify the demo works locally
- **Success criteria**: You should see the DC Assistant interface and be able to ask questions about NFL play-calling tendencies

### ✅ Environment Setup Checkpoint

Verify your setup:

- [ ] Environment variables configured successfully
- [ ] Sample data loaded without errors
- [ ] Local server runs and demo interface loads
- [ ] Can ask the DC Assistant questions locally (test the core functionality)

---

## 🚀 Phase 5: Deployment

> ⚠️ **STOP**: Only proceed if Phase 4 completed successfully and the DC Assistant works locally.

### 5.1 Deploy Based on Your Mode

#### For Full App Deployment:

> ⚠️ **Only follow this section if you chose Full Databricks App in Phase 2**

##### Configure App Permissions (Before Deployment)

Your Databricks App needs specific permissions to access the MLflow experiment and other resources.

**Get Your App's Service Principal:**

1. Go to your Databricks workspace → Compute → Apps
2. Find your app and click on it
3. Go to the **Authorization** tab
4. **Copy the service principal name** (you'll need this for the next steps)

**Grant Required Permissions:**

**MLflow Experiment Access:**
- [ ] Go to your MLflow experiment → Permissions tab
- [ ] Grant **CAN MANAGE** (or higher) to your app's service principal
- [ ] This enables tracing and demo functionality

**Unity Catalog Schema Access:**
- [ ] Go to your Unity Catalog schema → Permissions tab
- [ ] Grant **ALL PERMISSIONS** to your app's service principal
- [ ] Grant **MANAGE** to your app's service principal
- [ ] ⚠️ **Important**: You need BOTH permissions - ALL does not include MANAGE
- [ ] This enables the prompt registry functionality

**Model Serving Endpoint Access:**
- [ ] Go to the Databricks App
- [ ] Click on **Edit**
- [ ] Click **Next**
- [ ] Click **Add Resource** and choose **Serving Endpoint**
- [ ] Select your model serving endpoint (`databricks-claude-3-7-sonnet` unless you changed the model)
- [ ] Press **Save**
- [ ] This allows the app to call the LLM for the DC Assistant

##### Deploy the App

```bash
./deploy.sh
```

**This script will:**
- Package your application code
- Upload it to your Databricks App
- Configure the necessary environment variables
- Start the app in your Databricks workspace

#### For Notebook-Only Deployment:

> ⚠️ **Only follow this section if you chose Notebooks Only in Phase 2**

##### Sync Notebooks to Workspace

```bash
./deploy.sh --sync-only
```

**This script will:**
- Sync notebooks to your workspace location
- Skip app deployment steps
- Provide direct notebook URLs for easy access
- Configure MLflow experiment automatically

### 5.2 Verify Your Deployment

#### Full App Success:

After deployment completes:
- [ ] Check that your app shows as **ACTIVE** in Databricks Apps console
- [ ] Visit your app URL (provided in deploy script output)
- [ ] Test the DC Assistant functionality in the web interface
- [ ] Verify that traces appear in your MLflow experiment

#### Notebook-Only Success:

After sync completes:
- [ ] Notebooks are visible in your workspace at `/Workspace/Users/[your-email]/mlflow-demo/`
- [ ] Demo overview notebook opens correctly
- [ ] Can run notebook cells successfully
- [ ] MLflow experiment contains sample data

---

## 🎉 You're Ready!

### Full App Experience:

Your app is live! You should be able to:
- [ ] Access the app via the Databricks Apps URL
- [ ] Ask the DC Assistant questions about NFL play-calling tendencies
- [ ] See traces and experiments in MLflow
- [ ] Use all demo features (evaluation, labeling, monitoring, etc.)
- [ ] Explore the interactive web interface

**🎯 Your App URL**: Check the deploy script output for the direct link

### Notebook-Only Experience:

Your demo is ready! You should be able to:
- [ ] Access notebooks in your workspace
- [ ] Follow the step-by-step interactive guide
- [ ] Learn MLflow evaluation workflows
- [ ] Explore all demo features via notebooks
- [ ] Run your own experiments using the provided examples

**🎯 Start Here**: `/Workspace/Users/[your-email]/mlflow-demo/notebooks/0_demo_overview.ipynb`

---

## 🆘 Troubleshooting

### Common Issues by Deployment Mode

**Full App Deployment Issues:**
- **Permission Issues**: Verify your app's service principal has all required permissions
- **App Not Starting**: Check that your app was created successfully in Databricks Apps
- **Deployment Fails**: Review the deploy script output for specific error messages
- **Model Access**: Ensure your app has access to the selected LLM serving endpoint

**Notebook-Only Issues:**
- **Notebooks Not Syncing**: Verify your workspace path permissions
- **MLflow Not Working**: Check that your experiment was created successfully
- **Cells Not Running**: Ensure your Databricks CLI is authenticated properly

**General Issues:**
- **Environment Setup**: Check that you're using the correct schema name in your config
- **Local Development**: Ensure all prerequisites are completed before running commands
- **Authentication**: Verify CLI authentication: `databricks auth login`
- **Dependencies**: If dependencies fail, try running `uv sync` and `bun install` manually

### Getting Help

If you continue to experience issues:
1. Check the specific error messages in the script output
2. Verify all prerequisites are met for your chosen deployment mode
3. Ensure your Databricks workspace has the required features enabled
4. Try the automated setup: `python auto-setup.py` for a guided experience
