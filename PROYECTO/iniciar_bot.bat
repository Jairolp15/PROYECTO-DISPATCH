@echo off
title ElectroDispatch AI - Telegram Bot
cd /d "%~dp0"
echo Verificando dependencias...
pip install -r requirements.txt
echo.
echo ==========================================
echo   Iniciando Bot de Telegram...
echo   Bot: @tetranutabot
echo ==========================================
echo.
python telegram_bot.py
pause
