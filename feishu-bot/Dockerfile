# Build from repository root: context=. dockerfile=feishu-bot/Dockerfile
ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

WORKDIR /app

ARG PIP_INDEX_URL=

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Reuse backend lockfile for shared agents/data stack
COPY backend/requirements.txt /app/requirements.txt
RUN if [ -n "$PIP_INDEX_URL" ]; then \
      pip install --no-cache-dir -i "$PIP_INDEX_URL" -r /app/requirements.txt; \
    else \
      pip install --no-cache-dir -r /app/requirements.txt; \
    fi

# Bot entry imports backend packages (agents, config, data)
COPY backend /app/backend
COPY feishu-bot /app/feishu-bot

# run.py imports feishu_bot.bot (underscore package name)
RUN ln -sf /app/feishu-bot /app/feishu_bot

WORKDIR /app/feishu-bot
ENV PYTHONPATH=/app:/app/backend

EXPOSE 8001

CMD ["python", "run.py"]
