#!/bin/bash
set -e

echo "GitAI Setup Script"
echo "=================="

# Check if Python 3.9+ is available
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "Installing GitAI in development mode..."
pip install -e ".[dev]"

# Test CLI help
echo "Testing CLI help..."
gitai --help

echo ""
echo "✓ GitAI setup complete!"
echo ""
echo "To use GitAI:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run: gitai --help"
echo ""
echo "Example commands:"
echo "  gitai commit --preview      # Preview commit message"
echo "  gitai pr --base main        # Generate PR description"
echo "  gitai config --global       # Setup configuration"
