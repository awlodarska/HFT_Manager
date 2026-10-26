@echo off
setlocal
cd /d "%~dp0"
title HFT Studio OS

if not exist "app.py" (
    echo Nie znaleziono app.py. Umiesc ten plik w folderze aplikacji.
    goto failed
)

if exist ".venv\Scripts\python.exe" goto verify

echo Przygotowanie srodowiska. Pierwszy start moze potrwac kilka minut.
py -3.12 -m venv .venv
if not errorlevel 1 goto install
py -3.11 -m venv .venv
if not errorlevel 1 goto install
echo Zainstaluj Python 3.12 z python.org, a potem uruchom ten plik ponownie.
goto failed

:verify
".venv\Scripts\python.exe" -c "import streamlit, pandas, plotly, numpy, filelock" >nul 2>&1
if errorlevel 1 goto install
goto launch

:install
echo Instalowanie wymaganych bibliotek...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "import streamlit, pandas, plotly, numpy, filelock"
if errorlevel 1 goto failed

:launch
if /I "%~1"=="--check" (
    echo Python i biblioteki sa gotowe.
    exit /b 0
)
".venv\Scripts\python.exe" -m studio.backup
if errorlevel 1 echo UWAGA: Nie udalo sie utworzyc kopii zapasowej. Aplikacja zostanie uruchomiona mimo to.
echo.
echo HFT Studio OS - aplikacja otworzy sie w przegladarce.
echo Pozostaw to okno otwarte podczas pracy. Zatrzymanie: Ctrl+C.
echo Jesli przegladarka sie nie otworzy, wpisz: http://localhost:8502
echo Jesli port 8502 jest zajety, zamknij poprzednie okno aplikacji.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --server.headless false --browser.gatherUsageStats false
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo Nie udalo sie uruchomic aplikacji. Komunikat bledu jest powyzej.
if /I not "%~1"=="--check" pause
exit /b 1
