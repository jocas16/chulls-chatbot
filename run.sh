#!/usr/bin/env bash
# Inicio rápido para macOS / Linux
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[AVISO] Se creó .env. Agrega tu DEEPSEEK_API_KEY para usar IA real (sin clave: modo demo)."
fi
echo "Abriendo http://127.0.0.1:8000  (Ctrl+C para detener)"
python -m app
