#!/bin/bash

# Auto-setup wrapper script for MLflow Demo
# This script ensures the Python environment is set up before running auto-setup.py

set -e  # Exit on any error

echo "🚀 MLflow Demo Auto-Setup Wrapper"
echo "=================================="
echo ""
echo "This script will guide you through setting up the MLflow demo."
echo "You'll be able to choose between:"
echo "  • 📱 Full App Deployment - Complete web app with interactive UI"
echo "  • 📓 Notebook-Only Experience - Interactive notebooks for learning"
echo ""

# Run prerequisites check and installation
echo "🔧 Checking and installing prerequisites..."
./install-prerequisites.sh
if [ $? -ne 0 ]; then
    echo "❌ Prerequisites installation failed. Please check the output above and try again."
    exit 1
fi

# Initialize Python and TypeScript environments
echo "📦 Initializing development environments..."
./initialize-environment.sh
if [ $? -ne 0 ]; then
    echo "❌ Environment initialization failed. Please check the output above and try again."
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