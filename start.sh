#!/bin/bash

set -eu -o pipefail

readonly CODE_DIR="/app/code/documize"
readonly WORK_DIR="/run/documize"
readonly TMP_DIR="/app/data/tmp"
readonly HTTP_PORT="5010"

echo "==> Preparing directories"

# api-linux resolves "java/" and "puppet.js" relative to its working directory and
# the puppeteer wrapper writes documize-pdf.log there, so it cannot run straight
# from the read-only /app/code. Mirror the code into a writable runtime directory.
mkdir -p "${WORK_DIR}"
for entry in api-linux java node_modules package.json puppet.js; do
    ln -sfn "${CODE_DIR}/${entry}" "${WORK_DIR}/${entry}"
done

# Scratch space for uploaded documents and generated PDFs. It lives under
# /app/data because /tmp and /run are small tmpfs mounts on Cloudron and a single
# Word document can be hundreds of megabytes once expanded.
mkdir -p "${TMP_DIR}"
rm -rf "${TMP_DIR}/plugin-tolkien"

chown -R cloudron:cloudron /app/data "${WORK_DIR}"

echo "==> Starting Documize conversion service on port ${HTTP_PORT}"

export TMPDIR="${TMP_DIR}"
export HOME="/home/cloudron"

cd "${WORK_DIR}"
exec /usr/local/bin/gosu cloudron:cloudron "${CODE_DIR}/api-linux" -port "${HTTP_PORT}"
