#!/usr/bin/env bash
# Mirror the air-gapped image manifest into a private registry, OR save it to a portable tar
# for physical transfer into the enclave. One codebase, offline profile (ADR-0011).
#
#   ./mirror-images.sh save   <bundle.tar>                 # connected side: pull + save all images
#   ./mirror-images.sh load   <bundle.tar>                 # enclave side: load images from the tar
#   ./mirror-images.sh push   <registry.airgap.internal/dula>   # enclave side: retag + push to mirror
#
# No image is ever pulled from the public internet inside the enclave.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
MANIFEST="${HERE}/images.txt"
DULA_PREFIX="dula/"

images() { grep -vE '^\s*#|^\s*$' "$MANIFEST"; }

cmd="${1:-}"; arg="${2:-}"
case "$cmd" in
  save)
    [ -n "$arg" ] || { echo "usage: $0 save <bundle.tar>"; exit 2; }
    mapfile -t list < <(images)
    for img in "${list[@]}"; do echo "pull $img"; docker pull "$img"; done
    echo "saving ${#list[@]} images -> $arg"
    docker save "${list[@]}" -o "$arg"
    ;;
  load)
    [ -n "$arg" ] || { echo "usage: $0 load <bundle.tar>"; exit 2; }
    docker load -i "$arg"
    ;;
  push)
    [ -n "$arg" ] || { echo "usage: $0 push <registry/prefix>"; exit 2; }
    reg="${arg%/}"
    while read -r img; do
      # Dula images keep their repo path under the mirror prefix; infra images keep their basename.
      case "$img" in
        ${DULA_PREFIX}*) dest="${reg}/${img#$DULA_PREFIX}" ;;
        *)               dest="${reg}/$(basename "$img")" ;;
      esac
      echo "retag $img -> $dest"
      docker tag "$img" "$dest"
      docker push "$dest"
    done < <(images)
    ;;
  *)
    echo "usage: $0 {save <tar>|load <tar>|push <registry/prefix>}"; exit 2 ;;
esac
