#!/usr/bin/env python3
"""Update the cask only after both official macOS archives pass checksum checks."""

import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen


REPOSITORY = "earendil-works/pi"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASE_URL = f"https://github.com/{REPOSITORY}/releases/download"
ASSETS = {"arm": "pi-darwin-arm64.tar.gz", "intel": "pi-darwin-x64.tar.gz"}
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
VERSION_LINE = re.compile(r'^  version "([0-9]+\.[0-9]+\.[0-9]+)"$', re.MULTILINE)
CHECKSUM_LINES = re.compile(
    r'^  sha256 arm: "[0-9a-f]{64}",\n         intel: "[0-9a-f]{64}"$', re.MULTILINE
)


def open_url(url):
    headers = {"User-Agent": "RVZO6-homebrew-tap"}
    if url == API_URL:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if os.environ.get("GH_TOKEN"):
            headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    return urlopen(Request(url, headers=headers), timeout=60)


def read_metadata(url):
    with open_url(url) as response:
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Release metadata exceeds the size limit")
    return data.decode("utf-8")


def release_checksums(manifest):
    checksums = {}
    for line in manifest.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+\*?(\S+)", line)
        if not match:
            raise ValueError("Invalid SHA256SUMS entry")
        checksum, name = match.groups()
        if name in checksums:
            raise ValueError(f"Duplicate checksum for {name}")
        checksums[name] = checksum
    for name in ASSETS.values():
        if name not in checksums:
            raise ValueError(f"Missing checksum for {name}")
    return checksums


def verify_archive(url, expected):
    digest = hashlib.sha256()
    with open_url(url) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError(f"Checksum mismatch: {url}")


def update_cask(cask_path):
    original = cask_path.read_text(encoding="utf-8")
    current = VERSION_LINE.findall(original)
    if len(current) != 1 or len(CHECKSUM_LINES.findall(original)) != 1:
        raise ValueError("Expected one numeric version and one checksum stanza")

    release = json.loads(read_metadata(API_URL))
    tag = release["tag_name"]
    version = tag.removeprefix("v")
    if tag != f"v{version}" or not VERSION.fullmatch(version):
        raise ValueError(f"Unexpected release tag: {tag}")
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Refusing a draft or prerelease")

    if tuple(map(int, version.split("."))) <= tuple(map(int, current[0].split("."))):
        print(f"No newer release: cask {current[0]}, upstream {version}")
        return None

    published_assets = {asset["name"] for asset in release["assets"]}
    if not {"SHA256SUMS", *ASSETS.values()}.issubset(published_assets):
        raise ValueError("The release is missing required macOS assets")

    base_url = f"{RELEASE_URL}/{tag}"
    checksums = release_checksums(read_metadata(f"{base_url}/SHA256SUMS"))
    for name in ASSETS.values():
        verify_archive(f"{base_url}/{name}", checksums[name])

    updated = VERSION_LINE.sub(f'  version "{version}"', original)
    updated = CHECKSUM_LINES.sub(
        f'  sha256 arm: "{checksums[ASSETS["arm"]]}",\n'
        f'         intel: "{checksums[ASSETS["intel"]]}"',
        updated,
    )
    cask_path.write_text(updated, encoding="utf-8")
    print(f"Updated Pi: {current[0]} -> {version}; both archives verified")
    return version


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    version = update_cask(root / "Casks" / "pi.rb")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"updated={'true' if version else 'false'}\n")
            if version:
                output.write(f"version={version}\n")
