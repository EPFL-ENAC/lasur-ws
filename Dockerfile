FROM python:3.11.7-bullseye
ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

# Enable SSH agent forwarding
RUN apt-get update && apt-get install -y openssh-client

# Set SSH_AUTH_SOCK to use forwarded SSH credentials
ARG SSH_AUTH_SOCK
ENV SSH_AUTH_SOCK=${SSH_AUTH_SOCK}

# Use SSH for accessing private GitHub repos
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config installer.max-workers 10
RUN poetry config virtualenvs.create false
RUN apt-get update && apt-get install -y g++ libpq-dev libgl1 gdal-bin libgdal-dev
RUN poetry install --no-interaction --no-root
COPY api /app/api

ENTRYPOINT sh start.sh