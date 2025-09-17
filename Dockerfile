FROM python:3.11.13-alpine3.22

ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="/app"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN \
    # Set up SSH and install system packages
    apk add --no-cache openssh git cmake make g++ libpq mesa-gl gdal gdal-dev apache-arrow-dev && \
    # Poetry config
    poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root && \
    # Remove python caches
    rm -rf /root/.cache/pypoetry /root/.cache/pip

COPY start.sh /app/
COPY api /app/api

ENTRYPOINT ["sh", "start.sh"]