@echo off
title ElectroDispatch AI v3
cd /d "%~dp0"

echo.
echo  ==========================================
echo   ElectroDispatch AI v3 - Iniciando...
echo  ==========================================
echo.

:: Abre el navegador despues de 3 segundos
start /b cmd /c "timeout /t 3 >nul && start http://localhost:8501"

:: Lanza Streamlit
python -m streamlit run app.py --server.port 8501 --server.headless false

pause
