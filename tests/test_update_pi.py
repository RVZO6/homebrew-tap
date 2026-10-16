import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "update_pi", Path(__file__).resolve().parents[1] / "scripts" / "update-pi.py"
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdatePiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cask = Path(self.temp.name) / "pi.rb"
        self.original = (
            'cask "pi" do\n  version "1.2.0"\n'
            f'  sha256 arm: "{"0" * 64}",\n         intel: "{"0" * 64}"\n'
            '  binary "pi/pi"\nend\n'
        )
        self.cask.write_text(self.original)
        self.archives = {name: name.encode() for name in updater.ASSETS.values()}
        self.release = {
            "tag_name": "v1.3.0",
            "draft": False,
            "prerelease": False,
            "assets": [{"name": name} for name in ["SHA256SUMS", *self.archives]],
        }
        self.base_url = f"{updater.RELEASE_URL}/v1.3.0"
        self.manifest = "\n".join(
            f"{hashlib.sha256(data).hexdigest()}  {name}"
            for name, data in self.archives.items()
        )
        self.requests = []

    def fetch(self, url):
        self.requests.append(url)
        if url == updater.API_URL:
            return io.BytesIO(json.dumps(self.release).encode())
        if url == f"{self.base_url}/SHA256SUMS":
            return io.BytesIO(self.manifest.encode())
        return io.BytesIO(self.archives[url.rsplit("/", 1)[1]])

    def update(self):
        with patch.object(updater, "open_url", side_effect=self.fetch):
            return updater.update_cask(self.cask)

    def test_updates_version_and_both_verified_checksums(self):
        self.assertEqual(self.update(), "1.3.0")
        result = self.cask.read_text()
        self.assertIn('version "1.3.0"', result)
        for data in self.archives.values():
            self.assertIn(hashlib.sha256(data).hexdigest(), result)
        self.assertTrue(result.endswith('  binary "pi/pi"\nend\n'))
        self.assertEqual(len(self.requests), 4)

    def test_unchanged_release_only_fetches_metadata(self):
        self.cask.write_text(self.original.replace('"1.2.0"', '"1.3.0"'))
        before = self.cask.read_bytes()
        self.assertIsNone(self.update())
        self.assertEqual(self.cask.read_bytes(), before)
        self.assertEqual(self.requests, [updater.API_URL])

    def test_does_not_downgrade(self):
        self.cask.write_text(self.original.replace('"1.2.0"', '"1.4.0"'))
        before = self.cask.read_bytes()
        self.assertIsNone(self.update())
        self.assertEqual(self.cask.read_bytes(), before)
        self.assertEqual(self.requests, [updater.API_URL])

    def test_corrupt_second_archive_does_not_change_cask(self):
        self.archives[updater.ASSETS["intel"]] = b"corrupt archive"
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_missing_asset_does_not_change_cask(self):
        self.release["assets"].pop()
        with self.assertRaisesRegex(ValueError, "missing required"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_duplicate_checksum_does_not_change_cask(self):
        self.manifest += "\n" + self.manifest.splitlines()[0]
        with self.assertRaisesRegex(ValueError, "Duplicate checksum"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_missing_checksum_does_not_change_cask(self):
        self.manifest = self.manifest.splitlines()[0]
        with self.assertRaisesRegex(ValueError, "Missing checksum"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_rejects_prerelease(self):
        self.release["prerelease"] = True
        with self.assertRaisesRegex(ValueError, "draft or prerelease"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_rejects_unexpected_tag(self):
        self.release["tag_name"] = "v1.3.0-beta.1"
        with self.assertRaisesRegex(ValueError, "Unexpected release tag"):
            self.update()
        self.assertEqual(self.cask.read_text(), self.original)

    def test_rejects_unexpected_cask_layout_before_fetching(self):
        self.cask.write_text(self.original.replace('version "1.2.0"', "version :latest"))
        with self.assertRaisesRegex(ValueError, "Expected one numeric version"):
            self.update()
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
