#!/usr/bin/env python3
"""
Golden Path Test with Real Email & OTP Verification

Tests the complete soft-launch authentication flow:
1. Register with real email
2. Receive OTP via Resend
3. Verify OTP
4. Login with JWT
5. Create project
6. Verify persistence

Run: python scripts/golden_path_auth.py
"""
import sys
import os
import time
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test.zeusonic@gmail.com"
TEST_PASSWORD = "SecurePassword123!"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(title):
    print(f"\n{BOLD}{YELLOW}{'='*60}{RESET}")
    print(f"{BOLD}{YELLOW}{title}{RESET}")
    print(f"{BOLD}{YELLOW}{'='*60}{RESET}\n")


def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def print_info(msg):
    print(f"{BOLD}{msg}{RESET}")


def test_api_health():
    """Test 1: Verify API is running"""
    print_section("TEST 1: API HEALTH CHECK")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health")
        if response.status_code == 200:
            print_success("API is running")
            return True
        else:
            print_error(f"API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not connect to API: {e}")
        return False


def test_register(email=TEST_EMAIL, password=TEST_PASSWORD):
    """Test 2: Register new user account"""
    print_section("TEST 2: USER REGISTRATION")
    
    payload = {
        "email": email,
        "password": password,
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"User registered: {data['email']}")
            print_info(f"  is_verified: {data['is_verified']}")
            print_info(f"  message: {data['message']}")
            return True, data
        elif response.status_code == 409:
            print_error("User already registered (this is OK for retry)")
            return True, None
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_info(f"  {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Registration request failed: {e}")
        return False, None


def prompt_otp():
    """Prompt user to enter OTP from email"""
    print_section("TEST 3: OTP VERIFICATION")
    print_info("Check your email inbox for the OTP code from Zeusonic")
    print_info("The code is 6 digits and valid for 10 minutes")
    
    otp = input(f"{BOLD}Enter the 6-digit OTP from your email: {RESET}").strip()
    
    if len(otp) != 6 or not otp.isdigit():
        print_error("OTP must be 6 digits")
        return None
    
    return otp


def test_verify_otp(email=TEST_EMAIL, otp=None):
    """Test 3: Verify OTP"""
    if not otp:
        otp = prompt_otp()
        if not otp:
            return False, None
    
    payload = {
        "email": email,
        "otp": otp,
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/verify-otp", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Email verified successfully")
            print_info(f"  message: {data['message']}")
            return True, data
        else:
            print_error(f"OTP verification failed: {response.status_code}")
            print_info(f"  {response.text}")
            return False, None
    except Exception as e:
        print_error(f"OTP verification request failed: {e}")
        return False, None


