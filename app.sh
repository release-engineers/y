#!/usr/bin/env bash
#
# This script is used to build and run the application in a docker container.
#
# Run ./app.sh for usage information.
#

set -e
set -o pipefail

function debug() {
  trap 'printf -- "-- \033[0;36m${BASH_COMMAND}\033[0m\n"' DEBUG
}

command=$1

if [[ $command == "build" ]]; then
  debug
  poetry install --sync
  poetry build --format wheel
  poetry run pytest
  version=$(poetry version --short)
  docker build --tag "y:${version}" --file Dockerfile .
  exit 0
fi

if [[ $command == "run" ]]; then
  debug
  version=$(poetry version --short)
  shift
  docker run --rm --publish 8000:8000 "y:${version}" "$@"
  exit 0
fi

if [[ $command == "release" ]]; then
  shift
  release_type=$1
  if [[ -z $release_type ]]; then
    echo "Usage: $0 release <major|minor|patch>"
    exit 1
  fi
  debug
  poetry version "${release_type}"
  version=$(poetry version --short)
  tag="v${version}"
  git add pyproject.toml
  git commit --no-verify --all --message "${release_type} release ${version}"
  git tag "${tag}"
  branch=$(git rev-parse --abbrev-ref HEAD)
  git push --atomic origin "${branch}" "v${version}"
  if [[ -n "${GITHUB_ACTIONS}" ]]; then
    echo "release_version=${version}" | tee -a "${GITHUB_OUTPUT}"
    echo "release_tag=${tag}" | tee -a "${GITHUB_OUTPUT}"
  fi
  exit 0
fi

if [[ $command == "publish-pypi" ]]; then
  debug
  # configure token
  poetry config pypi-token.pypi "${PYPI_TOKEN}"
  poetry publish
  exit 0
fi

if [[ $command == "publish-ghcr" ]]; then
  debug
  version=$(poetry version --short)
  image_tag_local="y:${version}"
  image_tag_github="ghcr.io/release-engineers/${image_tag_local}"
  echo $GITHUB_TOKEN | docker login ghcr.io --username "release-engineers" --password-stdin
  docker tag "${image_tag_local}" "${image_tag_github}"
  docker push "${image_tag_github}"
  exit 0
fi

if [[ -z $command ]]; then
  echo "Unknown command: ${command}"
fi

echo "Usage: $0 <command>"
echo "Commands:"
echo "  build            -- build the docker image containing the local virtualenv and the application"
echo "  run              -- run the docker image associated with the current version, passing any arguments"
echo "  release <type>   -- tag the current revision and bump the version in pyproject.toml"
echo "  publish-pipy     -- publish the current built artifact to pipy under the current version"
echo "  publish-ghcr     -- publish the current built Docker image to the GitHub container registry"

exit 1
