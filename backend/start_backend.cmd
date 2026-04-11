@echo off
setlocal enabledelayedexpansion

REM Always run from backend root so relative paths work.
cd /d "%~dp0"
set "REPO_ROOT=%~dp0.."

set "PYTHON_EXE="
if exist "%REPO_ROOT%\.venv_run\Scripts\python.exe" set "PYTHON_EXE=%REPO_ROOT%\.venv_run\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%REPO_ROOT%\venv\Scripts\python.exe" set "PYTHON_EXE=%REPO_ROOT%\venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist ".venv_run\Scripts\python.exe" set "PYTHON_EXE=.venv_run\Scripts\python.exe"
if not defined PYTHON_EXE if exist ".venv312\Scripts\python.exe" set "PYTHON_EXE=.venv312\Scripts\python.exe"
if not defined PYTHON_EXE if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"

echo Starting API with: "%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
"%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app
