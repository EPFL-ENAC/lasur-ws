FROM python:3.11.13-slim-bookworm

# 1. Environment variables
ENV UV_VERSION=0.12.6 \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    UV_LINK_MODE=copy \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# 2. Install System Dependencies (This layer changes rarely)
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    openssh-client \
    cmake \
    make \
    g++ \
    libpq-dev \
    mesa-utils \
    libgdal-dev \
    osmium-tool \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 3. Install uv
RUN pip install "uv==$UV_VERSION"

# Add build argument for SSH key
ARG SSH_PRIVATE_KEY
# Private packages to precompile and source files to remove
ENV PRIVATE_PACKAGES="typo_modal"

WORKDIR /app

# 4. Copy ONLY dependency files first
# This ensures that editing your source code doesn't trigger a full 'uv sync'
COPY uv.lock pyproject.toml /app/

RUN \
    # Set up SSH
    mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" | base64 -d > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    # Accept host keys automatically
    echo "StrictHostKeyChecking no" >> /root/.ssh/config && \
    # Install dependencies into the system environment (UV_PROJECT_ENVIRONMENT)
    uv sync --locked --no-dev --no-install-project --no-cache && \
    # Remove python caches
    rm -rf /root/.cache/uv /root/.cache/pip && \
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


# Likely temporary: clone the repo itself to get the data from lfs.
# THIS NEEDS THE DEV TO PROCESS THE DATA WITH `make get-data` LOCALLY FIRST, THEN COMMIT THE LFS POINTERS TO THE REPO.
# Otherwise, this image will potentially use outdated data.
ARG DATA_REPO_URL="git@github.com:EPFL-ENAC/lasur-ws.git"
ARG DATA_REPO_BRANCH="dev"
ENV DATA_FOLDER="data"
RUN mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" | base64 -d > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    echo "StrictHostKeyChecking no" >> /root/.ssh/config && \
    GIT_LFS_SKIP_SMUDGE=1 git clone \
        --depth 1 \
        --branch ${DATA_REPO_BRANCH} \
        ${DATA_REPO_URL} /tmp/data_repo && \
    mv /tmp/data_repo/${DATA_FOLDER} /app/${DATA_FOLDER} && \
    rm -rf /tmp/data_repo && \
    rm -rf /root/.ssh/


COPY start.sh /app/
COPY api /app/api
COPY scripts /app/scripts

RUN chmod +x /app/start.sh
ENTRYPOINT ["/bin/sh", "-c", "/app/start.sh data"]