FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    APP_ENV=production
COPY pyproject.toml uv.lock README.md ./
COPY agent/ agent/
COPY api/ api/
COPY evaluation/ evaluation/
RUN uv sync --frozen --no-dev
COPY --from=frontend /app/frontend/dist frontend/dist
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
