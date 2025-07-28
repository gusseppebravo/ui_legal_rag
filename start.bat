@echo off
echo Starting Legal Document Search UI...
echo.
echo This will start the Streamlit application on http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

cd /d "%~dp0"
"%USERPROFILE%\.local\bin\uv.exe" run streamlit run app.py

pause
