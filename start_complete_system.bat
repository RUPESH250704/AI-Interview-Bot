@echo off
echo Starting AI Interview Bot with Complete Backend Integration...
echo.

echo Starting Face Detection API on port 5000...
start "Face Detection API" cmd /k "python flask_api.py"

timeout /t 2 /nobreak > nul

echo Starting Interview Backend API on port 8000...
start "Interview Backend" cmd /k "python interview_backend.py"

timeout /t 3 /nobreak > nul

echo Starting React Frontend on port 3000...
start "React App" cmd /k "npm start"

echo.
echo All services are starting...
echo Face Detection API: http://localhost:5000
echo Interview Backend: http://localhost:8000  
echo React Frontend: http://localhost:3000
echo.
echo Make sure you have the API key in AIGNITE/key.txt file
echo.
pause