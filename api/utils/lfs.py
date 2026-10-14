import base64
import hashlib
import logging
import os
import tempfile
import urllib.request
from pathlib import Path

POINTER_HEADER = b"version https://git-lfs.github.com/spec/v1"
POINTER_MAX_SIZE = 1024  # LFS pointers are ~130 bytes; never read real data files


def parse_pointer(path: Path) -> tuple[str, int] | None:
    """Return (oid, size) if the file is a Git LFS pointer, else None."""
    if path.stat().st_size > POINTER_MAX_SIZE:
        return None
    content = path.read_bytes()
    if not content.startswith(POINTER_HEADER):
        return None
    fields = dict(line.split(" ", 1) for line in content.decode().splitlines() if " " in line)
    return fields["oid"].removeprefix("sha256:").strip(), int(fields["size"])


def download_object(url: str, auth: str, path: Path, oid: str, size: int) -> None:
    """Download an LFS object to a temp file, verify it, then atomically replace the pointer."""
    request = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
    sha = hashlib.sha256()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(request, timeout=60) as response:
            while chunk := response.read(1 << 20):
                sha.update(chunk)
                out.write(chunk)
        actual_size = os.path.getsize(tmp)
        if actual_size != size or sha.hexdigest() != oid:
            raise ValueError(f"{path}: checksum/size mismatch (got {actual_size} bytes, expected {size})")
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def resolve_lfs_pointers(data_dir: str, username: str, password: str, server_path: str) -> None:
    """Replace every Git LFS pointer under data_dir with its verified object. Raises on any failure."""
    pointers = [(p, ptr) for p in Path(data_dir).rglob("*") if p.is_file() and (ptr := parse_pointer(p))]
    if not pointers:
        return
    if not (username and password and server_path):
        raise RuntimeError(f"{len(pointers)} LFS pointer(s) in '{data_dir}' but LFS_USERNAME/LFS_PASSWORD/LFS_SERVER_PATH not set")
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    for path, (oid, size) in pointers:
        logging.info(f"Downloading LFS object {oid} ({size} bytes) -> {path}")
        download_object(f"https://{server_path}/object/{oid}", auth, path, oid, size)
