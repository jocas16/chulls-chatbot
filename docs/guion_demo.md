# Guion de demo (≈5 min de la exposición)

**Antes de empezar:** `python -m app` y abrir http://127.0.0.1:8000. Comprobar el indicador arriba a la derecha: "DeepSeek activo" o "Modo demostración".
Para empezar con métricas en cero, borra `data/chulls.db` antes de iniciar.

| Paso | Qué hacer | Qué explicar |
|---|---|---|
| 1 | Mostrar la pantalla inicial y `/docs` | Canal web + API REST documentada automáticamente (FastAPI) |
| 2 | **Flujo feliz:** "¿Cuánto cuesta el SOAT para mi moto?" | Intención `soat`; el precio sale del JSON, no del LLM |
| 3 | "Mi placa es 12" | **Error controlado:** validación de formato de placa |
| 4 | "Mi placa es 1234-AB" → "987 654 321" | Memoria: hereda la intención; se crea y completa la **Solicitud #1** |
| 5a | **Postventa:** "¿Mi SOAT está vigente?" → "ABC-123" | Consulta `polizas.csv`: `modo: datos`, link al certificado, resuelto sin asesor |
| 5b | "Quiero renovar, mi DNI es 53251559" | Detecta pólizas vencidas / por vencer y renovación automática |
| 5c | "¿Qué es un deducible?" | RAG: etiqueta `fuente: Deducible` |
| 6 | **Fuera de alcance:** "¿Quién ganó el mundial de fútbol?" | Guardrail: `modo: regla`, no se gasta una llamada al LLM |
| 7 | "Hay heridos tras el choque" | Caso crítico: números de emergencia + derivación |
| 8 | Abrir `/api/solicitudes` y el panel de Métricas | Almacenamiento en SQLite |
| 9 | (Opcional) Ejecutar `pytest -v` | 30+ pruebas automáticas en verde |

**Error extra (si preguntan):** poner una clave inválida en `.env` → el bot responde con `modo: demo_fallback` en lugar de caerse.
