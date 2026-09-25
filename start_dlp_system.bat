@echo off
cd /d "%~dp0"
if not exist ".env" (
  echo Copy .env.example to .env and set both secrets before starting.
  exit /b 1
)
docker compose up --build -d
if errorlevel 1 exit /b 1
echo DataShield UI: http://localhost:3001
echo DataShield API: http://localhost:8000/docs
echo Seed demo: docker compose exec -e DATASHIELD_DEMO_ADMIN_PASSWORD=YOUR_PASSWORD backend python scripts/seed_demo.py
