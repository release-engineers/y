#
# A multi-stage Dockerfile with the following targets:
#
# | Target         | Description                                                                      |
# |----------------|----------------------------------------------------------------------------------|
# | build          | Install non-development dependencies and build the artifact with Poetry          |
# | test           | From build, install development dependencies and run tests                       |
# | release_py     | Copy the artifact from build to a scratch image (run with --output ./dist)       |
# | release_docker | Copy the dependencies and artifact from build to a Python image (default target) |
#
FROM python:3.11-slim as build

# install build tool
RUN pip install --no-cache-dir poetry
WORKDIR /app

# install dependencies
# (with assorted files for it to succeed)
COPY poetry.lock poetry.toml pyproject.toml /app/
RUN mkdir -p /app/y \
    && touch /app/y/__init__.py \
    && touch /app/README.md
RUN poetry install --only main
# build artifact
COPY y /app/y
COPY README.md /app/
RUN poetry build --format wheel

FROM build as test

COPY tests /app/tests
RUN poetry install
RUN poetry run pytest

FROM scratch as release_py

COPY --from=build /app/dist /

FROM python:3.11-alpine as release_docker

LABEL org.opencontainers.image.source=https://github.com/release-engineers/y

ENV PYTHONPATH=/app:/app/.venv/lib/python3.11/site-packages:$PYTHONPATH
COPY --from=build /app/ /app/
RUN rm -rf /app/dist/

ENTRYPOINT ["python", "-m", "y"]
