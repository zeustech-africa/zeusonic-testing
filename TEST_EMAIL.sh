#!/bin/bash
# Quick email test script for Zeusonic OTP delivery
# Usage: ./TEST_EMAIL.sh

set -e

echo "========================================================================"
echo "ZEUSONIC OTP EMAIL TEST"
echo "========================================================================"
echo ""

# Check if RESEND_API_KEY is set
if [ -z "$RESEND_API_KEY" ]; then
    echo "❌ ERROR: RESEND_API_KEY not set"
    echo ""
    echo "To fix, run:"
    echo "  export RESEND_API_KEY=re_your_actual_key_here"
    echo ""
    exit 1
fi

echo "✅ RESEND_API_KEY is set (length: ${#RESEND_API_KEY} chars)"
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "Running validation script..."
echo "------------------------------------------------------------------------"
python3 scripts/validate_resend.py

echo ""
echo "========================================================================"
echo "If you see '✅ EMAIL SENT SUCCESSFULLY!' above,"
echo "check your inbox at: ceo.zeustech@gmail.com"
echo "========================================================================"
