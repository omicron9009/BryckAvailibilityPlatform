FROM python:3.12-slim

# Security: non-root user
RUN groupadd --gid 1001 bryck && \
    useradd --uid 1001 --gid bryck --shell /bin/bash --create-home bryck

WORKDIR /app

# Install deps first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ownership
RUN chown -R bryck:bryck /app

USER bryck

EXPOSE 8000

# Entrypoint: run migrations then start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]
