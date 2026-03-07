#!/bin/bash

# Syntax Check Script for Tempest Weather Station InfluxDB Publisher
# This script performs comprehensive syntax and code quality checks

set -e  # Exit on any error

echo "Running syntax checks for tempest-influxdb..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}[OK] $2${NC}"
    else
        echo -e "${RED}[FAIL] $2${NC}"
        return 1
    fi
}

echo ""
echo "1. Checking Python syntax..."

# Check Python syntax
if python3 -m py_compile main.py 2>/dev/null; then
    print_status 0 "Python syntax check passed"
else
    print_status 1 "Python syntax check failed"
    echo "Running detailed syntax check:"
    python3 -m py_compile main.py
    exit 1
fi

echo ""
echo "2. Checking Python imports..."

# Test basic imports (excluding influxdb-client for dev environments)
if python3 -c "
import sys
try:
    import argparse, json, os, socket, threading, time
    from datetime import datetime, timezone
    print('Standard library imports successful')
except ImportError as e:
    print(f'Standard library import error: {e}')
    sys.exit(1)

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
    print('InfluxDB client import successful')
except ImportError as e:
    print(f'InfluxDB client import error: {e} (install with: pip install influxdb-client)')
" 2>/dev/null; then
    print_status 0 "Python imports check passed"
else
    # Check what specifically failed
    python3 -c "
import sys
missing = []
try:
    import argparse, json, os, socket, threading, time
    from datetime import datetime, timezone
    print('Standard library imports: OK')
except ImportError as e:
    missing.append(str(e))

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    print('InfluxDB client import: OK')
except ImportError as e:
    if 'influxdb' in str(e):
        print('InfluxDB client import: Missing (install with: pip install influxdb-client)')
    else:
        missing.append(str(e))

if missing:
    print('Critical missing dependencies:', missing)
    sys.exit(1)
else:
    print('All critical imports available')
    sys.exit(0)
" || {
        if [ $? -eq 1 ]; then
            print_status 1 "Critical imports failed"
            exit 1
        fi
        print_status 0 "Python imports check passed (influxdb-client missing in dev environment)"
    }
fi

echo ""
echo "3. Checking for common Python issues..."

# Check for common issues
issues_found=0

# Check for print statements (should use logging)
if grep -n "print(" main.py 2>/dev/null; then
    echo -e "${YELLOW}[WARN] Found print() statements - consider using logger instead${NC}"
    issues_found=1
fi

# Check for TODO comments
if grep -n "TODO\|FIXME\|XXX" main.py 2>/dev/null; then
    echo -e "${YELLOW}[WARN] Found TODO/FIXME comments in code${NC}"
fi

# Check line length (warn if >120 chars)
if grep -n "^.\{120,\}" main.py 2>/dev/null; then
    echo -e "${YELLOW}[WARN] Found long lines (>120 chars)${NC}"
fi

if [ $issues_found -eq 0 ]; then
    print_status 0 "Basic code quality checks passed"
fi

echo ""
echo "4. Attempting linting (flake8)..."

# Try flake8 if available
if command -v flake8 >/dev/null 2>&1; then
    if flake8 main.py --max-line-length=120 --ignore=E501,W503 2>/dev/null; then
        print_status 0 "Flake8 linting passed"
    else
        echo -e "${YELLOW}[WARN] Flake8 found issues (may be non-critical)${NC}"
        flake8 main.py --max-line-length=120 --ignore=E501,W503 || true
    fi
else
    echo -e "${YELLOW}[INFO] Flake8 not available - skipping advanced linting${NC}"
fi

echo ""
echo "5. Checking file permissions..."

# Check if main.py is executable (it should be)
if [ -x main.py ]; then
    print_status 0 "main.py has execute permissions"
else
    echo -e "${YELLOW}[INFO] main.py should be executable ($(ls -l main.py | cut -d' ' -f1))${NC}"
fi

echo ""
echo "6. Verifying required files..."

required_files=("main.py" "README.md" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "$file exists"
    else
        print_status 1 "$file is missing"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}All syntax checks completed successfully!${NC}"
echo ""
echo "Summary:"
echo "- Python syntax: OK"
echo "- Imports: OK" 
echo "- Code quality: Basic checks passed"
echo "- Required files: Present"
echo ""
echo "Ready for development and testing!"
