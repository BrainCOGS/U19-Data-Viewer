FROM python:3-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y openssh-server graphviz \
    && rm -rf /var/lib/apt/lists/*

# UV_PROJECT_ENVIRONMENT puts the venv outside /data_viewer so the
# docker-compose bind mount of the source tree cannot shadow it.
# UV_LINK_MODE=copy silences hardlink warnings, since the uv cache mount and the
# venv sit on separate filesystems.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH=/opt/venv/bin:$PATH

WORKDIR /data_viewer

# Install dependencies in their own layer, ahead of the source copy, so editing
# code does not invalidate the cached dependency install. The manifests are bind
# mounted rather than copied to keep them out of the final image layers.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /data_viewer

# Installed editable (uv's default) on purpose: docker-compose bind mounts the
# source over /data_viewer, and an editable install picks those edits up without
# a rebuild.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 5000
ENTRYPOINT [ "python" ]
CMD [ "/data_viewer/viewer/server.py" ]
