@echo off
REM SC Bauplan-Planer neu bauen (Baupläne live von star-head.de ziehen).
cd /d "%~dp0"
py bauplan_planer_bauen.py
if errorlevel 1 (
  echo.
  echo FEHLER beim Bauen - bitte Internetverbindung pruefen.
  pause
  exit /b 1
)
echo.
echo Fertig. SC_Bauplan_Planer.html wurde aktualisiert.
pause
