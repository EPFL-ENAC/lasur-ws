FROM python:3.11.7-bullseye
ENV POETRY_VERSION=1.8.3
RUN pip install "poetry==$POETRY_VERSION"
ENV PYTHONPATH="$PYTHONPATH:/app"

# Packages to precompile and source files to remove
ENV COMPILE_PACKAGES="typo_modal"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN \
    # Set up SSH
    apt-get update && apt-get install -y openssh-client git && \
    # Install packages
    poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    apt-get install -y g++ libpq-dev libgl1 gdal-bin libgdal-dev && \
    poetry install --no-interaction --no-root && \
    # Remove python caches
    rm -rf /root/.cache/pypoetry /root/.cache/pip && \
    # Precompile and remove source files
    for pkg in $COMPILE_PACKAGES; do \
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