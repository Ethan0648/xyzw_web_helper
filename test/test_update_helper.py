import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile


spec = importlib.util.spec_from_file_location(
    "updater", Path(__file__).resolve().parents[1] / "scripts" / "update-helper.py"
)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateHelperTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.target = self.root / "xyzw-helper"
        self.target.mkdir()
        (self.target / "index.html").write_text("old page")
        self.platform = self.root / "xyzw-platform"
        self.platform.mkdir()
        (self.platform / "index.html").write_text("platform")

    def release(self, files):
        archive = self.root / "dist.zip"
        with zipfile.ZipFile(archive, "w") as output:
            for name, content in files.items():
                output.writestr(name, content)
        (self.root / "dist.zip.sha256").write_text(
            hashlib.sha256(archive.read_bytes()).hexdigest() + "  dist.zip\n"
        )
        (self.root / "release.json").write_text(json.dumps({
            "tag_name": "dist-test",
            "assets": [{"name": name, "browser_download_url": f"https://example.com/{name}"}
                       for name in ("dist.zip", "dist.zip.sha256")],
        }))

    def download(self, url, destination):
        shutil.copyfile(self.root / destination.name, destination)

    def run_update(self):
        with patch.object(updater, "download", side_effect=self.download):
            updater.update(self.target)

    def assert_unchanged(self):
        self.assertEqual((self.target / "index.html").read_text(), "old page")
        self.assertEqual((self.platform / "index.html").read_text(), "platform")

    def test_updates_assets_before_index_and_preserves_platform_and_old_assets(self):
        (self.target / "old.js").write_text("cached asset")
        self.release({"index.html": "new page", "assets/new.js": "new asset"})
        with patch.object(updater.os, "replace", wraps=updater.os.replace) as replace:
            self.run_update()
        self.assertEqual(replace.call_args_list[-1].args[1], self.target / "index.html")
        self.assertEqual((self.target / "index.html").read_text(), "new page")
        self.assertEqual((self.target / "assets/new.js").read_text(), "new asset")
        self.assertEqual((self.target / "old.js").read_text(), "cached asset")
        self.assertEqual((self.platform / "index.html").read_text(), "platform")
        self.assertFalse(list(self.root.glob(".xyzw-helper-update-*")))

    def test_bad_checksum_leaves_site_untouched(self):
        self.release({"index.html": "new page"})
        (self.root / "dist.zip.sha256").write_text("wrong")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.run_update()
        self.assert_unchanged()

    def test_missing_index_leaves_site_untouched(self):
        self.release({"dist/index.html": "wrong archive layout"})
        with self.assertRaisesRegex(ValueError, "index.html"):
            self.run_update()
        self.assert_unchanged()

    def test_path_traversal_cannot_modify_sibling_project(self):
        self.release({"index.html": "new", "../xyzw-platform/index.html": "bad"})
        with self.assertRaisesRegex(ValueError, "不安全路径"):
            self.run_update()
        self.assert_unchanged()

    def test_download_failure_leaves_site_untouched(self):
        with patch.object(updater, "download", side_effect=OSError("network unavailable")):
            with self.assertRaises(OSError):
                updater.update(self.target)
        self.assert_unchanged()

    def test_archive_symlink_is_rejected(self):
        self.release({"index.html": "new"})
        archive = self.root / "dist.zip"
        with zipfile.ZipFile(archive, "a") as output:
            link = zipfile.ZipInfo("assets")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            output.writestr(link, "../xyzw-platform")
        (self.root / "dist.zip.sha256").write_text(hashlib.sha256(archive.read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, "不安全路径"):
            self.run_update()
        self.assert_unchanged()

    @unittest.skipIf(os.name == "nt", "POSIX permissions require Linux")
    def test_readable_permissions_even_with_restrictive_umask(self):
        self.release({"index.html": "new", "assets/nested/app.js": "asset"})
        previous = os.umask(0o077)
        try:
            self.run_update()
        finally:
            os.umask(previous)
        self.assertEqual(stat.S_IMODE((self.target / "assets/nested").stat().st_mode), 0o755)
        self.assertEqual(stat.S_IMODE((self.target / "index.html").stat().st_mode), 0o644)

    def test_existing_symlink_cannot_modify_sibling_project(self):
        self.release({"index.html": "new", "assets/index.html": "bad"})
        try:
            (self.target / "assets").symlink_to(self.platform, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable on this host")
        with self.assertRaisesRegex(ValueError, "符号链接"):
            self.run_update()
        self.assert_unchanged()


if __name__ == "__main__":
    unittest.main()
