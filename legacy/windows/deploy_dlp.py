#!/usr/bin/env python3
"""
deploy_dlp.py
Deployment script for DLP Upload Monitoring System
Installs the system on multiple PCs in a small network.
"""

import os
import sys
import subprocess
import shutil
import json
import logging
from pathlib import Path
import winreg

# Configuration
INSTALL_DIR = "C:/Program Files/DLPMonitor"
SERVICE_NAME = "DLPMonitorService"
ADMIN_SERVER_IP = "192.168.100.80"  # Change to your admin server IP

def setup_logging():
    """Setup logging for deployment"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler('deploy_dlp.log'),
            logging.StreamHandler()
        ]
    )

def check_admin_rights():
    """Check if running with administrator privileges"""
    try:
        return subprocess.check_output(['whoami', '/priv'],
                                     capture_output=True, text=True).find('SeDebugPrivilege') != -1
    except:
        return False

def install_python_dependencies():
    """Install required Python packages"""
    logging.info("Installing Python dependencies...")

    requirements = [
        'requests>=2.25.0',
        'watchdog>=2.1.0',
        'psutil>=5.8.0',
        'pywin32>=300'  # For Windows service
    ]

    for package in requirements:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package],
                         check=True, capture_output=True)
            logging.info(f"Installed {package}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install {package}: {e}")
            return False

    return True

def create_installation_directory():
    """Create installation directory"""
    try:
        install_path = Path(INSTALL_DIR)
        install_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created installation directory: {install_path}")
        return install_path
    except Exception as e:
        logging.error(f"Failed to create installation directory: {e}")
        return None

def copy_files(install_path):
    """Copy DLP files to installation directory"""
    try:
        files_to_copy = [
            'network_monitor_agent.py',
            'upload_monitor_agent.py',
            'dlp_windows_service.py',
            'http_upload_blocker.py',
            'requirements.txt'
        ]

        for file_name in files_to_copy:
            if os.path.exists(file_name):
                shutil.copy2(file_name, install_path / file_name)
                logging.info(f"Copied {file_name}")
            else:
                logging.warning(f"File not found: {file_name}")

        return True
    except Exception as e:
        logging.error(f"Failed to copy files: {e}")
        return False

def update_config_for_network(install_path):
    """Update configuration for network deployment"""
    try:
        # Update network monitor agent config
        network_monitor_file = install_path / 'network_monitor_agent.py'
        if network_monitor_file.exists():
            with open(network_monitor_file, 'r') as f:
                content = f.read()

            # Update admin server URL to use network IP
            content = content.replace(
                'ADMIN_SERVER_URL = "http://127.0.0.1:5000/upload_alert"',
                f'ADMIN_SERVER_URL = "http://{ADMIN_SERVER_IP}:5000/upload_alert"'
            )

            with open(network_monitor_file, 'w') as f:
                f.write(content)

            logging.info("Updated network monitor configuration")

        return True
    except Exception as e:
        logging.error(f"Failed to update configuration: {e}")
        return False

def install_windows_service(install_path):
    """Install the Windows service"""
    try:
        # Change to installation directory
        os.chdir(install_path)

        # Install the service
        result = subprocess.run([
            sys.executable, 'dlp_windows_service.py', 'install'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("Windows service installed successfully")
            return True
        else:
            logging.error(f"Failed to install service: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"Error installing service: {e}")
        return False

def start_windows_service():
    """Start the Windows service"""
    try:
        result = subprocess.run(['net', 'start', SERVICE_NAME],
                              capture_output=True, text=True)

        if result.returncode == 0:
            logging.info("DLP service started successfully")
            return True
        else:
            logging.error(f"Failed to start service: {result.stderr}")
            return False

    except Exception as e:
        logging.error(f"Error starting service: {e}")
        return False

def create_startup_script(install_path):
    """Create a startup script for manual installation"""
    startup_script = install_path / 'start_dlp.bat'

    script_content = f"""@echo off
