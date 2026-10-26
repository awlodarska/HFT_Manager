@echo off
setlocal
cd /d "%~dp0"
title HFT Studio OS - codzienne kopie

if not exist "Kopia_HFT.bat" (
    echo Nie znaleziono Kopia_HFT.bat. Umiesc ten plik w folderze aplikacji.
    goto failed
)

echo Ten krok doda codzienna kopie danych o 19:00 dla aktualnego konta Windows.
echo Kopie zostana zapisane lokalnie w folderze backups.
choice /M "Zainstalowac zadanie"
if errorlevel 2 exit /b 0

schtasks /Create /TN "HFT Studio OS - codzienna kopia" /TR "cmd.exe /d /c ""%~dp0Kopia_HFT.bat"" --silent" /SC DAILY /ST 19:00 /F
if errorlevel 1 goto failed

echo.
echo Gotowe. Aby zmienic godzine lub wylaczyc kopie, otworz Harmonogram zadan Windows
echo i znajdz zadanie: HFT Studio OS - codzienna kopia.
pause
exit /b 0

:failed
echo.
echo Nie udalo sie dodac zadania. Komunikat bledu jest powyzej.
pause
exit /b 1
