FROM node:22-bookworm AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/tsconfig.json frontend/vite.config.ts frontend/index.html ./
COPY frontend/src ./src
RUN npm install && npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTIC_OS_ENVIRONMENT=production AGENTIC_OS_DATA_DIR=/data AGENTIC_OS_APP_PORT=3737
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY config ./config
COPY --from=frontend /app/frontend/dist ./backend/static
RUN mkdir -p /data
EXPOSE 3737
CMD ["sh","-c","uvicorn backend.app.main:app --host 0.0.0.0 --port ${AGENTIC_OS_APP_PORT:-3737}"]
