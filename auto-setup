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

echo "🐍 Setting up Python environment..."

# Ensure virtual environment exists and dependencies are installed
if ! uv sync --quiet; then
    echo "❌ Failed to set up Python environment"
    echo "Please check that you have Python 3.12+ installed and try again."
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