@echo off
echo Starting AI Interview Bot with Face Detection...
echo.

echo Starting Flask API on port 5000...
start "Flask API" cmd /k "python flask_api.py"

timeout /t 3 /nobreak > nul

echo Starting React App on port 3000...
start "React App" cmd /k "npm start"

echo.
echo Both services are starting...
echo Flask API: http://localhost:5000
echo React App: http://localhost:3000
echo.
pause