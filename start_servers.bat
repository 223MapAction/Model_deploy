@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [INFO] Demarrage de l'API Map Action sur http://localhost:8000
start "MapAction-API" cmd /k "cd /d "%ROOT_DIR%" && python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul
echo [INFO] Ouverture du dashboard...
start "" "http://localhost:8000/dashboard"

echo [OK] Serveur lance. Utilisez stop_servers.bat pour l'arreter.
endlocal
