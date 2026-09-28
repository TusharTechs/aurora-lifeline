# AURORA Lifeline API image. Build context is the repository root, with the published run JSON
# unpacked into ./runs (CI does this from the web-data branch):
#   docker build -f services/api/Dockerfile -t aurora-api .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    AURORA_RUNS_DIR=/app/runs AURORA_SCHEMAS_DIR=/app/schemas
WORKDIR /app
# Workspace manifests first (dependency layer is cached until the lock changes).
COPY pyproject.toml uv.lock ./
COPY engine/pyproject.toml engine/pyproject.toml
COPY pipelines/pyproject.toml pipelines/pyproject.toml
COPY agents/pyproject.toml agents/pyproject.toml
COPY services/api/pyproject.toml services/api/pyproject.toml
RUN uv sync --locked --no-dev --package aurora-api --no-install-workspace
COPY schemas schemas
COPY agents agents
COPY services/api services/api
RUN uv sync --locked --no-dev --package aurora-api
COPY runs runs
RUN useradd --uid 10001 --no-create-home app
USER app
EXPOSE 8080
CMD ["sh", "-c", "exec /app/.venv/bin/uvicorn aurora_api.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
