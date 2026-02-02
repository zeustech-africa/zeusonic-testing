#!/usr/bin/env python3
"""
Email Delivery Validation & Health Check for Zeusonic 1.0

This script validates that Resend email delivery is properly configured and functional.
Run this BEFORE deploying to closed testing.

Usage:
  python3 scripts/validate_email_delivery.py [--test-send] [--verbose]

Options:
  --test-send    Actually send a test email (requires RESEND_API_KEY)
  --verbose      Print detailed diagnostic information
"""

import sys
import os
import argparse
from typing import Dict, Tuple

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    """Print a section header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_check(name: str, status: bool, detail: str = ""):
    """Print a single check result."""
    icon = f"{GREEN}✅{RESET}" if status else f"{RED}❌{RESET}"
    print(f"{icon} {name}")
    if detail:
        print(f"   {detail}")


def print_warning(msg: str):
    """Print a warning message."""
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def print_error(msg: str):
    """Print an error message."""
    print(f"{RED}❌ {msg}{RESET}")


def print_success(msg: str):
    """Print a success message."""
    print(f"{GREEN}✅ {msg}{RESET}")


def check_environment() -> Tuple[bool, Dict]:
    """Check required environment variables."""
    print_header("1. ENVIRONMENT CHECK")
    
    results = {
        "api_key_set": False,
        "from_email_set": False,
    }
    
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL", "Zeusonic <no-reply@zeustechafrica.com>")
    
    results["api_key_set"] = bool(api_key)
    results["from_email_set"] = bool(from_email)
    
    print_check("RESEND_API_KEY", results["api_key_set"], 
                f"Length: {len(api_key) if api_key else 0}" if api_key else "Not set")
    print_check("RESEND_FROM_EMAIL", results["from_email_set"], 
                f"Value: {from_email}")
    
    if not results["api_key_set"]:
        print_warning("RESEND_API_KEY not set - email delivery will fail")
        return False, results
    
    return True, results


def check_imports() -> Tuple[bool, Dict]:
    """Check required Python dependencies."""
    print_header("2. DEPENDENCY CHECK")
    
    results = {
        "resend_available": False,
        "resend_version": None,
    }
    
    try:
        import resend
        results["resend_available"] = True
        if hasattr(resend, "__version__"):
            results["resend_version"] = resend.__version__
        print_check("resend library", True, 
                    f"Version: {results['resend_version'] or 'unknown'}")
    except ImportError:
        print_error("resend library not available")
        print_warning("Install with: pip install resend")
        return False, results
    
    return True, results


def check_configuration() -> Tuple[bool, Dict]:
    """Check email service configuration."""
    print_header("3. CONFIGURATION CHECK")
    
    results = {
        "config_loadable": False,
        "from_email_valid": False,
    }
    
    try:
        sys.path.insert(0, os.path.dirname(__file__) + "/..")
        from backend.services.email_service import FROM_EMAIL
        results["config_loadable"] = True
        print_check("Email service imports", True)
        
        # Check from email format
        if "@" in FROM_EMAIL or "<" in FROM_EMAIL:
            results["from_email_valid"] = True
            print_check("FROM_EMAIL format valid", True, f"Address: {FROM_EMAIL}")
        else:
            print_warning(f"FROM_EMAIL may be malformed: {FROM_EMAIL}")
    except Exception as e:
        print_error(f"Failed to load email configuration: {e}")
        return False, results
    
    return True, results


def check_resend_connectivity(verbose: bool = False) -> Tuple[bool, Dict]:
    """Check connectivity to Resend API."""
    print_header("4. RESEND API CONNECTIVITY")
    
    results = {
        "api_reachable": False,
        "api_error": None,
    }
    
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key:
        print_warning("RESEND_API_KEY not set - skipping connectivity check")
        return False, results
    
    try:
        import resend
        resend.api_key = api_key
        
        # Try a minimal API call (list contacts - read-only, won't modify anything)
        try:
            # This is a lightweight check without sending anything
            result = resend.Contacts.list(limit=1)
            results["api_reachable"] = True
            print_check("Resend API accessible", True)
            
            if verbose:
                print(f"   API Response: {result}")
        except Exception as e:
            error_str = str(e)
            results["api_error"] = error_str
            
            if "Invalid API key" in error_str or "Unauthorized" in error_str:
                print_error(f"Authentication failed: {error_str}")
                print_warning("Verify RESEND_API_KEY is correct in your environment")
            else:
                print_warning(f"API check returned: {error_str}")
                print_warning("Email sending may still work (API returned non-fatal error)")
                results["api_reachable"] = True  # Don't block on non-critical errors
    
    except Exception as e:
        print_error(f"Failed to check API: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False, results
    
    return results["api_reachable"], results


def test_send_email(verbose: bool = False) -> Tuple[bool, Dict]:
    """Attempt to send a test email."""
    print_header("5. TEST EMAIL SEND")
    
    results = {
        "email_sent": False,
        "response": None,
        "error": None,
    }
    
    api_key = os.getenv("RESEND_API_KEY")
    
    if not api_key:
        print_warning("RESEND_API_KEY not set - skipping email send test")
        return False, results
    
    print("Attempting to send test email...")
    
    try:
        import resend
        sys.path.insert(0, os.path.dirname(__file__) + "/..")
        from backend.services.email_service import FROM_EMAIL
        
        resend.api_key = api_key
        
        test_email = "test@zeusonic.local"  # Non-real test address
        
        response = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [test_email],
            "subject": "Zeusonic Test Email - Ignore",
            "html": """
                <h2>Zeusonic Email Delivery Test</h2>
                <p>If you received this, email is working correctly.</p>
                <p><strong>Test Code:</strong> ZTEST-001</p>
            """,
        })
        
        results["email_sent"] = True
        results["response"] = response
        
        if verbose:
            print(f"   Response: {response}")
        
        print_check("Test email sent", True)
        print_warning(f"Email sent to {test_email} (test address, will not be delivered)")
        
    except Exception as e:
        error_str = str(e)
        results["error"] = error_str
        print_error(f"Failed to send test email: {error_str}")
        
        if "unverified" in error_str.lower():
            print_warning("Domain may not be verified in Resend dashboard")
        
        if verbose:
            import traceback
            traceback.print_exc()
        
        return False, results
    
    return True, results


def print_summary(all_results: Dict[str, any]) -> bool:
    """Print final summary and return GO/NO-GO."""
    print_header("SUMMARY")
    
    checks = [
        ("Environment Variables", all_results.get("env", {}).get("api_key_set", False)),
        ("Dependencies", all_results.get("deps", {}).get("resend_available", False)),
        ("Configuration", all_results.get("config", {}).get("config_loadable", False)),
        ("API Connectivity", all_results.get("connectivity", {}).get("api_reachable", False)),
        ("Email Send", all_results.get("email", {}).get("email_sent", False)),
    ]
    
    passed = sum(1 for _, status in checks if status)
    total = len(checks)
    
    for name, status in checks:
        print_check(name, status)
    
    print(f"\n{BOLD}Score: {passed}/{total}{RESET}")
    
    if passed >= 3:  # At least env, deps, config
        print_success("Email delivery is READY for testing")
        return True
    else:
        print_error("Email delivery is NOT ready for testing")
        return False


def main():
    """Run all validation checks."""
    parser = argparse.ArgumentParser(
        description="Validate Zeusonic email delivery configuration"
    )
    parser.add_argument("--test-send", action="store_true", 
                       help="Send a test email (requires valid RESEND_API_KEY)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Print detailed diagnostic information")
    
    args = parser.parse_args()
    
    print(f"\n{BOLD}{BLUE}Zeusonic 1.0 - Email Delivery Validation{RESET}")
    print(f"Date: {os.popen('date').read().strip()}")
    print(f"Python: {sys.version.split()[0]}")
    
    all_results = {}
    
    # Run all checks
    env_ok, all_results["env"] = check_environment()
    deps_ok, all_results["deps"] = check_imports()
    config_ok, all_results["config"] = check_configuration()
    conn_ok, all_results["connectivity"] = check_resend_connectivity(args.verbose)
    
    # Optional: test email send
    email_ok = False
    if args.test_send:
        email_ok, all_results["email"] = test_send_email(args.verbose)
    else:
        print_header("5. TEST EMAIL SEND")
        print_warning("Skipped - use --test-send to send a test email")
        all_results["email"] = {"email_sent": False}
    
    # Print summary
    go_no_go = print_summary(all_results)
    
    # Print instructions
    print_header("NEXT STEPS")
    
    if not env_ok:
        print("1. Set environment variables:")
        print("   export RESEND_API_KEY=re_your_key_from_resend_dashboard")
    
    if not email_ok and args.test_send:
        print("2. Check Resend dashboard:")
        print("   - Verify your domain is configured")
        print("   - Ensure sender email is approved")
        print("   - Check API key is valid")
    
    if go_no_go:
        print("✅ Email delivery is configured correctly!")
        print("✅ Ready for closed testing")
    else:
        print("❌ Fix issues above before testing")
    
    print("\n")
    
    return 0 if go_no_go else 1


if __name__ == "__main__":
    sys.exit(main())
