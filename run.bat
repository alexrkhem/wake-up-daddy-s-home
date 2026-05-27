@echo off
echo.
echo  ========================================
echo    Jarvis Personal Dashboard
echo  ========================================
echo.
cd /d "%~dp0"
if not exist ".env" (
    echo  Creating .env from template...
    copy .env.example .env
    echo  Please edit .env and add your ANTHROPIC_API_KEY
    echo.
)
echo  Starting dashboard on http://localhost:8501
echo  Press Ctrl+C to stop.
echo.
streamlit run app.py --server.port 8501 --server.address localhost
pause
