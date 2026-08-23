# BigExtractor - Video MVP

Proto tipo para generar videos de 30 segundos usando FastAPI + RQ + ffmpeg.

Arquitectura mínima incluida:
- FastAPI backend para subir assets y crear jobs
- Redis + RQ para cola y worker
- Worker que ejecuta ffmpeg para producir MP4 de 30s
- Frontend simple para subir imagen/audio y descargar el resultado
- docker-compose para correr todo localmente

Requisitos locales:
- Docker + docker-compose (recomendado)
- En producción: S3 o almacenamiento permanente

Endpoints principales:
- POST /create-video -> sube archivos y encola job, devuelve job_id
- GET /jobs/{id} -> estado y URL de descarga cuando esté listo
- GET /outputs/{file} -> archivos generados (solo para desarrollo)

Cómo probar (local con docker-compose):
1. docker compose up --build
2. Abrir http://localhost:8000 y usar el formulario

Limitaciones MVP:
- Soporta 1 imagen + audio (opcional). Si no hay audio, genera audio silencioso para alcanzar 30s.
- No autenticación, sin límites de uso.
- No TTS ni generación de imágenes aún.
