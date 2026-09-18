#!/usr/bin/env python3
"""Build Jellyfin manifest.json from public GitHub Releases."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = ROOT / "plugin-sources.json"
MANIFEST_PATH = ROOT / "manifest.json"
API_ROOT = "https://api.github.com"
USER_AGENT = "DemonUnchained-Jellyfin-Plugin-Catalog/1.0"


def request(url: str) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()


def version_key(version: str) -> tuple[int, ...]:
    if not re.fullmatch(r"\d+(?:\.\d+)*", version):
        raise ValueError(f"Unsupported numeric version: {version}")
    return tuple(int(part) for part in version.split("."))


def checksum(url: str) -> str:
    return hashlib.md5(request(url), usedforsecurity=False).hexdigest()


def build_versions(source: dict[str, str]) -> list[dict[str, str]]:
    repository = source["repository"]
    releases = json.loads(request(f"{API_ROOT}/repos/{repository}/releases?per_page=30"))
    versions: list[dict[str, str]] = []

    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue

        version = str(release["tag_name"]).removeprefix("v")
        try:
            version_key(version)
        except ValueError as error:
            print(f"Skipping {repository} tag {release['tag_name']}: {error}", file=sys.stderr)
            continue

        expected_asset = source["assetTemplate"].format(version=version)
        asset = next((item for item in release.get("assets", []) if item["name"] == expected_asset), None)
        if asset is None:
            print(f"Skipping {repository} {version}: missing {expected_asset}", file=sys.stderr)
            continue

        download_url = asset["browser_download_url"]
        versions.append(
            {
                "version": version,
                "changelog": release.get("body") or release.get("name") or f"Release {version}",
                "targetAbi": source["targetAbi"],
                "sourceUrl": download_url,
                "checksum": checksum(download_url),
                "timestamp": release.get("published_at") or release.get("created_at"),
            }
        )

    versions.sort(key=lambda item: version_key(item["version"]), reverse=True)
    return versions


def main() -> None:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    manifest = []
    for source in sources:
        versions = build_versions(source)
        if not versions:
            print(f"No published install ZIPs found for {source['repository']}; omitting it for now.")
            continue
        entry = {
            key: source[key]
            for key in ("guid", "name", "description", "overview", "owner", "category")
        }
        if source.get("imageUrl"):
            entry["imageUrl"] = source["imageUrl"]
        entry["versions"] = versions
        manifest.append(entry)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(manifest)} plugin entries to {MANIFEST_PATH}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Catalog generation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
