FROM python:3.12-slim

WORKDIR /app

# ffmpeg is a system binary, not a pip package - required for episode export
# (app/assembler/). --no-install-recommends skips hardware video-acceleration
# drivers that are irrelevant for the software encoding this app does.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000

# Migrations run on every start. alembic upgrade head is a no-op once the
# database is already current, so this is safe to run unconditionally.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
