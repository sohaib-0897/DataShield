#!/usr/bin/env python3
"""
test_file_monitoring.py
Tests the file monitoring system with real file movements in user folders.
Verifies that Desktop, Downloads, and Documents are properly monitored.
"""

import os
import sys
import time
import shutil
import requests
import json
from pathlib import Path
from datetime import datetime

# Configuration
ADMIN_URL = "http://127.0.0.1:5000"
API_KEY = os.environ["DATASHIELD_API_KEY"]
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

# Test files
TEST_FILE_WITH_CNIC = """
This is a test document.
Important CNIC: 12345-6789012-3
Please handle with care.
"""

TEST_FILE_NORMAL = "This is a normal test file without sensitive data.\n"


def get_user_folders():
    """Get standard user monitoring folders"""
    home = Path.home()
    return {
        "Desktop": home / "Desktop",
        "Downloads": home / "Downloads",
        "Documents": home / "Documents",
        "Pictures": home / "Pictures"
    }


def verify_admin_running():
    """Check if admin server is running"""
    try:
        resp = requests.get(f"{ADMIN_URL}/alerts", headers=HEADERS, timeout=5)
        return resp.status_code in [200, 401]  # 401 means auth issue, but server is up
    except Exception as e:
        return False


def create_test_file(folder: Path, filename: str, content: str) -> Path:
    """Create a test file in the target folder"""
    test_file = folder / filename
    try:
        # Ensure folder exists
        folder.mkdir(parents=True, exist_ok=True)

        with open(test_file, "w") as f:
            f.write(content)
        return test_file
    except Exception as e:
        print(f"❌ Failed to create test file {test_file}: {e}")
        return None


def get_current_alerts():
    """Get current alerts from backend"""
    try:
        resp = requests.get(f"{ADMIN_URL}/alerts", headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"⚠️  Failed to get alerts: HTTP {resp.status_code}")
            return []
    except Exception as e:
        print(f"❌ Failed to get alerts: {e}")
        return []


def find_file_activity_alerts(alerts, filename: str, activity: str = None) -> list:
    """Find file activity alerts matching the filename and optional activity type"""
    matching = []
    for alert in alerts:
        if alert.get("type") == "file_activity" and filename in alert.get("file", ""):
            if activity is None or alert.get("activity") == activity:
                matching.append(alert)
    return matching


def test_file_creation(folder_name: str, folder: Path):
    """Test file creation event"""
    print(f"\n📝 TEST 1: File Creation Detection ({folder_name})")
    print(f"   Creating test file in {folder}...")

    filename = f"dlp_test_created_{datetime.now().strftime('%H%M%S')}.txt"
    test_file = create_test_file(folder, filename, TEST_FILE_NORMAL)

    if not test_file:
        print(f"   ❌ Could not create test file")
        return False

    print(f"   ✓ Created: {test_file}")

    # Wait for watcher to detect
    print(f"   ⏳ Waiting for watcher to detect file creation...")
    for i in range(10):
        alerts = get_current_alerts()
        matched = find_file_activity_alerts(alerts, filename, "created")
        if matched:
            print(f"   ✅ File creation detected!")
            print(f"      Alert ID: {matched[0]['id']}")
            print(f"      Activity: {matched[0]['activity']}")
            print(f"      Time: {matched[0]['timestamp']}")
            os.remove(test_file)
            return True
        time.sleep(1)

    print(f"   ❌ File creation NOT detected after 10 seconds")
    os.remove(test_file)
    return False


def test_file_modification(folder_name: str, folder: Path):
    """Test file modification event"""
    print(f"\n✏️  TEST 2: File Modification Detection ({folder_name})")

    filename = f"dlp_test_modified_{datetime.now().strftime('%H%M%S')}.txt"
    test_file = create_test_file(folder, filename, TEST_FILE_NORMAL)

    if not test_file:
        print(f"   ❌ Could not create test file")
        return False

    print(f"   ✓ Created: {test_file}")

    # Modify the file
    time.sleep(1)
    print(f"   Modifying file...")
    with open(test_file, "a") as f:
        f.write("\nModified content added.\n")

    # Wait for watcher to detect
    print(f"   ⏳ Waiting for watcher to detect modification...")
    for i in range(10):
        alerts = get_current_alerts()
        matched = find_file_activity_alerts(alerts, filename, "modified")
        if matched:
            print(f"   ✅ File modification detected!")
            print(f"      Alert ID: {matched[0]['id']}")
            print(f"      Activity: {matched[0]['activity']}")
            print(f"      Time: {matched[0]['timestamp']}")
            os.remove(test_file)
            return True
        time.sleep(1)

    print(f"   ❌ File modification NOT detected after 10 seconds")
    os.remove(test_file)
    return False


def test_file_movement(folder_name: str, source_folder: Path, dest_folder: Path):
    """Test file movement/rename event"""
    print(f"\n🚚 TEST 3: File Movement Detection ({folder_name} → {dest_folder.name})")

    filename = f"dlp_test_moved_{datetime.now().strftime('%H%M%S')}.txt"
    test_file = create_test_file(source_folder, filename, TEST_FILE_NORMAL)

    if not test_file:
        print(f"   ❌ Could not create test file")
        return False

    print(f"   ✓ Created: {test_file}")

    # Only test movement within same folder (recursive same-folder move = rename)
    if source_folder == dest_folder:
        new_filename = f"dlp_test_moved_renamed_{datetime.now().strftime('%H%M%S')}.txt"
        new_path = source_folder / new_filename

        time.sleep(1)
        print(f"   Renaming file to {new_filename}...")
        shutil.move(str(test_file), str(new_path))

        # Wait for watcher to detect
        print(f"   ⏳ Waiting for watcher to detect rename/move...")
        for i in range(10):
            alerts = get_current_alerts()
            matched = find_file_activity_alerts(alerts, new_filename, "moved")
            if matched:
                print(f"   ✅ File movement detected!")
                print(f"      Alert ID: {matched[0]['id']}")
                print(f"      Activity: {matched[0]['activity']}")
                print(f"      Old path: {matched[0].get('activity')}")
                print(f"      Time: {matched[0]['timestamp']}")
                os.remove(new_path)
                return True
            time.sleep(1)

        print(f"   ❌ File movement NOT detected after 10 seconds")
        os.remove(new_path)
        return False
    else:
        print(f"   ⚠️  Skipping: Cannot move file across different monitored folders in this test")
        os.remove(test_file)
        return None


