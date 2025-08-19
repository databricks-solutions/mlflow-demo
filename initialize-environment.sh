#!/bin/bash

# Environment Initialization Script for MLflow Demo
# Initializes Python and TypeScript environments

set -e  # Exit on any error

echo "📦 MLflow Demo Environment Initializer"
echo "======================================"
echo ""

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

echo "This script will initialize the development environments:"
echo ""
echo "📋 What will be installed:"
echo "  🐍 Python environment via uv"
echo "  📱 TypeScript environment via bun"
echo ""

echo ""
echo "🚀 Initializing environments..."
echo ""

# Install Python dependencies
echo "🐍 Installing Python dependencies with uv..."
echo "This will set up the Python virtual environment and install all required packages..."
uv sync &
spinner_pid=$!
show_spinner $spinner_pid "🐍 Installing Python dependencies"
wait $spinner_pid
python_exit_code=$?

if [ $python_exit_code -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    echo "Please check that you have Python 3.10.16+ installed and try again."
    echo "You can also try running 'uv sync' manually to see more detailed error messages."
    exit 1
fi

echo "✅ Python dependencies installed successfully!"
echo ""

# Install frontend dependencies
echo "📱 Installing frontend dependencies with bun..."
echo "This will install React, TypeScript, and all UI components..."

# Remove any npm lock files that shouldn't be there
[ -f client/package-lock.json ] && rm client/package-lock.json

pushd client > /dev/null
bun install &
spinner_pid=$!
show_spinner $spinner_pid "📱 Installing frontend dependencies"
wait $spinner_pid
frontend_exit_code=$?
popd > /dev/null

if [ $frontend_exit_code -ne 0 ]; then
    echo "❌ Failed to install frontend dependencies"
    echo "Please check the error messages above and try again."
    exit 1
fi

echo "✅ Frontend dependencies installed successfully!"
echo ""
echo "🎉 All environments initialized successfully!"
echo ""