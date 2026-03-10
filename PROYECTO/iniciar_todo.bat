@echo off
title ElectroDispatch AI - Sistema Completo
cd /d "%~dp0"

echo.
echo  ===========================================================
echo   ElectroDispatch AI - Iniciando Sistema Completo
echo  ===========================================================
echo.

:: Matar procesos previos de python para evitar duplicados
taskkill /F /IM python.exe /T >nul 2>&1

echo [1/2] Iniciando Bot de Telegram en segundo plano...
start /b cmd /c "python telegram_bot.py"

echo [2/2] Iniciando Dashboard Web...
echo Abrir en: http://localhost:8501
timeout /t 2 >nul
start http://localhost:8501

python -m streamlit run app.py --server.port 8501 --server.headless false

pause
