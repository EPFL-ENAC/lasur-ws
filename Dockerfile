FROM python:3.11.7-bullseye
ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

# Install openssh-client
RUN apt-get update && apt-get install -y openssh-client git

# Add build argument for SSH key
ARG SSH_PRIVATE_KEY

# Set up SSH
RUN mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" | base64 -d > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    # Accept host keys automatically
    echo "StrictHostKeyChecking no" >> /root/.ssh/config

WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config installer.max-workers 10
RUN poetry config virtualenvs.create false
RUN apt-get update && apt-get install -y g++ libpq-dev libgl1 gdal-bin libgdal-dev
RUN poetry install --no-interaction --no-root
COPY api /app/api

# Important: Remove the SSH key when no longer needed
RUN rm -rf /root/.ssh/

ENTRYPOINT sh start.sh