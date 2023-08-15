#
# A multi-stage Dockerfile.
#
# Contains the following build arguments:
#
# | Argument         | Description                                                                    |
# |------------------|--------------------------------------------------------------------------------|
# | ARTIFACT_VERSION | The version to assign to the artifact (default: 0.0.0)                         |
#
# Contains the following targets:
#
# | Target                | Description                                                                      | Run by default |
# |-----------------------|----------------------------------------------------------------------------------|----------------|
# | resolve_dependencies  | Install non-development dependencies with Poetry                                 | Yes            |
# | build                 | Using Poetry, build the artifact                                                 | Yes            |
# | test                  | Using Poetry and Pytest, install development dependencies and run tests          | No             |
# | release_py            | Copy the artifact from build to a scratch image (run with --output ./dist)       | No             |
# | release_docker        | Copy the dependencies and artifact from build to a Python image (default target) | Yes            |
#
FROM python:3.11-slim as resolve_dependencies

RUN pip install --no-cache-dir poetry
WORKDIR /app

COPY poetry.lock poetry.toml pyproject.toml /app/
RUN mkdir -p /app/y \
    && touch /app/y/__init__.py \
    && touch /app/README.md
RUN poetry install --only main

FROM resolve_dependencies as build

ARG ARTIFACT_VERSION=0.0.0
COPY y /app/y
RUN poetry version "$ARTIFACT_VERSION"
RUN poetry build --format wheel

FROM build as test

COPY tests /app/tests
RUN poetry install
RUN poetry run pytest

FROM scratch as release_py

COPY --from=build /app/dist /

FROM python:3.11-alpine as release_docker

LABEL org.opencontainers.image.source=https://github.com/release-engineers/y

COPY --from=resolve_dependencies /app/.venv/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=build /app/dist/*.whl /app/dist/
RUN pip install --no-cache-dir /app/dist/*.whl \
    && rm -rf /app/dist

ENTRYPOINT ["python", "-m", "y"]
