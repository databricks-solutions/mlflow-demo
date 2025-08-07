#!/bin/bash

# Auto-setup wrapper script for MLflow Demo
# This script ensures the Python environment is set up before running auto-setup.py

set -e  # Exit on any error

echo "🚀 MLflow Demo Auto-Setup Wrapper"
echo "=================================="
echo ""

# Check if uv is available
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed."
    echo ""
    read -p "Would you like to install uv now? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "⚠️  Please install uv first with:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "   Then restart your terminal and run this script again."
        exit 1
    else
        echo "📥 Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Source the shell to get uv in PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        if ! command -v uv >/dev/null 2>&1; then
            echo "❌ uv installation failed. Please restart your terminal and run this script again."
            exit 1
        fi
        echo "✅ uv installed successfully!"
    fi
fi

# Check Python version (>= 3.10.16)
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 || python --version 2>/dev/null | cut -d' ' -f2 || echo "0.0.0")
required_python="3.10.16"

# Function to compare versions
version_compare() {
    local ver1=$1
    local ver2=$2
    if [[ "$ver1" == "$ver2" ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($ver1) ver2=($ver2)
    # Fill empty fields in ver1 with zeros
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

version_compare "$python_version" "$required_python"
result=$?

if [[ $result -eq 2 ]]; then
    echo "❌ Python version $python_version is too old. Required: >= $required_python"
    echo "   Please install a newer version of Python"
    exit 1
else
    echo "✅ Python version $python_version is supported"
fi

# Check Databricks CLI version (>= 0.262.0)
echo "🔍 Checking Databricks CLI version..."
if ! command -v databricks >/dev/null 2>&1; then
    echo "❌ Databricks CLI not found"
    echo "   Please install Databricks CLI"
    echo "   Install from: https://docs.databricks.com/aws/en/dev-tools/cli/install"
    exit 1
fi

cli_version=$(databricks --version 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/v//' || echo "0.0.0")
required_cli="0.262.0"

version_compare "$cli_version" "$required_cli"
result=$?

if [[ $result -eq 2 ]]; then
    echo "❌ Databricks CLI version $cli_version is too old. Required: >= $required_cli"
    echo "   Please update Databricks CLI"
    echo "   Install from: https://docs.databricks.com/aws/en/dev-tools/cli/install"
    exit 1
else
    echo "✅ Databricks CLI version $cli_version is supported"
fi

echo "🐍 Setting up Python environment..."

# Ensure virtual environment exists and dependencies are installed
if ! uv sync --quiet; then
    echo "❌ Failed to set up Python environment"
    echo "Please check that you have Python 3.10.16+ installed and try again."
    exit 1
fi

echo "✅ Python environment ready"
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