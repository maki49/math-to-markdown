@echo off
cd /d "%~dp0"
if not exist ".venv312\Scripts\python.exe" (
  echo Please run setup.cmd first.
  pause
  exit /b 1
)
".venv312\Scripts\python.exe" app.py
if errorlevel 1 pause
