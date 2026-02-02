#!/usr/bin/env python3
"""
Zeusonic 1.0 Launch Readiness Check

This script validates that the system is ready for closed testing.
It performs no mutations - it's a read-only health check.

Usage:
  python3 scripts/launch_readiness_check.py [--verbose]

Exit Codes:
  0 = Ready for testing (GO)
  1 = Issues found (NO-GO)
"""

import sys
import os
import json
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


class ReadinessCheck:
    """Zeusonic launch readiness validation."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warning = []
        self.workspace_root = Path(__file__).resolve().parents[1]
        self.backend_root = self.workspace_root / "backend"
    
    def header(self, title: str):
        """Print section header."""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}{title}{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    def pass_check(self, name: str, detail: str = ""):
        """Record passed check."""
        icon = f"{GREEN}✅{RESET}"
        print(f"{icon} {name}")
        if detail:
            print(f"   {detail}")
        self.checks_passed.append(name)
    
    def fail_check(self, name: str, detail: str = "", advice: str = ""):
        """Record failed check."""
        icon = f"{RED}❌{RESET}"
        print(f"{icon} {name}")
        if detail:
            print(f"   {detail}")
        if advice:
            print(f"   💡 {advice}")
        self.checks_failed.append(name)
    
    def warn_check(self, name: str, detail: str = "", advice: str = ""):
        """Record warning check."""
        icon = f"{YELLOW}⚠️{RESET}"
        print(f"{icon} {name}")
        if detail:
            print(f"   {detail}")
        if advice:
            print(f"   💡 {advice}")
        self.checks_warning.append(name)
    
    def check_python_version(self) -> bool:
        """Verify Python 3.8+."""
        self.header("1. ENVIRONMENT SETUP")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.pass_check(
                "Python version",
                f"Using Python {version.major}.{version.minor}.{version.micro}"
            )
            return True
        else:
            self.fail_check(
                "Python version",
                f"Found Python {version.major}.{version.minor}, need 3.8+",
                "Install Python 3.8 or later"
            )
            return False
    
    def check_dependencies(self) -> bool:
        """Verify required Python packages."""
        packages = {
            "fastapi": "FastAPI web framework",
            "pydantic": "Data validation",
            "pydantic_settings": "Settings management",
            "sqlalchemy": "Database ORM",
            "resend": "Email delivery",
            "stripe": "Billing integration",
            "passlib": "Password hashing",
            "python-dotenv": "Environment variables",
        }
        
        all_ok = True
        for pkg, description in packages.items():
            try:
                __import__(pkg.replace("-", "_"))
                self.pass_check(f"Package: {pkg}", description)
            except ImportError:
                self.fail_check(
                    f"Package: {pkg}",
                    description,
                    f"Install with: pip install {pkg}"
                )
                all_ok = False
        
        return all_ok
    
    def check_file_structure(self) -> bool:
        """Verify required files exist."""
        self.header("2. FILE STRUCTURE")
        
        required_files = {
            "backend/main.py": "FastAPI application",
            "backend/core/config.py": "Configuration",
            "backend/core/logging.py": "Logging setup",
            "backend/core/auth.py": "Auth utilities",
            "backend/api/auth.py": "Auth endpoints",
            "backend/db/models.py": "Data models",
            "backend/db/database.py": "Database setup",
            "backend/services/email_service.py": "Email delivery",
            "scripts/launch_readiness_check.py": "This script",
        }
        
        all_ok = True
        for rel_path, description in required_files.items():
            full_path = self.workspace_root / rel_path
            if full_path.exists():
                self.pass_check(f"File: {rel_path}", description)
            else:
                self.fail_check(
                    f"File: {rel_path}",
                    f"Not found: {full_path}",
                    "Restore from version control"
                )
                all_ok = False
        
        return all_ok
    
    def check_python_syntax(self) -> bool:
        """Verify Python files compile."""
        self.header("3. CODE QUALITY")
        
        critical_files = [
            "backend/main.py",
            "backend/api/auth.py",
            "backend/services/email_service.py",
            "backend/core/config.py",
        ]
        
        all_ok = True
        for rel_path in critical_files:
            full_path = self.workspace_root / rel_path
            if not full_path.exists():
                continue
            
            try:
                import py_compile
                py_compile.compile(str(full_path), doraise=True)
                self.pass_check(f"Syntax: {rel_path}")
            except py_compile.PyCompileError as e:
                self.fail_check(
                    f"Syntax: {rel_path}",
                    f"Compilation error: {e}",
                    "Fix syntax errors and retry"
                )
                all_ok = False
        
        return all_ok
    
    def check_environment_vars(self) -> bool:
        """Check required environment variables."""
        self.header("4. ENVIRONMENT VARIABLES")
        
        critical = {
            "JWT_SECRET": "Application startup",
            "RESEND_API_KEY": "Email delivery",
        }
        
        optional = {
            "STRIPE_SECRET_KEY": "Billing (if enabled)",
            "APP_ENV": "Environment (dev/prod)",
        }
        
        all_ok = True
        
        # Check critical
        for var, purpose in critical.items():
            if os.getenv(var):
                length = len(os.getenv(var))
                self.pass_check(f"Env var: {var}", f"{purpose} (set, {length} chars)")
            else:
                self.fail_check(
                    f"Env var: {var}",
                    f"{purpose} - REQUIRED",
                    f"Set: export {var}=your_value"
                )
                all_ok = False
        
        # Check optional
        for var, purpose in optional.items():
            if os.getenv(var):
                self.pass_check(f"Env var: {var}", purpose)
            else:
                self.warn_check(f"Env var: {var}", purpose, f"Optional: export {var}=value")
        
        return all_ok
    
    def check_imports(self) -> bool:
        """Test critical module imports."""
        self.header("5. MODULE IMPORTS")
        
        sys.path.insert(0, str(self.workspace_root))
        
        modules = {
            "backend.main": "FastAPI app",
            "backend.api.auth": "Auth endpoints",
            "backend.services.email_service": "Email service",
            "backend.db.models": "Data models",
            "backend.core.config": "Configuration",
        }
        
        all_ok = True
        for module, description in modules.items():
            try:
                __import__(module)
                self.pass_check(f"Import: {module}", description)
            except Exception as e:
                self.fail_check(
                    f"Import: {module}",
                    f"{description} - {str(e)[:50]}",
                    "Check file syntax and dependencies"
                )
                all_ok = False
        
        return all_ok
    
    def check_auth_flow(self) -> bool:
        """Verify auth endpoints exist."""
        self.header("6. AUTH FLOW VALIDATION")
        
        all_ok = True
        
        try:
            sys.path.insert(0, str(self.workspace_root))
            from backend.api.auth import register, verify_otp, login
            
            self.pass_check("Endpoint: POST /auth/register", "User registration with OTP")
            self.pass_check("Endpoint: POST /auth/verify-otp", "OTP verification")
            self.pass_check("Endpoint: POST /auth/login", "JWT token issuance")
        except Exception as e:
            self.fail_check(
                "Auth endpoints",
                f"Failed to load auth module: {e}",
                "Check backend/api/auth.py syntax"
            )
            all_ok = False
        
        return all_ok
    
    def check_database_models(self) -> bool:
        """Verify database models."""
        self.header("7. DATABASE MODELS")
        
        all_ok = True
        
        try:
            sys.path.insert(0, str(self.workspace_root))
            from backend.db.models import User, ApiKey, Subscription
            
            # Check User model has required fields
            required_fields = ["email", "password_hash", "is_verified", "otp_hash", "otp_expires_at"]
            
            for field in required_fields:
                if hasattr(User, field):
                    self.pass_check(f"User field: {field}")
                else:
                    self.fail_check(
                        f"User field: {field}",
                        "Missing from User model",
                        "Restore from version control"
                    )
                    all_ok = False
            
        except Exception as e:
            self.fail_check(
                "Database models",
                f"Failed to load models: {e}",
                "Check backend/db/models.py"
            )
            all_ok = False
        
        return all_ok
    
    def check_logging_setup(self) -> bool:
        """Verify logging is configured."""
        self.header("8. OBSERVABILITY")
        
        all_ok = True
        
        try:
            sys.path.insert(0, str(self.workspace_root))
            from backend.core.logging import get_logger, logger
            
            # Test logger
            test_logger = get_logger("test")
            if test_logger:
                self.pass_check("Logger setup", "Centralized logging configured")
            else:
                self.fail_check("Logger setup", "Could not create logger")
                all_ok = False
        
        except Exception as e:
            self.fail_check(
                "Logger setup",
                f"Failed to load logging: {e}",
                "Check backend/core/logging.py"
            )
            all_ok = False
        
        return all_ok
    
    def check_documentation(self) -> bool:
        """Verify launch documentation exists."""
        self.header("9. DOCUMENTATION")
        
        docs = {
            "ENVIRONMENT_CHECKLIST.md": "Environment configuration audit",
            "AUTH_SECURITY_REPORT.md": "Authentication security review",
            "ERROR_HANDLING_GUIDE.md": "Error handling standards",
            "README.md": "Project overview",
        }
        
        all_ok = True
        for doc, purpose in docs.items():
            path = self.workspace_root / doc
            if path.exists():
                size = path.stat().st_size
                self.pass_check(f"Doc: {doc}", f"{purpose} ({size} bytes)")
            else:
                self.warn_check(f"Doc: {doc}", f"{purpose}", "Create documentation")
        
        return all_ok
    
    def check_scripts(self) -> bool:
        """Verify helper scripts exist."""
        self.header("10. TESTING SCRIPTS")
        
        scripts = {
            "scripts/test_email.py": "Simple email test",
            "scripts/validate_email_delivery.py": "Email validation",
            "scripts/validate_resend.py": "Resend API check",
            "scripts/golden_path_auth.py": "Full auth flow test",
        }
        
        all_ok = True
        for script, purpose in scripts.items():
            path = self.workspace_root / script
            if path.exists():
                self.pass_check(f"Script: {script}", purpose)
            else:
                self.warn_check(f"Script: {script}", purpose, "Optional test helper")
        
        return all_ok
    
    def print_summary(self) -> Tuple[bool, str]:
        """Print summary and return GO/NO-GO."""
        self.header("READINESS SUMMARY")
        
        total = len(self.checks_passed) + len(self.checks_failed) + len(self.checks_warning)
        passed = len(self.checks_passed)
        failed = len(self.checks_failed)
        warnings = len(self.checks_warning)
        
        print(f"{BOLD}Results:{RESET}")
        print(f"  {GREEN}✅ Passed:{RESET}  {passed}")
        print(f"  {RED}❌ Failed:{RESET}  {failed}")
        print(f"  {YELLOW}⚠️  Warnings:{RESET} {warnings}")
        print(f"  {BOLD}Total:{RESET}   {total}")
        
        # Determine GO/NO-GO
        if failed == 0:
            print(f"\n{BOLD}{GREEN}✅ READY FOR TESTING (GO){RESET}")
            status = "GO"
        else:
            print(f"\n{BOLD}{RED}❌ NOT READY FOR TESTING (NO-GO){RESET}")
            status = "NO-GO"
        
        return failed == 0, status
    
    def print_next_steps(self, go: bool):
        """Print next steps."""
        self.header("NEXT STEPS")
        
        if not go:
            print(f"{RED}Fix the issues above before starting tests.{RESET}\n")
        
        print("To start Zeusonic 1.0 for testing:\n")
        print("1. Ensure environment variables are set:")
        print("   export JWT_SECRET=your-32-char-secret")
        print("   export RESEND_API_KEY=re_your_actual_key")
        print("")
        print("2. Start the backend:")
        print("   python -m uvicorn backend.main:app --reload --port 8000")
        print("")
        print("3. Test email delivery:")
        print("   python scripts/validate_email_delivery.py --test-send")
        print("")
        print("4. Run end-to-end auth test:")
        print("   python scripts/golden_path_auth.py")
        print("")
        print("See ZEUSONIC_1.0_TESTING_CHECKLIST.md for detailed testing instructions.")
    
    def run(self) -> int:
        """Run all checks."""
        print(f"\n{BOLD}{BLUE}Zeusonic 1.0 - Launch Readiness Check{RESET}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Workspace: {self.workspace_root}\n")
        
        # Run all checks
        self.check_python_version()
        self.check_dependencies()
        self.check_file_structure()
        self.check_python_syntax()
        self.check_environment_vars()
        self.check_imports()
        self.check_auth_flow()
        self.check_database_models()
        self.check_logging_setup()
        self.check_documentation()
        self.check_scripts()
        
        # Summary
        go, status = self.print_summary()
        self.print_next_steps(go)
        
        print("\n")
        
        return 0 if go else 1


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Zeusonic 1.0 launch readiness validation"
    )
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    
    checker = ReadinessCheck(verbose=args.verbose)
    return checker.run()


if __name__ == "__main__":
    sys.exit(main())
