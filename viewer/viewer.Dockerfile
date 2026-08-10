FROM python:3-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y openssh-server graphviz \
    && rm -rf /var/lib/apt/lists/*

# The venv lives outside /data_viewer so the docker-compose bind mount of the
# source tree cannot shadow the installed dependencies.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH=/opt/venv/bin:$PATH

# Install dependencies first, in their own layer, so editing the source does not
# invalidate the dependency cache.
WORKDIR /data_viewer
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . /data_viewer
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "/data_viewer/viewer/server.py" ]
