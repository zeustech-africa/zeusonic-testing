#!/usr/bin/env python3
"""
Test email delivery via Resend.
Run: python scripts/test_email.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.email_service import send_otp_email

TEST_EMAIL = "ceo.zeustech@gmail.com"
TEST_OTP = "483920"

print(f"Sending OTP email to: {TEST_EMAIL}")
print(f"Test OTP: {TEST_OTP}")
print("-" * 50)

try:
    send_otp_email(TEST_EMAIL, TEST_OTP)
    print("✅ OTP email sent successfully via Resend!")
    sys.exit(0)
except Exception as e:
    print(f"❌ Failed to send email: {e}")
    sys.exit(1)
