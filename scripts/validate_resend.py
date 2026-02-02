#!/usr/bin/env python3
"""
Validate Resend email configuration and API connectivity.
Run: python scripts/validate_resend.py
"""
import sys
import os

print("="*70)
print("RESEND EMAIL VALIDATION")
print("="*70)

# Step 1: Check environment
api_key = os.getenv("RESEND_API_KEY")
if not api_key:
    print("❌ RESEND_API_KEY not set in environment")
    print("\nTo fix, run:")
    print("  export RESEND_API_KEY=re_your_actual_key_here")
    sys.exit(1)
else:
    print(f"✅ RESEND_API_KEY: Set (length: {len(api_key)} chars)")

# Step 2: Import resend
try:
    import resend
    print("✅ resend module: Imported successfully")
except ImportError as e:
    print(f"❌ Cannot import resend: {e}")
    print("\nTo fix, run:")
    print("  pip install resend")
    sys.exit(1)

# Step 3: Test API call
print("\nAttempting to send test email...")
print("-"*70)

try:
    resend.api_key = api_key
    
    result = resend.Emails.send({
        "from": "Zeusonic <no-reply@zeustechafrica.com>",
        "to": ["ceo.zeustech@gmail.com"],
        "subject": "Zeusonic Test - OTP Verification",
        "html": """
            <h2>Zeusonic OTP Verification Test</h2>
            <p>Your verification code is:</p>
            <div style='font-size: 28px; font-weight: bold; letter-spacing: 4px; 
                        margin: 24px 0; color: #2563eb;'>483920</div>
            <p>This code expires in 10 minutes.</p>
            <p style='color:#666; font-size: 12px;'>
                If you did not request this, please ignore this email.
            </p>
        """
    })
    
    print("✅ EMAIL SENT SUCCESSFULLY!")
    print(f"\nResponse details:")
    print(f"  {result}")
    print("\n" + "="*70)
    print("✅ VALIDATION PASSED - Resend is configured correctly")
    print("="*70)
    sys.exit(0)
    
except Exception as e:
    print(f"❌ EMAIL SEND FAILED")
    print(f"\nError: {e}")
    print("\nPossible issues:")
    print("  1. Invalid RESEND_API_KEY")
    print("  2. Domain not verified in Resend dashboard")
    print("  3. Sender email not authorized")
    print("\n" + "="*70)
    sys.exit(1)