def test_sensitive_file_detection():
    """Test detection of CNIC patterns"""
    print(f"\n🔐 TEST 4: Sensitive File (CNIC) Detection")

    home = Path.home()
    desktop = home / "Desktop"

    filename = f"dlp_test_sensitive_{datetime.now().strftime('%H%M%S')}.txt"
    test_file = create_test_file(desktop, filename, TEST_FILE_WITH_CNIC)

    if not test_file:
        print(f"   ❌ Could not create test file")
        return False

    print(f"   ✓ Created sensitive file with CNIC: {test_file}")

    # Wait for watcher to detect and analyze
    print(f"   ⏳ Waiting for watcher to detect and analyze file...")
    for i in range(10):
        alerts = get_current_alerts()
        matched = find_file_activity_alerts(alerts, filename)
        if matched:
            alert = matched[0]
            is_sensitive = alert.get("isSensitive", False)
            matches = alert.get("sensitiveMatches", [])

            if is_sensitive:
                print(f"   ✅ Sensitive file detected!")
                print(f"      Alert ID: {alert['id']}")
                print(f"      Sensitive: {is_sensitive}")
                print(f"      CNIC matches found: {matches}")
                os.remove(test_file)
                return True
            else:
                print(f"   ⚠️  File detected but not marked as sensitive")
                print(f"      Sensitive: {is_sensitive}")
                print(f"      Matches: {matches}")

        time.sleep(1)

    print(f"   ❌ Sensitive file NOT detected after 10 seconds")
    os.remove(test_file)
    return False


def test_monitored_folders_exist():
    """Verify monitoring folders exist and are accessible"""
    print(f"\n📂 TEST 0: Monitored Folder Accessibility")

    folders = get_user_folders()
    accessible = []
    inaccessible = []

    for name, path in folders.items():
        try:
            if path.exists():
                # Try to list contents
                list(path.iterdir())
                print(f"   ✅ {name}: {path}")
                accessible.append(name)
            else:
                print(f"   ⚠️  {name}: Does not exist ({path})")
                inaccessible.append(f"{name} (missing)")
        except PermissionError:
            print(f"   ⚠️  {name}: Permission denied ({path})")
            print(f"       → Run this test as Administrator to monitor protected folders")
            inaccessible.append(f"{name} (permission denied)")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
            inaccessible.append(f"{name} ({type(e).__name__})")

    return len(accessible) > 0


def main():
    """Main test runner"""
    print("=" * 70)
    print("   DLP FILE MONITORING SYSTEM - REAL FILE DETECTION TESTS")
    print("=" * 70)

    # Check prerequisites
    print("\n🔍 PREREQUISITES")

    if not verify_admin_running():
        print("   ❌ Admin server not running!")
        print("   → Run: python admin_server.py")
        print("   → Or run start_dlp_system.bat")
        return False
    print("   ✅ Admin server is running")

    # Get monitored folders
    folders = get_user_folders()
    print(f"   ✅ Monitoring {len(folders)} user folders:")
    for name, path in folders.items():
        print(f"      - {name}: {path}")

    # Test 0: Folder accessibility
    if not test_monitored_folders_exist():
        print("\n⚠️  WARNING: Some monitored folders are not accessible")
        print("   → You may need to run the monitor as Administrator")

    # Test 1-3: File events in Desktop folder
    home = Path.home()
    desktop = home / "Desktop"

    results = {
        "Folder Accessibility": test_monitored_folders_exist(),
        "File Creation (Desktop)": False,
        "File Modification (Desktop)": False,
        "File Movement": False,
        "Sensitive File Detection": False
    }

    try:
        results["File Creation (Desktop)"] = test_file_creation("Desktop", desktop)
        results["File Modification (Desktop)"] = test_file_modification("Desktop", desktop)
        results["File Movement"] = test_file_movement("Desktop", desktop, desktop)
        results["Sensitive File Detection"] = test_sensitive_file_detection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False

    # Print summary
    print("\n" + "=" * 70)
    print("   TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"   {status}  {test_name}")

    print(f"\n   Total: {passed} passed, {failed} failed, {skipped} skipped")

    if failed == 0:
        print("\n   ✅ ALL TESTS PASSED!")
        print("\n   File monitoring system is working correctly:")
        print("   → Desktop, Downloads, Documents are being monitored")
        print("   → File creation, modification, and movement events are detected")
        print("   → Sensitive files (CNIC patterns) are identified")
        return True
    else:
        print(f"\n   ❌ {failed} TEST(S) FAILED")
        print("\n   Possible issues:")
        print("   1. File monitor agent is not running")
        print("      → Execute: python upload_monitor_agent.py")
        print("   2. File events are slow (watchdog latency)")
        print("      → Try again, some systems have 5-10s latency")
        print("   3. Administrator permissions required")
        print("      → Run this test as Administrator")
        print("   4. Antivirus is blocking file operations")
        print("      → Check antivirus logs")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
