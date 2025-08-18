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

echo "🐍 Setting up Python environment..."

# Function to show spinner while running a command
show_spinner() {
    local pid=$1
    local message=$2
    local spin='-\|/'
    local i=0
    while kill -0 $pid 2>/dev/null; do
        i=$(( (i+1) %4 ))
        printf "\r%s %s" "$message" "${spin:$i:1}"
        sleep 0.1
    done
    printf "\r%s ✅\n" "$message"
}

# Ensure virtual environment exists and dependencies are installed
echo "🔄 Setting up Python environment with uv sync..."
uv sync &
spinner_pid=$!
show_spinner $spinner_pid "🐍 Installing Python dependencies"
wait $spinner_pid
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ Failed to set up Python environment"
    echo "Please check that you have Python 3.10.16+ installed and try again."
    echo "You can also try running 'uv sync' manually to see more detailed error messages."
    exit 1
fi

echo "✅ Python environment ready"
echo ""

# Install frontend dependencies
echo "📱 Installing frontend dependencies with bun..."
# Remove any npm lock files that shouldn't be there
[ -f client/package-lock.json ] && rm client/package-lock.json
pushd client > /dev/null
echo "🔄 Installing frontend dependencies with bun..."
bun install &
spinner_pid=$!
show_spinner $spinner_pid "📱 Installing frontend dependencies"
wait $spinner_pid
bun_exit_code=$?
popd > /dev/null

if [ $bun_exit_code -eq 0 ]; then
    echo "✅ Frontend dependencies installed successfully!"
else
    echo "❌ Failed to install frontend dependencies"
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