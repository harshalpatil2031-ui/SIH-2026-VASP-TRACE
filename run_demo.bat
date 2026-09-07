@echo off
echo ======================================================================
echo    VA-TRACE: Automated VASP Attribution ^& Cross-Case Forensics Engine
echo                  Smart India Hackathon (SIH26182)
echo ======================================================================
echo.
echo [1/2] Starting Forensic Intelligence Core Backend (FastAPI)...
start /B python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
timeout /t 2 /nobreak >nul

echo [2/2] Opening Interactive Investigation Dashboard in Browser...
start http://127.0.0.1:8000

echo.
echo ======================================================================
echo   VA-TRACE Dashboard is Live at: http://127.0.0.1:8000
echo   To stop the server, close this command window.
echo ======================================================================
pause
