"""Offline regressions for explicit catalog admission and per-version ABI selection."""

import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("build_manifest", ROOT / "scripts" / "build_manifest.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def release(version, *, prerelease=False, draft=False):
    return {
        "tag_name": "v" + version,
        "prerelease": prerelease,
        "draft": draft,
        "body": "Release " + version,
        "published_at": "2026-11-01T01:24:09Z",
        "assets": [{"name": "ThemeMusicFinder_" + version + ".zip",
                    "browser_download_url": "https://example.invalid/" + version + ".zip"}],
    }


class CatalogAdmissionTests(unittest.TestCase):
    def source(self):
        return {
            "repository": "example/theme",
            "targetAbi": "12.1.0.0",
            "assetTemplate": "ThemeMusicFinder_{version}.zip",
        }

    def build(self, source, releases):
        self.downloads = []

        def request(url):
            if "/releases?" in url:
                return json.dumps(releases).encode()
            self.downloads.append(url)
            return ("published bytes: " + url).encode()

        with patch.object(builder, "request", side_effect=request):
            return builder.build_versions(source)

    def test_previews_are_excluded_by_default(self):
        versions = self.build(self.source(), [release("1.2.2.2", prerelease=True), release("1.2.1.9")])
        self.assertEqual([v["version"] for v in versions], ["1.2.1.9"])
        self.assertEqual(self.downloads, ["https://example.invalid/1.2.1.9.zip"])

    def test_only_allowlisted_preview_is_admitted_with_its_abi(self):
        source = self.source()
        source["allowedPrereleaseVersions"] = ["1.2.2.2"]
        source["targetAbiOverrides"] = {"1.2.2.2": "12.4.0.0"}
        stable = self.build(self.source(), [release("1.2.1.9")])[0]
        versions = self.build(source, [release("1.2.1.9"), release("1.2.2.1", prerelease=True),
                                       release("1.2.2.2", prerelease=True), release("1.2.2.3", prerelease=True)])
        self.assertEqual([v["version"] for v in versions], ["1.2.2.2", "1.2.1.9"])
        self.assertEqual(versions[0]["targetAbi"], "12.4.0.0")
        self.assertEqual(versions[1], stable)
        self.assertEqual(versions[0]["checksum"], hashlib.md5(
            b"published bytes: https://example.invalid/1.2.2.2.zip", usedforsecurity=False).hexdigest())

    def test_allowlisted_draft_is_always_excluded(self):
        source = self.source()
        source["allowedPrereleaseVersions"] = ["1.2.2.2"]
        self.assertEqual(self.build(source, [release("1.2.2.2", prerelease=True, draft=True)]), [])
        self.assertEqual(self.downloads, [])

    def test_allowlist_does_not_enable_previews_for_another_plugin(self):
        allowed = self.source()
        allowed["allowedPrereleaseVersions"] = ["1.2.2.2"]
        releases = [release("1.2.2.2", prerelease=True)]
        self.assertEqual(len(self.build(allowed, releases)), 1)
        self.assertEqual(self.build(self.source(), releases), [])

    def test_missing_asset_is_not_added(self):
        source = self.source()
        source["allowedPrereleaseVersions"] = ["1.2.2.2"]
        preview = release("1.2.2.2", prerelease=True)
        preview["assets"] = []
        self.assertEqual(self.build(source, [preview]), [])
        self.assertEqual(self.downloads, [])

    def test_actual_configuration_retains_12_1_default_and_pins_only_12_4_preview(self):
        sources = json.loads((ROOT / "plugin-sources.json").read_text(encoding="utf-8"))
        theme = next(s for s in sources if s["guid"] == "03459bac-6165-4b2d-b05f-40b953159b59")
        self.assertEqual(theme["targetAbi"], "12.1.0.0")
        self.assertEqual(theme["targetAbiOverrides"], {"1.2.2.2": "12.4.0.0"})
        self.assertEqual(theme["allowedPrereleaseVersions"], ["1.2.2.2"])


if __name__ == "__main__":
    unittest.main()
