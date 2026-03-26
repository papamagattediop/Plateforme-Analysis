@echo off
echo ============================================
echo   CensusAnalyse - Lancement local (dev)
echo ============================================

set "ROOT=%~dp0"
set "PYTHON=%ROOT%venv\Scripts\python.exe"

:: Migrations en parallele
echo.
echo [1/4] Migrations (paralleles)...

start /b "" cmd /c "cd /d "%ROOT%service_import"  & "%PYTHON%" manage.py migrate --run-syncdb -v 0 > "%ROOT%migrate_import.log"  2>&1"
start /b "" cmd /c "cd /d "%ROOT%service_analyse" & "%PYTHON%" manage.py migrate --run-syncdb -v 0 > "%ROOT%migrate_analyse.log" 2>&1"
start /b "" cmd /c "cd /d "%ROOT%service_visu"    & "%PYTHON%" manage.py migrate --run-syncdb -v 0 > "%ROOT%migrate_visu.log"    2>&1"

:: Attendre la fin des migrations
timeout /t 12 /nobreak >nul
echo     Migrations terminees. Voir migrate_*.log si erreur.

:: Lancement des 3 services dans des fenetres separees
echo.
echo [2/4] Lancement service_import  -^> http://localhost:8001
start "service_import"  cmd /k "cd /d "%ROOT%service_import" & "%PYTHON%" manage.py runserver 8001"

echo [3/4] Lancement service_analyse -^> http://localhost:8002
start "service_analyse" cmd /k "cd /d "%ROOT%service_analyse" & "%PYTHON%" manage.py runserver 8002"

echo [4/4] Lancement service_visu    -^> http://localhost:8003
start "service_visu"    cmd /k "cd /d "%ROOT%service_visu" & "%PYTHON%" manage.py runserver 8003"

:: Ouvrir le navigateur sur le dashboard
timeout /t 3 /nobreak >nul
start "" "http://localhost:8003/dashboard/"

echo.
echo ============================================
echo   StatVision - Plateforme Analytics
echo   Dashboard : http://localhost:8003/dashboard/
echo   Import    : http://localhost:8001
echo   Analyse   : http://localhost:8002
echo   Visu      : http://localhost:8003
echo ============================================
pause
