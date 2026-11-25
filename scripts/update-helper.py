#!/usr/bin/env python3
"""Download the latest public dist release and update only xyzw-helper."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile


REPOSITORY = "Ethan0648/xyzw_web_helper"
TARGET = Path("/root/xyzw-helper")


def download(url, destination):
    request = Request(url, headers={"User-Agent": "xyzw-helper-updater"})
    with urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def update(target):
    if target.is_symlink():
        raise ValueError("网站目录不能是符号链接")
    # Staging on the same filesystem allows atomic replacement of each file.
    with tempfile.TemporaryDirectory(prefix=".xyzw-helper-update-", dir=target.parent) as temporary:
        staging = Path(temporary)
        metadata = staging / "release.json"
        download(f"https://api.github.com/repos/{REPOSITORY}/releases/latest", metadata)
        release = json.loads(metadata.read_text(encoding="utf-8"))
        assets = {asset["name"]: asset["browser_download_url"] for asset in release["assets"]}
        # Resolve latest once so a new release cannot mix the ZIP and checksum.
        for name in ("dist.zip", "dist.zip.sha256"):
            if name not in assets:
                raise ValueError(f"最新 Release 缺少 {name}，请先运行 main 分支的 build-dist")
            download(assets[name], staging / name)

        digest = hashlib.sha256()
        with (staging / "dist.zip").open("rb") as archive_file:
            for chunk in iter(lambda: archive_file.read(1024 * 1024), b""):
                digest.update(chunk)
        checksum = (staging / "dist.zip.sha256").read_text().split()
        if not checksum or digest.hexdigest() != checksum[0]:
            raise ValueError("压缩包 SHA-256 校验失败，未更新网站")

        extracted = staging / "dist"
        with zipfile.ZipFile(staging / "dist.zip") as archive:
            for entry in archive.infolist():
                path = PurePosixPath(entry.filename)
                if (path.is_absolute() or ".." in path.parts or "\\" in entry.filename
                        or ":" in entry.filename or stat.S_ISLNK(entry.external_attr >> 16)):
                    raise ValueError(f"压缩包包含不安全路径：{entry.filename}")
            archive.extractall(extracted)

        index = extracted / "index.html"
        if not index.is_file() or index.stat().st_size == 0:
            raise ValueError("压缩包根目录缺少有效的 index.html，未更新网站")

        files = [path for path in extracted.rglob("*") if path.is_file()]
        # Check all destinations before writing; never follow links into another project.
        for source in files:
            destination = target / source.relative_to(extracted)
            for component in (destination, *destination.parents):
                if component == target.parent:
                    break
                if component.is_symlink():
                    raise ValueError(f"目标路径包含符号链接：{component}")
            if destination.exists() and not destination.is_file():
                raise ValueError(f"目标文件被目录占用：{destination}")
            for parent in destination.parents:
                if parent == target.parent:
                    break
                if parent.exists() and not parent.is_dir():
                    raise ValueError(f"目标目录被文件占用：{parent}")

        # shortcut: retain obsolete assets for open browser tabs; clean them during maintenance.
        # Publish the entry page last, after its assets have been installed.
        files.sort(key=lambda path: path == index)
        target.mkdir(mode=0o755, exist_ok=True)
        target.chmod(0o755)
        for source in files:
            destination = target / source.relative_to(extracted)
            destination.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            for parent in destination.parents:
                if parent == target:
                    break
                parent.chmod(0o755)
            source.chmod(0o644)
            os.replace(source, destination)
        print(f"已更新 {release['tag_name']} → {target}，无需重启 Nginx。")


def main():
    if os.geteuid() != 0:
        raise PermissionError("请使用 root 运行：sudo update-helper")
    import fcntl

    with open("/run/lock/xyzw-helper-update.lock", "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("已有 helper 更新正在运行，请稍后重试") from error
        update(TARGET)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"更新失败：{error}", file=sys.stderr)
        sys.exit(1)
