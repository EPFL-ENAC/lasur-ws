FROM python:3.11.13-slim-bookworm

# 1. Environment variables
ENV POETRY_VERSION=2.1.3 \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# 2. Install System Dependencies (This layer changes rarely)
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    make \
    g++ \
    libpq-dev \
    mesa-utils \
    libgdal-dev \
    osmium-tool \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Add build argument for SSH key
ARG SSH_PRIVATE_KEY
# Private packages to precompile and source files to remove
ENV PRIVATE_PACKAGES="typo_modal"

WORKDIR /app

# 4. Copy ONLY dependency files first
# This ensures that editing your source code doesn't trigger a full 'poetry install'
COPY poetry.lock pyproject.toml /app/

RUN \
    # Set up SSH
    apt-get update && apt-get install -y openssh-client git && \
    mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" | base64 -d > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    # Accept host keys automatically
    echo "StrictHostKeyChecking no" >> /root/.ssh/config && \
    # Install system packages
    apt-get install -y git cmake make g++ libpq-dev mesa-utils libgdal-dev && \
    # Poetry config
    poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root -v && \
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

ENTRYPOINT ["sh", "start.sh"]