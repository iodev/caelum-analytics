FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv sync --frozen

COPY static/ ./static/
COPY templates/ ./templates/

ENV CAELUM_ANALYTICS_HOST=0.0.0.0
ENV CAELUM_ANALYTICS_PORT=8090

EXPOSE 8090

CMD ["uv", "run", "python", "-m", "caelum_analytics.cli", "serve", "--host", "0.0.0.0", "--port", "8090"]