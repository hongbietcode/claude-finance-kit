FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system cfk && useradd --system --gid cfk --create-home cfk
WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[monitor]"

RUN mkdir -p /app/data /app/reports /app/config && chown -R cfk:cfk /app
USER cfk

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD ["cfk", "monitor", "health", "--config", "/app/config/monitor.toml"]

CMD ["cfk", "monitor", "run", "--config", "/app/config/monitor.toml"]
