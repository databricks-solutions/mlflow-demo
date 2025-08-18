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

# Check Databricks CLI
echo "🔍 Checking Databricks CLI..."
databricks_result=0
if ! command -v databricks >/dev/null 2>&1; then
    echo "❌ Databricks CLI not found"
    missing_prereqs+=("Databricks CLI")
    databricks_result=2
else
    cli_version=$(databricks --version 2>/dev/null | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/v//' || echo "0.0.0")
    echo "Found Databricks CLI version: $cli_version"
    required_cli="0.262.0"
    
    set +e  # Temporarily disable exit on error
    version_compare "$cli_version" "$required_cli"
    databricks_result=$?
    set -e  # Re-enable exit on error
    
    if [[ $databricks_result -eq 2 ]]; then
        echo "❌ Databricks CLI version $cli_version is too old. Required: >= $required_cli"
        missing_prereqs+=("Databricks CLI >= $required_cli")
    else
        echo "✅ Databricks CLI version $cli_version is supported"
    fi
fi

# Check uv (only if Python and Databricks CLI are available)
echo "🔍 Checking uv package manager..."
if ! command -v uv >/dev/null 2>&1; then
    echo "❌ uv is not installed"
    missing_prereqs+=("uv package manager")
    # Only add to will_install if both Python and Databricks CLI are properly installed
    if [[ $result -ne 2 ]] && [[ $databricks_result -ne 2 ]]; then
        will_install+=("uv")
    fi
else
    echo "✅ uv is installed"
fi

# Check bun (only if Python and Databricks CLI are available)
echo "🔍 Checking bun JavaScript runtime..."
python_ok=true
databricks_ok=true

# Check if Python requirement was met
for prereq in "${missing_prereqs[@]}"; do
    if [[ "$prereq" == *"Python"* ]]; then
        python_ok=false
        break
    fi
done

# Check if Databricks CLI requirement was met
for prereq in "${missing_prereqs[@]}"; do
    if [[ "$prereq" == *"Databricks CLI"* ]]; then
        databricks_ok=false
        break
    fi
done

if ! command -v bun >/dev/null 2>&1; then
    echo "❌ bun is not installed"
    missing_prereqs+=("bun JavaScript runtime")
    # Only add to will_install if both Python and Databricks CLI are OK
    if [ "$python_ok" = true ] && [ "$databricks_ok" = true ]; then
        will_install+=("bun")
    fi
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
        echo "⚠️  CRITICAL: Python and Databricks CLI must be installed first!"
        echo "📋 The following must be installed manually:"
        for prereq in "${missing_prereqs[@]}"; do
            if [[ "$prereq" == *"Python"* ]]; then
                echo "  • Install Python $required_python or newer from https://python.org"
            elif [[ "$prereq" == *"Databricks CLI"* ]]; then
                echo "  • Install/update Databricks CLI from https://docs.databricks.com/aws/en/dev-tools/cli/install"
            fi
        done
        echo ""
        echo "❌ Cannot install uv/bun until Python and Databricks CLI are properly installed."
        echo "   Please install the above requirements and run this script again."
        exit 1
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
    echo ""
    
    # Show critical prerequisites first
    echo "⚠️  CRITICAL (must be installed first):"
    for prereq in "${missing_prereqs[@]}"; do
        if [[ "$prereq" == *"Python"* ]]; then
            echo "  • Install Python $required_python or newer from https://python.org"
        elif [[ "$prereq" == *"Databricks CLI"* ]]; then
            echo "  • Install/update Databricks CLI from https://docs.databricks.com/aws/en/dev-tools/cli/install"
        fi
    done
    
    # Show other prerequisites
    other_prereqs_exist=false
    for prereq in "${missing_prereqs[@]}"; do
        if [[ "$prereq" != *"Python"* ]] && [[ "$prereq" != *"Databricks CLI"* ]]; then
            if [ "$other_prereqs_exist" = false ]; then
                echo ""
                echo "📋 After installing the above, run this script again to install:"
                other_prereqs_exist=true
            fi
            if [[ "$prereq" == *"uv"* ]]; then
                echo "  • uv package manager (will be auto-installed)"
            elif [[ "$prereq" == *"bun"* ]]; then
                echo "  • bun JavaScript runtime (will be auto-installed)"
            else
                echo "  • $prereq"
            fi
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

# Check if we installed uv or bun and force shell restart
if [[ " ${will_install[@]} " =~ " uv " ]] || [[ " ${will_install[@]} " =~ " bun " ]]; then
    echo "🔄 REQUIRED: You must restart your terminal or source your shell configuration!"
    echo ""
    echo "Choose one of the following options:"
    echo "  1. Close and reopen your terminal (recommended)"
    echo "  2. Run: source ~/.bashrc    (for bash users)"
    echo "  3. Run: source ~/.zshrc     (for zsh users)"
    echo ""
    echo "❗ This script will now exit. Please complete the above step and"
    echo "   run the setup script again to continue with the demo setup."
    exit 0
else
    echo "📝 All tools were already installed. You can proceed with the demo setup."
fi