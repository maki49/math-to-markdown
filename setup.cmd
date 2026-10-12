@echo off
cd /d "%~dp0"
if not exist ".bootstrap\bin\uv.exe" (
  python -m pip install --target .bootstrap uv
  if errorlevel 1 goto fail
)
".bootstrap\bin\uv.exe" python install 3.12 --install-dir .runtime
if errorlevel 1 goto fail
for /d %%D in (".runtime\cpython-3.12*") do set "MATH_PYTHON=%%~fD\python.exe"
if not exist ".venv312\Scripts\python.exe" (
  "%MATH_PYTHON%" -m venv .venv312
  if errorlevel 1 goto fail
)
".venv312\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Ready. Open start.cmd or the VBS launcher.
pause
exit /b 0
:fail
echo Setup failed. Check your connection and the error above.
pause
exit /b 1
