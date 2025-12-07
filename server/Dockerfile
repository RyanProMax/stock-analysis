# -------------------------------------------------------------
# Stage 1: Build dependencies with Poetry
# -------------------------------------------------------------
FROM python:3.12.12-slim AS builder

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files for efficient caching
COPY pyproject.toml poetry.lock* README.md ./

# Install poetry
RUN pip install --no-cache-dir poetry

# Install dependencies (no venv)
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Copy application source (including /server)
COPY . .

# Ensure dependencies installed after source copied
RUN poetry install --only main --no-interaction --no-ansi


# -------------------------------------------------------------
# Stage 2: Minimal production image
# -------------------------------------------------------------
FROM python:3.12.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

WORKDIR /app

# Set timezone
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copy built app from builder stage
COPY --from=builder /app /app

# Expose Cloud Run port
EXPOSE 8080

# Use uvicorn directly (production mode)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
