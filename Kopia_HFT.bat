@echo off
setlocal
cd /d "%~dp0"
title HFT Studio OS - kopia zapasowa

if not exist ".venv\Scripts\python.exe" (
    echo Nie znaleziono przygotowanej aplikacji. Najpierw uruchom Uruchom_HFT.bat.
    goto failed
)

".venv\Scripts\python.exe" -m studio.backup
if errorlevel 1 goto failed
echo.
echo Gotowe. Archiwum ZIP jest w folderze backups.
if /I not "%~1"=="--silent" pause
exit /b 0

:failed
echo.
if /I not "%~1"=="--silent" pause
exit /b 1
