@echo off
chcp 65001 >nul
title Estado Sistema RRHH

echo ============================================================
echo    ESTADO DEL SISTEMA RRHH (puerto 8090)
echo ============================================================
echo.

powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort 8090 -State Listen -ErrorAction SilentlyContinue; if ($c) { Write-Host '  ESTADO: ENCENDIDO (escuchando en el puerto 8090)' -ForegroundColor Green } else { Write-Host '  ESTADO: APAGADO' -ForegroundColor Yellow }"

echo.
echo  Acceso local: http://localhost:8090
echo.
pause
