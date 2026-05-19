@echo off
setlocal
cd /d "%~dp0"
title BizOptima Server

echo ==========================================
echo   BizOptima - Local Server
echo ==========================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python was not found. Install Python 3.10+ and try again.
    pause
    exit /b 1
  )
  set "PY_CMD=python"
) else (
  set "PY_CMD=py -3"
)

if not exist "backend\venv\Scripts\python.exe" (
  echo [1/5] Creating virtual environment...
  %PY_CMD% -m venv "backend\venv"
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
) else (
  echo [1/5] Virtual environment already exists.
)

echo [2/5] Upgrading pip...
"backend\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [3/5] Installing project dependencies...
"backend\venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :error

echo [4/5] Preparing machine learning model...
if not exist "backend\ml\saved_model.pkl" (
  pushd backend
  "venv\Scripts\python.exe" "ml\model_training.py"
  if errorlevel 1 (
    popd
    goto :error
  )
  popd
) else (
  echo Model already exists.
)

echo [5/5] Starting Flask server...
echo.
echo Visit: http://127.0.0.1:5000
echo Press CTRL+C to stop the server.
echo.
start "" "http://127.0.0.1:5000"
pushd backend
"venv\Scripts\python.exe" "app.py"
popd
pause
exit /b 0

:error
echo.
echo Setup failed. Review the message above, then run this file again.
pause
exit /b 1
