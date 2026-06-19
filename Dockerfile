# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /srv

FROM base AS deps
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM base AS runtime
COPY --from=deps /install /usr/local
COPY app ./app
COPY migrations ./migrations
EXPOSE 8000
# The same image runs the API (default) and the event workers:
#   docker run ... python -m app.workers.runner
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
