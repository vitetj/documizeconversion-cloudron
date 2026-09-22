#!/usr/bin/env python3
"""Generate CloudronVersions.json from CloudronManifest.json.

A Cloudron server can install this app straight from the resulting file
(Dashboard -> App Store -> install from URL, or `cloudron install --versions-url`),
so the manifest it embeds has to be self-contained: the `file://` fields are
inlined and the image the version refers to is named explicitly.

    scripts/build-versions.py --docker-image ghcr.io/vitetj/documizeconversion-cloudron:1.0.0

Existing versions in the file are kept, so every release stays installable.
"""

import argparse
import collections
import email.utils
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "CloudronManifest.json")
VERSIONS = os.path.join(ROOT, "CloudronVersions.json")
INLINE_FIELDS = ("description", "changelog", "postInstallMessage")


def load_manifest(docker_image):
    with open(MANIFEST) as fh:
        manifest = json.load(fh, object_pairs_hook=collections.OrderedDict)

    for field in INLINE_FIELDS:
        value = manifest.get(field, "")
        if isinstance(value, str) and value.startswith("file://"):
            path = os.path.join(ROOT, value[len("file://"):])
            with open(path) as fh:
                manifest[field] = fh.read().strip()

    manifest["dockerImage"] = docker_image
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-image", required=True,
                        help="image this version installs from, e.g. ghcr.io/owner/app:1.0.0")
    parser.add_argument("--publish-state", default="published",
                        choices=["published", "testing", "revoked"])
    parser.add_argument("--stable", default="true", choices=["true", "false"])
    parser.add_argument("--output", default=VERSIONS)
    args = parser.parse_args()

    manifest = load_manifest(args.docker_image)
    version = manifest["version"]

    if os.path.exists(args.output):
        with open(args.output) as fh:
            catalog = json.load(fh, object_pairs_hook=collections.OrderedDict)
    else:
        catalog = collections.OrderedDict([("stable", True), ("versions", collections.OrderedDict())])

    catalog["stable"] = args.stable == "true"
    versions = catalog.setdefault("versions", collections.OrderedDict())

    now = email.utils.formatdate(usegmt=True)
    previous = versions.get(version, {})

    versions[version] = collections.OrderedDict([
        ("manifest", manifest),
        ("creationDate", previous.get("creationDate", now)),
        ("ts", now),
        ("publishState", args.publish_state),
    ])

    with open(args.output, "w") as fh:
        json.dump(catalog, fh, indent=4)
        fh.write("\n")

    print("%s: version %s -> %s (%s)" % (
        os.path.basename(args.output), version, args.docker_image, args.publish_state),
        file=sys.stderr)


if __name__ == "__main__":
    main()
