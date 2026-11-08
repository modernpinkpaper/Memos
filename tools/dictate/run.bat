@echo off
cd /d "%~dp0"
if not exist .venv (
  echo First time setup. This takes a few minutes...
  py -3 -m venv .venv || (echo Install Python from python.org first, tick "Add to PATH". & pause & exit /b)
  .venv\Scripts\pip install -r requirements.txt
)
.venv\Scripts\python dictate.py
pause
