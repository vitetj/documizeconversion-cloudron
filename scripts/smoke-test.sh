#!/bin/bash
#
# Smoke test for the packaged Documize conversion service.
#
#   scripts/smoke-test.sh https://apidocumize.ixapack.com [document.docx]
#
# Checks that the health endpoint answers and, when a .docx is given, that the
# service really converts it (the reply is a zip holding result.html).

set -eu -o pipefail

readonly URL="${1:-}"
readonly DOCX="${2:-}"

if [[ -z "${URL}" ]]; then
    echo "usage: $0 <service-url> [document.docx]" >&2
    exit 64
fi

echo "==> GET ${URL}/api/version"
version=$(curl -fsS --max-time 30 "${URL}/api/version")
echo "    service reports version ${version}"

if [[ -z "${DOCX}" ]]; then
    echo "==> OK (pass a .docx as second argument to also test conversion)"
    exit 0
fi

if [[ ! -f "${DOCX}" ]]; then
    echo "no such file: ${DOCX}" >&2
    exit 66
fi

out=$(mktemp -d)
trap 'rm -rf "${out}"' EXIT

echo "==> POST ${URL}/api/1/word (${DOCX})"
code=$(curl -s --max-time 300 -o "${out}/result.zip" -w '%{http_code}' \
    -F "wordfile=@${DOCX}" "${URL}/api/1/word")

if [[ "${code}" != "200" ]]; then
    echo "    conversion failed with HTTP ${code}" >&2
    exit 1
fi

if ! unzip -l "${out}/result.zip" | grep -q "result.html"; then
    echo "    reply is not a conversion result archive" >&2
    exit 1
fi

echo "    converted, $(stat -c %s "${out}/result.zip") bytes returned"
echo "==> OK"
