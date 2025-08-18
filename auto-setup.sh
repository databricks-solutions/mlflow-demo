#!/bin/bash

# Auto-setup wrapper script for MLflow Demo
# This script ensures the Python environment is set up before running auto-setup.py

set -e  # Exit on any error

# Check for --reset argument and handle it early
for arg in "$@"; do
    if [[ "$arg" == "--reset" ]]; then
        echo "🔄 Resetting all progress..."
        if [ -f ".setup_progress.json" ]; then
            rm .setup_progress.json
            echo "✅ Removed .setup_progress.json - setup will start fresh"
        else
            echo "✅ No progress file found - already reset"
        fi
        echo "Run auto-setup again to begin setup process."
        exit 0
    fi
done

echo "🚀 MLflow Demo"
echo "========================="
echo ""
echo "This creates sample GenAI application that shows you how to use MLflow to evaluate, improve, and monitor the app's quality."
echo " Sample application: Generate sales follow up emails based on retrieved customer data"
echo ""
echo "You will get:"
echo "• MLflow Experiment with sample traces, prompts, evaluation runs, and production monitoring"
echo "• Sales email generation app with sample data" 
echo "• Interactive notebooks that show how to use MLflow for quality evaluation and monitoring"
echo ""
echo "========================="
echo "Before we start, we will check/install the required prerequisites & initialize the Python/Typescript environments."
echo "========================="
echo ""

# Run prerequisites check and installation
echo "🔧 Checking and installing prerequisites..."
./install-prerequisites.sh
if [ $? -ne 0 ]; then
    echo "Please check the output above and try again."
    exit 1
fi

# Initialize Python and TypeScript environments
echo "📦 Initializing development environments..."
./initialize-environment.sh
if [ $? -ne 0 ]; then
    echo "Please check the output above and try again."
    exit 1
fi

echo ""

# Run the actual auto-setup script with all arguments passed through
echo "🔧 Running auto-setup.py..."
echo ""

# Activate the virtual environment and run auto-setup.py
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # Unix/Linux/macOS
    source .venv/bin/activate
fi

# Pass all command line arguments to the Python script
python auto-setup.py "$@"