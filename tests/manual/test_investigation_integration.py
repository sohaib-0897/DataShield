#!/usr/bin/env python3
"""
Investigation Button Integration Test Suite
Tests the complete workflow for Investigation page decision submission
"""

import os
import requests
import json
import time
from typing import Tuple, Dict

# Configuration
BACKEND_URL = "http://localhost:5000"
API_KEY = os.environ["DATASHIELD_API_KEY"]
HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}

class TestColor:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"

def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result with color"""
    status = f"{TestColor.GREEN}✓ PASS{TestColor.END}" if passed else f"{TestColor.RED}✗ FAIL{TestColor.END}"
    print(f"  {status} {test_name}")
    if details:
        print(f"     {details}")

def test_backend_connection() -> bool:
    """Test 1: Backend is accessible"""
    test_name = "Backend Connection"
    try:
        response = requests.get(f"{BACKEND_URL}/alerts", headers=HEADERS, timeout=5)
        passed = response.status_code == 200
        print_test(test_name, passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def test_upload_alert_creation() -> Tuple[bool, int]:
    """Test 2: Create upload alert"""
    test_name = "Upload Alert Creation"
    try:
        payload = {
            "client": "test@company.com",
            "filename": "test_doc.pdf",
            "upload_url": "https://cloud.example.com/upload",
            "sensitive": True,
            "sensitive_matches": ["12345-6789012-3"]
        }
        response = requests.post(
            f"{BACKEND_URL}/upload_alert",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 200
        alert_id = response.json().get("alert_id", -1) if passed else -1
        print_test(test_name, passed, f"Alert ID: {alert_id}, Status: {response.status_code}")
        return passed, alert_id
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False, -1

def test_file_activity_alert_creation() -> Tuple[bool, int]:
    """Test 3: Create file activity alert"""
    test_name = "File Activity Alert Creation"
    try:
        payload = {
            "event": "created",
            "filepath": "C:\\Users\\Sohaib\\Desktop\\test_file.txt",
            "severity": "high",
            "pattern_match": "test_pattern"
        }
        response = requests.post(
            f"{BACKEND_URL}/file_activity_alert",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 200
        alert_id = response.json().get("alert_id", -1) if passed else -1
        print_test(test_name, passed, f"Alert ID: {alert_id}, Status: {response.status_code}")
        return passed, alert_id
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False, -1

def test_decision_upload_alert(alert_id: int) -> bool:
    """Test 4: Submit decision for upload alert"""
    test_name = "Upload Alert Decision Submission"
    try:
        payload = {"alert_id": alert_id, "decision": "allow"}
        response = requests.post(
            f"{BACKEND_URL}/upload_decision",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 200
        if passed:
            data = response.json()
            alert_type = data.get("alert_type", "unknown")
            decision = data.get("decision", "unknown")
            details = f"Alert Type: {alert_type}, Decision: {decision}"
        else:
            details = f"Status: {response.status_code}, Response: {response.text}"
        print_test(test_name, passed, details)
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def test_decision_file_activity_alert(alert_id: int) -> bool:
    """Test 5: Submit decision for file activity alert"""
    test_name = "File Activity Alert Decision Submission"
    try:
        payload = {"alert_id": alert_id, "decision": "block"}
        response = requests.post(
            f"{BACKEND_URL}/upload_decision",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 200
        if passed:
            data = response.json()
            alert_type = data.get("alert_type", "unknown")
            decision = data.get("decision", "unknown")
            details = f"Alert Type: {alert_type}, Decision: {decision}"
        else:
            details = f"Status: {response.status_code}, Response: {response.text}"
        print_test(test_name, passed, details)
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def test_invalid_decision() -> bool:
    """Test 6: Invalid decision rejection"""
    test_name = "Invalid Decision Rejection"
    try:
        payload = {"alert_id": 999, "decision": "allow"}
        response = requests.post(
            f"{BACKEND_URL}/upload_decision",
            headers=HEADERS,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 404
        details = f"Expected 404, Got: {response.status_code}"
        print_test(test_name, passed, details)
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def test_missing_api_key() -> bool:
    """Test 7: API key validation"""
    test_name = "API Key Validation"
    try:
        payload = {"alert_id": 1, "decision": "allow"}
        headers = {"Content-Type": "application/json"}  # No API key
        response = requests.post(
            f"{BACKEND_URL}/upload_decision",
            headers=headers,
            json=payload,
            timeout=5
        )
        passed = response.status_code == 401
        details = f"Expected 401, Got: {response.status_code}"
        print_test(test_name, passed, details)
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def test_alert_retrieval() -> bool:
    """Test 8: Alert retrieval after decision"""
    test_name = "Alert Retrieval After Decision"
    try:
        response = requests.get(
            f"{BACKEND_URL}/alerts",
            headers=HEADERS,
            timeout=5
        )
        passed = response.status_code == 200
        alert_count = len(response.json()) if passed else 0
        details = f"Status: {response.status_code}, Alert Count: {alert_count}"
        print_test(test_name, passed, details)
        return passed
    except Exception as e:
        print_test(test_name, False, f"Error: {str(e)}")
        return False

def run_integration_tests():
    """Main test runner"""
    print(f"\n{TestColor.BLUE}{'='*60}")
    print("Investigation Button Integration Test Suite")
    print(f"{'='*60}{TestColor.END}\n")

    tests_passed = 0
    tests_total = 0

    # Test 1: Backend Connection
    tests_total += 1
    if test_backend_connection():
        tests_passed += 1
    else:
        print(f"\n{TestColor.RED}Backend not accessible. Aborting remaining tests.{TestColor.END}\n")
        return

    print()

    # Test 2 & 4: Upload Alert Creation + Decision
    tests_total += 1
    success, upload_alert_id = test_upload_alert_creation()
    if success:
        tests_passed += 1
        time.sleep(0.5)

        tests_total += 1
        if test_decision_upload_alert(upload_alert_id):
            tests_passed += 1
    print()

    # Test 3 & 5: File Activity Alert Creation + Decision
    tests_total += 1
    success, file_activity_alert_id = test_file_activity_alert_creation()
    if success:
        tests_passed += 1
        time.sleep(0.5)

        tests_total += 1
        if test_decision_file_activity_alert(file_activity_alert_id):
            tests_passed += 1
    print()

    # Test 6: Invalid Decision
    tests_total += 1
    if test_invalid_decision():
        tests_passed += 1
    print()

    # Test 7: API Key Validation
    tests_total += 1
    if test_missing_api_key():
        tests_passed += 1
    print()

    # Test 8: Alert Retrieval
    tests_total += 1
    if test_alert_retrieval():
        tests_passed += 1

    # Summary
    print(f"\n{TestColor.BLUE}{'='*60}")
    print(f"Test Summary: {TestColor.GREEN}{tests_passed}{TestColor.END}/{tests_total} passed")

    if tests_passed == tests_total:
        print(f"{TestColor.GREEN}✓ All tests passed!{TestColor.END}")
    else:
        print(f"{TestColor.RED}✗ Some tests failed{TestColor.END}")

    print(f"{'='*60}{TestColor.END}\n")

if __name__ == "__main__":
    run_integration_tests()
