ARG BASE_IMAGE=python:3.10-slim
FROM ${BASE_IMAGE}

WORKDIR /app

ARG PIP_INDEX_URL=

# System deps for building some Python wheels
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Optional PyPI mirror (e.g. China): set build-arg PIP_INDEX_URL
RUN if [ -n "$PIP_INDEX_URL" ]; then \
      pip install --no-cache-dir -i "$PIP_INDEX_URL" -r requirements.txt; \
    else \
      pip install --no-cache-dir -r requirements.txt; \
    fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
