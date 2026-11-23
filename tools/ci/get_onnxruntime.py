"""Download the ONNX Runtime C/C++ package for the CI build into ./onnxruntime-<platform>-<version>/.

Tries the GitHub release archive first. If that fails (the release assets returned "Not Found" on
2026-11-23), it falls back to the official NuGet package Microsoft.ML.OnnxRuntime and lays it out
the same way (include/ and lib/), so the CMake option ONNXRUNTIME_DIR works with either source.

Usage: python tools/ci/get_onnxruntime.py win-x64|linux-x64 [version]
"""
from __future__ import annotations

import io
import shutil
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "tapis-ci"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def from_github(plat: str, ver: str, out: Path) -> None:
    ext = "zip" if plat.startswith("win") else "tgz"
    data = fetch(f"https://github.com/microsoft/onnxruntime/releases/download/v{ver}/onnxruntime-{plat}-{ver}.{ext}")
    if ext == "zip":
        zipfile.ZipFile(io.BytesIO(data)).extractall(".")
    else:
        tarfile.open(fileobj=io.BytesIO(data), mode="r:gz").extractall(".")
    if not (out / "include").is_dir():
        raise RuntimeError("archive has no include/ folder")


def from_nuget(plat: str, ver: str, out: Path) -> None:
    data = fetch(f"https://www.nuget.org/api/v2/package/Microsoft.ML.OnnxRuntime/{ver}")
    z = zipfile.ZipFile(io.BytesIO(data))
    shutil.rmtree(out, ignore_errors=True)
    (out / "include").mkdir(parents=True)
    (out / "lib").mkdir()
    native = f"runtimes/{plat}/native/"
    for name in z.namelist():
        if name.startswith("build/native/include/") and not name.endswith("/"):
            (out / "include" / Path(name).name).write_bytes(z.read(name))
        elif name.startswith(native) and not name.endswith("/"):
            (out / "lib" / Path(name).name).write_bytes(z.read(name))
    so = out / "lib" / "libonnxruntime.so"
    if so.exists():                       # the release archive also has the versioned names
        for alias in ("libonnxruntime.so.1", f"libonnxruntime.so.{ver}"):
            shutil.copyfile(so, out / "lib" / alias)
    if not any((out / "lib").iterdir()) or not (out / "include" / "onnxruntime_cxx_api.h").exists():
        raise RuntimeError(f"NuGet package has no files for {plat}")


def main() -> int:
    plat = sys.argv[1]
    ver = sys.argv[2] if len(sys.argv) > 2 else "1.20.1"
    out = Path(f"onnxruntime-{plat}-{ver}")
    try:
        from_github(plat, ver, out)
        print(f"ONNX Runtime {ver} ({plat}) from the GitHub release")
    except Exception as e:
        print(f"GitHub release download failed ({e}); using NuGet")
        from_nuget(plat, ver, out)
        print(f"ONNX Runtime {ver} ({plat}) from NuGet")
    for f in sorted(out.rglob("*")):
        if f.is_file() and f.parent.name == "lib":
            print("  ", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
