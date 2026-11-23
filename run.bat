@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo =========================================================
echo   CHULLS SEGUROS - CHATBOT LANGCHAIN + DEEPSEEK
echo =========================================================
where py >nul 2>&1
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creando entorno virtual...
  %PY% -m venv .venv
  if errorlevel 1 (echo ERROR: Instala Python 3.11+ y marca "Add to PATH".& pause & exit /b 1)
)
echo [2/3] Verificando dependencias...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (echo ERROR instalando dependencias. Revisa tu conexion.& pause & exit /b 1)
if not exist ".env" (
  copy /y ".env.example" ".env" >nul
  echo [AVISO] Se creo .env. Agrega tu DEEPSEEK_API_KEY para usar IA real.
  echo         Sin clave, el chatbot funciona en modo demostracion.
)
echo [3/3] Abriendo http://127.0.0.1:8000
start "" "http://127.0.0.1:8000"
".venv\Scripts\python.exe" -m app
pause
