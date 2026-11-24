FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ZoneInfo necesita la base de datos de zonas horarias del sistema.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY src ./src

RUN pip install .

ENTRYPOINT ["vinted"]
CMD ["--dry-run"]
