@echo off
setlocal
cd /d "%~dp0"

where code >nul 2>nul
if errorlevel 1 (
  echo VS Code command "code" was not found in PATH.
  echo Open VS Code manually, then choose File ^> Open Folder and select:
  echo %CD%
  pause
  exit /b 1
)

code "%CD%"
echo Opened BizOptima in VS Code.
echo To run the server, double-click start_windows.bat or run it from the VS Code terminal.
pause
