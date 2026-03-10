FROM python:3.12-slim

WORKDIR /app

# Copy source first (needed for pip install)
COPY pyproject.toml .
COPY feedpulse/ feedpulse/

RUN pip install --no-cache-dir .

RUN mkdir -p /app/data

ENV FEEDPULSE_DB_PATH=/app/data/feedpulse.db

CMD ["python", "-m", "feedpulse.main"]
