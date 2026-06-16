@echo off
chcp 65001 >nul
setlocal
title Instalacion Sistema RRHH

echo ============================================================
echo    INSTALACION DEL SISTEMA RRHH (PRODUCCION)
echo ============================================================
echo.
echo Este proceso solo se ejecuta UNA vez (o tras actualizar el codigo).
echo.

REM ---------- BACKEND ----------
cd /d "%~dp0..\backend"

echo [1/5] Creando entorno virtual de Python (.venv)...
python -m venv .venv
if errorlevel 1 (
    echo.
    echo ERROR: no se pudo crear el entorno virtual.
    echo Verifica que Python este instalado y en el PATH.
    pause
    exit /b 1
)

echo [2/5] Instalando dependencias del backend...
.venv\Scripts\python.exe -m pip install --upgrade pip >nul
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: fallo la instalacion de dependencias del backend.
    pause
    exit /b 1
)

echo [3/5] Generando clave secreta (SECRET_KEY)...
if not exist ".env" copy ".env.example" ".env" >nul
.venv\Scripts\python.exe -c "import secrets,re;from pathlib import Path;p=Path('.env');t=p.read_text(encoding='utf-8');t=re.sub(r'SECRET_KEY=.*','SECRET_KEY='+secrets.token_urlsafe(48),t,count=1);p.write_text(t,encoding='utf-8');print('   SECRET_KEY generada correctamente.')"

REM ---------- FRONTEND ----------
cd /d "%~dp0..\frontend"

echo [4/5] Instalando dependencias del frontend (npm install)...
call npm install
if errorlevel 1 (
    echo.
    echo ERROR: fallo npm install. Verifica que Node.js este instalado.
    pause
    exit /b 1
)

echo [5/5] Compilando el frontend (build de produccion)...
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: fallo la compilacion del frontend.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    INSTALACION COMPLETADA
echo ============================================================
echo.
echo  - Para ENCENDER:  doble clic en "Iniciar_RRHH.vbs"
echo  - Para APAGAR:     doble clic en "Detener_RRHH.vbs"
echo  - Acceso local:    http://localhost:8090
echo.
pause