def test_login(email=TEST_EMAIL, password=TEST_PASSWORD):
    """Test 4: Login and get JWT token"""
    print_section("TEST 4: LOGIN & JWT TOKEN")
    
    payload = {
        "email": email,
        "password": password,
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            expires_in = data['expires_in']
            
            print_success(f"Login successful")
            print_info(f"  token_type: {data['token_type']}")
            print_info(f"  expires_in: {expires_in} seconds ({expires_in//60} minutes)")
            print_info(f"  token: {token[:20]}...{token[-20:]}")
            
            return True, token
        elif response.status_code == 403:
            print_error("Email not verified (verify OTP first)")
            return False, None
        else:
            print_error(f"Login failed: {response.status_code}")
            print_info(f"  {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Login request failed: {e}")
        return False, None


def test_create_project(token, project_name="Test Project - Soft Launch"):
    """Test 5: Create a project (requires verified user)"""
    print_section("TEST 5: CREATE PROJECT")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "name": project_name,
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v1/projects", json=payload, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            project_id = data['id']
            
            print_success(f"Project created successfully")
            print_info(f"  project_id: {project_id}")
            print_info(f"  name: {data['name']}")
            print_info(f"  created_at: {data['created_at']}")
            
            return True, project_id, data
        else:
            print_error(f"Project creation failed: {response.status_code}")
            print_info(f"  {response.text}")
            return False, None, None
    except Exception as e:
        print_error(f"Project creation request failed: {e}")
        return False, None, None


def test_get_projects(token):
    """Test 6: Retrieve projects (verify persistence)"""
    print_section("TEST 6: RETRIEVE PROJECTS (PERSISTENCE CHECK)")
    
    headers = {
        "Authorization": f"Bearer {token}",
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/projects", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            
            print_success(f"Retrieved {len(projects)} project(s)")
            for proj in projects:
                print_info(f"  - {proj['name']} (id={proj['id']})")
            
            return True, projects
        else:
            print_error(f"Failed to retrieve projects: {response.status_code}")
            print_info(f"  {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Project retrieval request failed: {e}")
        return False, None


def test_logout_and_relogin(email=TEST_EMAIL, password=TEST_PASSWORD):
    """Test 7: Logout and re-login (session persistence)"""
    print_section("TEST 7: LOGOUT & RE-LOGIN (SESSION PERSISTENCE)")
    
    # Logout is client-side in JWT, so we just simulate by discarding token
    print_info("Simulating logout (JWT is stateless, just discard token)...")
    time.sleep(1)
    
    # Re-login
    print_info("Attempting to re-login with same credentials...")
    success, new_token = test_login(email, password)
    
    if success and new_token:
        print_success("Re-login successful after logout")
        return True, new_token
    else:
        print_error("Re-login failed")
        return False, None


def run_full_test_flow():
    """Run the complete golden path"""
    print(f"\n{BOLD}{YELLOW}╔{'='*58}╗{RESET}")
    print(f"{BOLD}{YELLOW}║ ZEUSONIC 1.0 — SOFT LAUNCH AUTH VERIFICATION FLOW    ║{RESET}")
    print(f"{BOLD}{YELLOW}╚{'='*58}╝{RESET}")
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test email: {TEST_EMAIL}")
    
    results = {
        "health_check": False,
        "register": False,
        "otp_verify": False,
        "login": False,
        "create_project": False,
        "persistence": False,
        "relogin": False,
    }
    
    # Test 1: Health check
    if not test_api_health():
        print_error("API is not running. Start the backend with: python -m uvicorn backend.main:app --reload")
        return results
    results["health_check"] = True
    
    # Test 2: Register
    success, reg_data = test_register()
    if not success:
        print_error("Registration failed. Stopping tests.")
        return results
    results["register"] = True
    
    # Test 3: Verify OTP
    success, verify_data = test_verify_otp()
    if not success:
        print_error("OTP verification failed. Stopping tests.")
        return results
    results["otp_verify"] = True
    
    # Test 4: Login
    success, token = test_login()
    if not success:
        print_error("Login failed. Stopping tests.")
        return results
    results["login"] = True
    
    # Test 5: Create project
    success, project_id, proj_data = test_create_project(token)
    if not success:
        print_error("Project creation failed. Stopping tests.")
        return results
    results["create_project"] = True
    
    # Test 6: Retrieve projects
    success, projects = test_get_projects(token)
    if not success:
        print_error("Project retrieval failed. Stopping tests.")
        return results
    results["persistence"] = True
    
    # Test 7: Re-login
    success, new_token = test_logout_and_relogin()
    if not success:
        print_error("Re-login failed. Stopping tests.")
        return results
    results["relogin"] = True
    
    return results


def print_summary(results):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    test_names = {
        "health_check": "API Health Check",
        "register": "User Registration",
        "otp_verify": "OTP Verification",
        "login": "Login & JWT",
        "create_project": "Create Project",
        "persistence": "Data Persistence",
        "relogin": "Session Persistence",
    }
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for key, name in test_names.items():
        status = "✅ PASS" if results[key] else "❌ FAIL"
        color = GREEN if results[key] else RED
        print(f"{color}{status}{RESET} — {name}")
    
    print(f"\n{BOLD}Total: {passed}/{total} passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! Zeusonic auth is ready for soft launch.{RESET}")
        return True
    else:
        print(f"\n{RED}{BOLD}⚠️ Some tests failed. Review errors above.{RESET}")
        return False


if __name__ == "__main__":
    try:
        results = run_full_test_flow()
        success = print_summary(results)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
