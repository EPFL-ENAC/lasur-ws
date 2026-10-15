import hashlib
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from api.utils.lfs import download_object, parse_pointer


def test_lfs_download_verifies_and_keeps_pointer_on_mismatch(tmp_path):
    served = tmp_path / "srv"
    served.mkdir()
    payload = b"parquet bytes" * 1000
    oid = hashlib.sha256(payload).hexdigest()
    (served / oid).write_bytes(payload)
    (served / "bad").write_bytes(b"truncated")

    data = tmp_path / "data"
    data.mkdir()
    pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {len(payload)}\n"
    target = data / "routes.parquet"
    target.write_text(pointer)
    assert parse_pointer(target) == (oid, len(payload))

    server = HTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=served))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with pytest.raises(ValueError):
            download_object(f"{base}/bad", target, oid, len(payload))
        assert target.read_text() == pointer  # failed download leaves pointer untouched
        assert list(data.iterdir()) == [target]  # temp file cleaned up

        download_object(f"{base}/{oid}", target, oid, len(payload))
        assert target.read_bytes() == payload
        assert parse_pointer(target) is None
    finally:
        server.shutdown()
