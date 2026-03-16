#!/bin/bash
# Setup and Run Script for Cloud Data Integrity Verification System
# This script sets up the environment and runs the Flask application

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Cloud Data Integrity Verification System                      ║"
echo "║  Setup and Installation Script                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip

if [ $? -ne 0 ]; then
    echo "⚠️ Warning: pip upgrade failed, continuing..."
fi

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    deactivate
    exit 1
fi

echo "✓ Dependencies installed successfully"
echo ""

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p uploads
mkdir -p reports
mkdir -p sample_data

echo "✓ Directories created"
echo ""

# Display instructions
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                              ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║                                                                ║"
echo "║  To start the Flask application, run:                          ║"
echo "║                                                                ║"
echo "║      python app.py                                             ║"
echo "║                                                                ║"
echo "║  This will start the server on: http://127.0.0.1:5000         ║"
echo "║                                                                ║"
echo "║  Open your web browser and navigate to that address            ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Optional: Start the Flask app automatically
read -p "Do you want to start the Flask application now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Flask application..."
    echo ""
    python app.py
else
    echo "Setup complete. Run 'python app.py' to start the application."
fi
