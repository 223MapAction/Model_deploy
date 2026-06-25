@echo off
setlocal EnableDelayedExpansion

echo [INFO] Arret des processus sur le port 8000...
set "FOUND=0"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    set "FOUND=1"
    echo [INFO] Arret du PID %%P
    taskkill /PID %%P /F >nul 2>&1
)

if "!FOUND!"=="0" (
    echo [INFO] Aucun processus en ecoute sur le port 8000.
) else (
    echo [OK] Processus sur le port 8000 arretes.
)

endlocal
