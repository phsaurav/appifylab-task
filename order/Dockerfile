# A two stage docker container creation to get the full python support while building
# Along with a light weight slim python image after building in production

# --- Building Stage ---
  FROM python:3.11.6-bookworm AS builder

  WORKDIR /app
  
  COPY ./requirements.txt .
  RUN pip install --no-cache-dir --upgrade -r requirements.txt
  
  
  # --- Final image ---
  FROM python:3.11.6-slim-bookworm

  ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

  # Create non-root user
  RUN useradd -m -r appuser
  
  WORKDIR /app
  
  # Copy Python dependencies
  COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
  COPY --from=builder /usr/local/bin/ /usr/local/bin/
  
  # Copy application code
  COPY --chown=appuser:appuser . .

  # Switch to non-root user
  USER appuser

