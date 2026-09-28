@echo off
rem Rebuild the site, then preview it at http://localhost:8000 (Ctrl+C to stop)
cd /d "%~dp0"
python build.py || (pause & exit /b 1)
start "" http://localhost:8000
python -m http.server 8000
