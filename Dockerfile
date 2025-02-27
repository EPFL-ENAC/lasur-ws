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

# Private packages to precompile and source files to remove
ENV PRIVATE_PACKAGES="typo_modal"

COPY poetry.lock pyproject.toml /app/

RUN poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    apt-get update && apt-get install -y g++ libpq-dev libgl1 gdal-bin libgdal-dev && \
    poetry install --no-interaction --no-root && \
    # Remove python caches
    rm -rf /root/.cache/pypoetry /root/.cache/pip && \
    # Important: Remove the SSH key after using it
    rm -rf /root/.ssh/ && \
    # Precompile and remove source files
    for pkg in $PRIVATE_PACKAGES; do \
        path=$(python -c "import $pkg; print($pkg.__path__[0])" 2>/dev/null) && \
        if [ -n "$path" ]; then \
            echo "Compiling $pkg at $path..."; \
            python -m compileall -b -f "$path"; \
            find "$path" -name "*.py" -type f -delete; \
        else \
            echo "$pkg is not installed."; \
        fi \
    done

COPY start.sh /app/
COPY api /app/api

ENTRYPOINT sh start.sh