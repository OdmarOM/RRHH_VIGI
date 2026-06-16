@echo off
REM ============================================================
REM  Arranque interno del servidor RRHH (lo invoca el .vbs oculto)
REM  No ejecutar directamente salvo para depurar.
REM ============================================================
cd /d "%~dp0..\backend"

REM Usar el Python del entorno virtual si existe; si no, el del sistema
set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

REM Carpeta de logs
if not exist "%~dp0logs" mkdir "%~dp0logs"

REM Lanzar el servidor (sirve API + frontend en el puerto 8090)
"%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8090 --workers 1 >> "%~dp0logs\server.log" 2>&1
