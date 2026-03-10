FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY feedpulse/ feedpulse/

RUN mkdir -p /app/data

ENV FEEDPULSE_DB_PATH=/app/data/feedpulse.db

CMD ["python", "-m", "feedpulse.main"]
