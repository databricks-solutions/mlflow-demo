#!/bin/bash

# Prerequisites Installation Script for MLflow Demo
# Handles checking and installing all required prerequisites

set -e  # Exit on any error

echo "🔍 MLflow Demo Prerequisites Checker"
echo "===================================="
echo ""

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
        # Remove leading zeros and compare as integers
        local v1=${ver1[i]#0}
        local v2=${ver2[i]#0}
        # Handle empty strings after removing leading zeros
        [[ -z "$v1" ]] && v1=0
        [[ -z "$v2" ]] && v2=0
        # Convert to integers
        v1=$((v1))
        v2=$((v2))
        if [[ $v1 -gt $v2 ]]; then
            return 1
        fi
        if [[ $v1 -lt $v2 ]]; then
            return 2
        fi
    done
    return 0
}

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
    wait $pid
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        printf "\r%s ✅\n" "$message"
    else
        printf "\r%s ❌\n" "$message"
    fi
}

# Track what needs to be installed
missing_prereqs=()
will_install=()

echo "Checking prerequisites..."
echo ""

# Check Python version (>= 3.10.16)
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2 || python --version 2>/dev/null | cut -d' ' -f2 || echo "0.0.0")
echo "Found Python version: $python_version"
required_python="3.10.16"

set +e  # Temporarily disable exit on error
version_compare "$python_version" "$required_python"
result=$?
set -e  # Re-enable exit on error

if [[ $result -eq 2 ]]; then
    echo "❌ Python version $python_version is too old. Required: >= $required_python"
    missing_prereqs+=("Python >= $required_python")
else
    echo "✅ Python version $python_version is supported"
fi

# Check uv
echo "🔍 Checking uv package manager..."
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed"
    missing_prereqs+=("uv package manager")
    will_install+=("uv")
else
    echo "✅ uv is installed"
fi

# Check Databricks CLI
echo "🔍 Checking Databricks CLI..."
if ! command -v databricks >/dev/null 2>&1; then
    echo "❌ Databricks CLI not found"
    missing_prereqs+=("Databricks CLI")
else
    cli_version=$(databricks --version 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/v//' || echo "0.0.0")
    echo "Found Databricks CLI version: $cli_version"
    required_cli="0.262.0"
    
    set +e  # Temporarily disable exit on error
    version_compare "$cli_version" "$required_cli"
    result=$?
    set -e  # Re-enable exit on error
    
    if [[ $result -eq 2 ]]; then
        echo "❌ Databricks CLI version $cli_version is too old. Required: >= $required_cli"
        missing_prereqs+=("Databricks CLI >= $required_cli")
    else
        echo "✅ Databricks CLI version $cli_version is supported"
    fi
fi

# Check bun
echo "🔍 Checking bun JavaScript runtime..."
if ! command -v bun >/dev/null 2>&1; then
    echo "❌ bun is not installed"
    missing_prereqs+=("bun JavaScript runtime")
    will_install+=("bun")
else
    echo "✅ bun is installed"
fi

echo ""

# Summary of what's missing
if [ ${#missing_prereqs[@]} -eq 0 ]; then
    echo "🎉 All prerequisites are already installed!"
    exit 0
fi

echo "📋 Missing prerequisites:"
for prereq in "${missing_prereqs[@]}"; do
    echo "  • $prereq"
done

echo ""

if [ ${#will_install[@]} -gt 0 ]; then
    echo "📦 The following will be installed automatically:"
    for item in "${will_install[@]}"; do
        echo "  • $item"
    done
    echo ""
    
    # Check if there are any manual installation requirements
    manual_install_needed=false
    for prereq in "${missing_prereqs[@]}"; do
        if [[ "$prereq" == *"Python"* ]] || [[ "$prereq" == *"Databricks CLI"* ]]; then
            manual_install_needed=true
            break
        fi
    done
    
    if [ "$manual_install_needed" = true ]; then
        echo "📋 The following must be installed manually:"
        for prereq in "${missing_prereqs[@]}"; do
            if [[ "$prereq" == *"Python"* ]]; then
                echo "  • Install Python $required_python or newer from https://python.org"
            elif [[ "$prereq" == *"Databricks CLI"* ]]; then
                echo "  • Install/update Databricks CLI from https://docs.databricks.com/aws/en/dev-tools/cli/install"
            fi
        done
        echo ""
    fi
    
    read -p "Would you like to install the automatic prerequisites now? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "❌ Cannot proceed without installing prerequisites."
        echo ""
        echo "Manual installation instructions:"
        if [[ " ${will_install[@]} " =~ " uv " ]]; then
            echo "  uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        fi
        if [[ " ${will_install[@]} " =~ " bun " ]]; then
            echo "  bun: curl -fsSL https://bun.sh/install | bash"
        fi
        exit 1
    fi
else
    echo "❌ Cannot proceed. Please install the missing prerequisites manually:"
    for prereq in "${missing_prereqs[@]}"; do
        if [[ "$prereq" == *"Python"* ]]; then
            echo "  • Install Python $required_python or newer from https://python.org"
        elif [[ "$prereq" == *"Databricks CLI"* ]]; then
            echo "  • Install/update Databricks CLI from https://docs.databricks.com/aws/en/dev-tools/cli/install"
        fi
    done
    exit 1
fi

echo ""
echo "🚀 Installing prerequisites..."
echo ""

# Install uv if needed
if [[ " ${will_install[@]} " =~ " uv " ]]; then
    echo "📥 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh &
    spinner_pid=$!
    show_spinner $spinner_pid "📥 Installing uv package manager"
    wait $spinner_pid
    
    # Check if uv installation was successful
    if [ $? -ne 0 ]; then
        echo "❌ uv installation failed. Please install uv manually and run this script again."
        echo "   Manual installation: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    # Source the shell to get uv in PATH
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv >/dev/null 2>&1; then
        echo "❌ uv installation failed. Please restart your terminal and run this script again."
        exit 1
    fi
    echo "✅ uv installed successfully!"
fi

# Install bun if needed
if [[ " ${will_install[@]} " =~ " bun " ]]; then
    echo "📥 Installing bun..."
    curl -fsSL https://bun.sh/install | bash &
    spinner_pid=$!
    show_spinner $spinner_pid "📥 Installing bun JavaScript runtime"
    wait $spinner_pid
    
    # Check if bun installation was successful
    if [ $? -ne 0 ]; then
        echo "❌ bun installation failed. Please install bun manually and run this script again."
        echo "   Manual installation: curl -fsSL https://bun.sh/install | bash"
        exit 1
    fi
    
    # Source the shell to get bun in PATH
    export BUN_INSTALL="$HOME/.bun"
    export PATH="$BUN_INSTALL/bin:$PATH"
    if ! command -v bun >/dev/null 2>&1; then
        echo "❌ bun installation failed. Please restart your terminal and run this script again."
        exit 1
    fi
    echo "✅ bun installed successfully!"
fi

echo ""
echo "✅ All prerequisites installed successfully!"
echo ""
echo "📝 Note: If you installed new tools, you may need to restart your terminal"
echo "   or run 'source ~/.bashrc' (or ~/.zshrc) to update your PATH."