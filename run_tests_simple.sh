#!/bin/bash
# Simple test runner script

echo "Running tests..."
cd /Users/machine/Desktop/Namaskah\ .\ app

# Run pytest on validators and errors test
python3 -m pytest app/tests/test_validators_and_errors.py -v --tb=short 2>&1 | head -100

echo ""
echo "Test run complete!"
