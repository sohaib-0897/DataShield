@echo off
cd /d "%~dp0"
if not defined DATASHIELD_API_KEY (
    echo Set DATASHIELD_API_KEY before starting DataShield.
    exit /b 1
)
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
cls
echo ========================================
echo        DataShield DLP SYSTEM
echo          FYP-I Iteration I
echo ========================================

echo Starting all DLP components...
echo.

echo [1/4] Starting Admin Server...
start "DLP Admin Server" cmd /k "python backend/admin_server.py"
timeout /t 2 /nobreak > nul

echo [2/4] Starting Test Upload Server...
start "DLP Test Upload Server" cmd /k "python backend/simple_test_server.py"
timeout /t 2 /nobreak > nul

echo [3/4] Starting File System Monitor...
start "DLP File Monitor" cmd /k "python backend/upload_monitor_agent.py"
timeout /t 2 /nobreak > nul

echo [4/4] Starting React Frontend...
cd frontend
start "DLP Frontend" cmd /k "npm start"
cd ..

echo.
echo ========================================
echo    DLP SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo IMPORTANT LINKS:
echo   Admin Dashboard: http://127.0.0.1:5000
echo   Test Upload:     http://127.0.0.1:8080
echo   Frontend:        http://localhost:3000
echo.
echo NEXT STEPS:
echo   1. In File Monitor GUI, click "Start Monitoring"
echo   2. Open Admin Dashboard in your browser
echo   3. Open Frontend in browser
echo   4. Upload files at Test Upload page
echo   5. Review and approve/block uploads in Admin Dashboard
echo.
echo Press any key to close this window...
pause > nul
