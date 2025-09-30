FROM python:3.11.13-trixie

ENV POETRY_VERSION=2.1.3
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="/app"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN \
    # Set up SSH and install system packages
    apt-get update && apt-get install -y git cmake make g++ libpq-dev mesa-utils libgdal-dev && \
    # Poetry config
    poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root -v && \
    # Remove python caches
    rm -rf /root/.cache/pypoetry /root/.cache/pip

COPY start.sh /app/
COPY api /app/api

ENTRYPOINT ["sh", "start.sh"]