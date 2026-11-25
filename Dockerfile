# Ubuntu: Debian images carry unfixed HIGH CVEs that fail the Trivy scan. Python is
# the distribution's so that it is patched with it and visible to the scan.
FROM ubuntu:24.04 AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/bin/python3 \
    UV_LINK_MODE=copy

# git, openssh-client: private git dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    openssh-client \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Build argument for the SSH key: this stage only, so that it is not in the final image history
ARG SSH_PRIVATE_KEY
# Private packages to precompile and source files to remove
ENV PRIVATE_PACKAGES="typo_modal"

WORKDIR /app

# Copy ONLY dependency files first
# This ensures that editing your source code doesn't trigger a full 'uv sync'
COPY uv.lock pyproject.toml /app/

RUN \
    # Set up SSH
    mkdir -p /root/.ssh && \
    echo "${SSH_PRIVATE_KEY}" | base64 -d > /root/.ssh/id_ed25519 && \
    chmod 600 /root/.ssh/id_ed25519 && \
    # Accept host keys automatically
    echo "StrictHostKeyChecking no" >> /root/.ssh/config && \
    # Install dependencies into the virtual environment (UV_PROJECT_ENVIRONMENT)
    uv sync --locked --no-dev --no-install-project --no-cache && \
    # Important: Remove the SSH key after using it
    rm -rf /root/.ssh/ && \
    # Precompile and remove source files
    for pkg in $PRIVATE_PACKAGES; do \
        path=$(/opt/venv/bin/python -c "import $pkg; print($pkg.__path__[0])" 2>/dev/null) && \
        if [ -n "$path" ]; then \
            echo "Compiling $pkg at $path..."; \
            /opt/venv/bin/python -m compileall -b -f "$path"; \
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


FROM ubuntu:24.04
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    DATA_FOLDER="data"

# libexpat1: needed by the osmium wheel
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    ca-certificates \
    libexpat1 \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/data /app/data
COPY start.sh /app/
COPY api /app/api

RUN chmod +x /app/start.sh
ENTRYPOINT ["/bin/sh", "-c", "/app/start.sh"]
