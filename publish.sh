#!/usr/bin/env sh
set -eu

DOCKER_USERNAME="${1:-lokizhan}"
VERSION="${2:-1.0.0}"
IMAGE="${DOCKER_USERNAME}/pcb-file-checker"

printf '%s\n' "Checking Docker..."
docker version >/dev/null

printf '%s\n' "Signing in to Docker Hub..."
docker login

printf '%s\n' "Building ${IMAGE}..."
docker build -t "${IMAGE}:${VERSION}" -t "${IMAGE}:latest" .

printf '%s\n' "Testing the image with the included sample files..."
SAMPLE_PATH="$(cd sample-gerber && pwd)"
docker run --rm -v "${SAMPLE_PATH}:/data:ro" "${IMAGE}:${VERSION}" /data --assembly

printf '%s\n' "Pushing tags..."
docker push "${IMAGE}:${VERSION}"
docker push "${IMAGE}:latest"

printf '%s\n' "Done. Open Docker Hub and add README.md to the Repository overview."
