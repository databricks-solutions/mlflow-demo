# MLflow 3 GenAI Demo

A comprehensive demonstration of **MLflow 3's GenAI capabilities** for observability and evaluating, monitoring, and improving GenAI application quality. This interactive demo showcases a sales email generation use case with end-to-end quality assessment workflows.

This interactive demo is deployed as a Databricks app in your Databricks workspace. There is a guided UI experience that's accompanied by Notebooks that show you how to do the end-to-end workflow of evaluating quality, iterating to improve quality, and monitoring quality in production.

**Learn more about MLflow 3:**

- Read the [blog post](https://www.databricks.com/blog/mlflow-30-unified-ai-experimentation-observability-and-governance)
- View our [website](https://www.managed-mlflow.com/genai)
- Get started via the [documentation](https://docs.databricks.com/aws/en/mlflow3/genai/)

<img width="1723" alt="image" src="https://i.imgur.com/MXhaayF.gif" />

## Installing the demo

**Estimated time: 10 minutes work + 10 minutes waiting for scripts to run**

## 🔧 Phase 1: Prerequisites Setup

> ⚠️ **IMPORTANT**: Complete ALL items in this phase before proceeding to Phase 2. Each prerequisite is required for the demo to work properly.

### 1.1 Databricks Workspace

- [ ] **Create or access a Databricks workspace**
  - If you don't have one, [create a workspace here](https://signup.databricks.com/?destination_url=/ml/experiments-signup?source=TRY_MLFLOW&dbx_source=TRY_MLFLOW&signup_experience_step=EXPRESS&provider=MLFLOW&utm_source=email_demo_github)
  - Verify access by logging into your workspace

### 1.2 Databricks App Setup

- [ ] **Create a new Databricks App** using the custom app template
  - Follow the [Databricks Apps getting started guide](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/get-started)
  - **Important**: Note down the app name and workspace directory (you'll need these for `setup.sh`)

### 1.3 Create MLflow Experiment

- [ ] **Create a new MLflow Experiment** in your workspace
- [ ] **Complete IDE setup** to get API credentials
  - Follow the [IDE setup guide](https://docs.databricks.com/aws/en/mlflow3/genai/getting-started/connect-environment)
  - You'll need these credentials for `setup.sh`

### 1.4 Unity Catalog Schema

- [ ] **Create or select a Unity Catalog schema** with proper permissions
  - You need **ALL** and **MANAGE** permissions on the schema
  - See [Unity Catalog schema documentation](https://docs.databricks.com/aws/en/schemas/create-schema)
  - **Quick option**: If you created a workspace in step 1.1, you can use the `workspace.default` schema

### 1.5 Install & Connect Databricks CLI

- [ ] **Install the Databricks CLI**
  - Follow the [installation guide](https://docs.databricks.com/aws/en/dev-tools/cli/install)
  - **Verify installation**: Run `databricks --version` to confirm it's installed
- [ ] **Authenticate with your workspace**
  - Run `databricks auth login` and follow the prompts

### ✅ Prerequisites Checkpoint

Before proceeding to Phase 2, verify you have:

- [ ] Access to a Databricks workspace
- [ ] A Databricks App created with name/directory noted
- [ ] An MLflow experiment and API credentials
- [ ] A Unity Catalog schema with proper permissions
- [ ] Databricks CLI installed and authenticated

---

## 🚀 Phase 2: Installation & Local Testing

> ⚠️ **STOP**: Only proceed if you've completed ALL items in Phase 1 above.

Run these commands in order from the project root directory:

### 2.1 Configure Environment Variables

```bash
./setup.sh
```

- This script will prompt you for all the information from Phase 1
- Have your app name, workspace directory, experiment ID, and schema name ready

### 2.2 Load Sample Data

```bash
./load_sample_data.sh
```

- Creates evaluation datasets in your MLflow experiment
- Loads sample customer data for the demo

### 2.3 Test Local Development Server

```bash
./watch.sh
```

- Starts both backend (port 8000) and frontend development servers
- Visit `http://localhost:8000` to verify the demo works locally
- **Success criteria**: You should see the email generation interface and be able to generate emails

### ✅ Local Testing Checkpoint

Verify your local setup:

- [ ] Environment variables configured successfully
- [ ] Sample data loaded without errors
- [ ] Local server runs and demo interface loads
- [ ] Can generate emails locally (test the core functionality)

---

## 🌐 Phase 3: Deployment to Databricks Apps

> ⚠️ **STOP**: Only proceed if Phase 2 completed successfully and you can generate emails locally.

### 3.1 Configure App Permissions

Your Databricks App needs specific permissions to access the the MLflow experiment and other resources in you created in the first steps.

#### Get Your App's Service Principal

1. Go to your Databricks workspace → Compute → Apps
2. Find your app and click on it
3. Go to the **Authorization** tab
4. **Copy the service principal name** (you'll need this for the next steps)

#### Grant Required Permissions

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

- [ ] Go the Databricks App
- [ ] Click on **Edit**
- [ ] Click **Next**
- [ ] Click **Add Resource** and choose **Serving Endpoint**
- [ ] Select your model serving endpoint (`databricks-claude-3-7-sonnet` unless you changed the model during the step above)
- [ ] Press **Save**
- [ ] This allows the app to call the LLM for email generation

### 3.2 Deploy the Application

```bash
./deploy.sh
```

**This script will:**

- Package your application code
- Upload it to your Databricks App
- Configure the necessary environment variables
- Start the app in your Databricks workspace

### 3.3 Verify Deployment

After deployment completes:

- [ ] Check that your app shows as **ACTIVE** in Databricks Apps
- [ ] Visit your app URL (provided in deploy script output)
- [ ] Test email generation functionality
- [ ] Verify that traces appear in your MLflow experiment

### ✅ Deployment Success

Your demo is now live! You should be able to:

- [ ] Access the app via the Databricks Apps URL
- [ ] Generate emails using the deployed application
- [ ] See traces and experiments in MLflow
- [ ] Use all demo features (prompt registry, evaluation, etc.)

---

## 🆘 Troubleshooting

**Permission Issues:**

- Verify your app's service principal has all required permissions
- Check that you're using the correct schema name in your environment config

**Local Development Issues:**

- Ensure all prerequisites are completed before running installation commands
- Check that your Databricks CLI is authenticated: `databricks auth login`

**Deployment Issues:**

- Verify your app was created successfully in Databricks Apps
- Check the deploy script output for specific error messages

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