echo Starting DLP Upload Monitor...
cd /d "{install_path}"
python network_monitor_agent.py
pause
"""

    try:
        with open(startup_script, 'w') as f:
            f.write(script_content)
        logging.info("Created startup script")
        return True
    except Exception as e:
        logging.error(f"Failed to create startup script: {e}")
        return False

def create_uninstall_script(install_path):
    """Create uninstall script"""
    uninstall_script = install_path / 'uninstall_dlp.bat'

    script_content = f"""@echo off
echo Uninstalling DLP Upload Monitor...
net stop {SERVICE_NAME}
python dlp_windows_service.py uninstall
rmdir /s /q "{install_path}"
echo DLP Upload Monitor uninstalled.
pause
"""

    try:
        with open(uninstall_script, 'w') as f:
            f.write(script_content)
        logging.info("Created uninstall script")
        return True
    except Exception as e:
        logging.error(f"Failed to create uninstall script: {e}")
        return False

def deploy_to_network_pc(pc_name):
    """Deploy DLP to a specific network PC"""
    logging.info(f"Deploying to PC: {pc_name}")

    try:
        # Copy files to network PC
        network_path = f"\\\\{pc_name}\\C$\\Program Files\\DLPMonitor"

        # Create remote directory
        subprocess.run(['mkdir', network_path], check=True)

        # Copy files
        files_to_copy = [
            'network_monitor_agent.py',
            'upload_monitor_agent.py',
            'dlp_windows_service.py',
            'http_upload_blocker.py',
            'requirements.txt'
        ]

        for file_name in files_to_copy:
            if os.path.exists(file_name):
                remote_file = f"{network_path}\\{file_name}"
                shutil.copy2(file_name, remote_file)
                logging.info(f"Copied {file_name} to {pc_name}")

        # Install service on remote PC
        subprocess.run([
            'psexec', f'\\\\{pc_name}',
            'python', f'{network_path}\\dlp_windows_service.py', 'install'
        ], check=True)

        # Start service on remote PC
        subprocess.run([
            'psexec', f'\\\\{pc_name}',
            'net', 'start', SERVICE_NAME
        ], check=True)

        logging.info(f"Successfully deployed to {pc_name}")
        return True

    except Exception as e:
        logging.error(f"Failed to deploy to {pc_name}: {e}")
        return False

def main():
    """Main deployment function"""
    print("🔒 DLP Upload Monitor - Network Deployment")
    print("=" * 50)

    setup_logging()

    # Check admin rights
    if not check_admin_rights():
        print("❌ This script requires administrator privileges!")
        print("Please run as Administrator")
        return False

    print("✅ Running with administrator privileges")

    # Install dependencies
    if not install_python_dependencies():
        print("❌ Failed to install dependencies")
        return False

    print("✅ Dependencies installed")

    # Create installation directory
    install_path = create_installation_directory()
    if not install_path:
        print("❌ Failed to create installation directory")
        return False

    print("✅ Installation directory created")

    # Copy files
    if not copy_files(install_path):
        print("❌ Failed to copy files")
        return False

    print("✅ Files copied")

    # Update configuration
    if not update_config_for_network(install_path):
        print("❌ Failed to update configuration")
        return False

    print("✅ Configuration updated")

    # Install Windows service
    if not install_windows_service(install_path):
        print("❌ Failed to install Windows service")
        return False

    print("✅ Windows service installed")

    # Start service
    if not start_windows_service():
        print("❌ Failed to start service")
        return False

    print("✅ Service started")

    # Create utility scripts
    create_startup_script(install_path)
    create_uninstall_script(install_path)

    print("\n🎉 DLP Upload Monitor deployed successfully!")
    print(f"Installation directory: {install_path}")
    print(f"Service name: {SERVICE_NAME}")
    print(f"Admin server: http://{ADMIN_SERVER_IP}:5000")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
