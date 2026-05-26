@echo off
title Pathshala Wear Server
cd /d "%~dp0shopping_assistant"

:loop
echo.
echo ============================================================
echo Pathshala Wear development server
echo URL: http://127.0.0.1:8000/
echo Keep this window open while using the website.
echo If Django exits, this launcher restarts it automatically.
echo ============================================================
echo.
"%~dp0.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000 --noreload
echo.
echo Django stopped. Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto loop
