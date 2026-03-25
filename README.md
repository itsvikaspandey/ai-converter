# AI Long-Form to Reels Converter

POC app with:

- FastAPI + Celery + Redis for deterministic video processing
- LangGraph + Ollama for clip scoring and framing decisions
- Streamlit for upload, progress polling, and clip review

## Quick start

1. Copy `.env.example` to `.env`
2. Run `docker-compose up --build`
3. Open `http://localhost:8501`

## Notes

- The pipeline is structured to use local models when installed.
- Safe fallbacks are included so the stack can boot even before every GPU model is available.
- Storage is persisted under `./storage`.
