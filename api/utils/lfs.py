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


def download_object(url: str, path: Path, oid: str, size: int) -> None:
    """Download an LFS object to a temp file, verify it, then atomically replace the pointer."""
    sha = hashlib.sha256()
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "wb") as out, urllib.request.urlopen(url, timeout=60) as response:
            while chunk := response.read(1 << 20):
                sha.update(chunk)
                out.write(chunk)
        actual_size = os.path.getsize(tmp)
        if actual_size != size or sha.hexdigest() != oid:
            raise ValueError(f"{path}: checksum/size mismatch (got {actual_size} bytes, expected {size})")
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def resolve_lfs_pointers(data_dir: str, data_url: str) -> None:
    """Replace every Git LFS pointer under data_dir with its verified copy from data_url
    (same relative path, e.g. <data_url>/geneva/routes.parquet). Raises on any failure."""
    root = Path(data_dir)
    for path in list(root.rglob("*")):
        if path.is_file() and (pointer := parse_pointer(path)):
            oid, size = pointer
            url = f"{data_url.rstrip('/')}/{path.relative_to(root).as_posix()}"
            logging.info(f"Downloading {url} ({size} bytes) -> {path}")
            download_object(url, path, oid, size)
