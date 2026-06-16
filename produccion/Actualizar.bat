@echo off
chcp 65001 >nul
setlocal
title Actualizar Sistema RRHH

echo ============================================================
echo    ACTUALIZAR SISTEMA RRHH
echo    (recompila frontend y actualiza dependencias)
echo ============================================================
echo.
echo Detendra el servidor si esta encendido...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8090 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

cd /d "%~dp0..\backend"
echo.
echo [1/3] Actualizando dependencias del backend...
.venv\Scripts\python.exe -m pip install -r requirements.txt

cd /d "%~dp0..\frontend"
echo [2/3] Actualizando dependencias del frontend...
call npm install

echo [3/3] Recompilando el frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: fallo la compilacion del frontend.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    ACTUALIZACION COMPLETADA. Vuelve a iniciar con Iniciar_RRHH.vbs
echo ============================================================
pause
