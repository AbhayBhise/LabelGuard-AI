"""Object storage wrapper (MinIO / S3) with local-filesystem fallback.

When MinIO is unreachable, files are stored under ./storage to keep the app
functional for demos without external services.
"""
import os
import uuid
from pathlib import Path

from app.config import get_settings

settings = get_settings()

# Try to connect to MinIO lazily; fall back to local disk.
try:
    from minio import Minio  # type: ignore

    _client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    _minio_ready = False
except Exception:
    _client = None
    _minio_ready = False


_LOCAL_ROOT = Path("storage")


def _ensure_local(name: str) -> Path:
    _LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    return _LOCAL_ROOT / name


def _ensure_bucket():
    global _minio_ready
    if _minio_ready or _client is None:
        return
    try:
        found = _client.bucket_exists(settings.MINIO_BUCKET)
        if not found:
            _client.make_bucket(settings.MINIO_BUCKET)
        _minio_ready = True
    except Exception:
        _minio_ready = False


def put_file(data: bytes, content_type: str = "application/octet-stream") -> str:
    """Store a file, return its public URL/path."""
    _ensure_bucket()
    key = f"{uuid.uuid4().hex}/{uuid.uuid4().hex}"
    if _minio_ready:
        try:
            _client.put_object(
                settings.MINIO_BUCKET,
                key,
                data,
                length=len(data),
                content_type=content_type,
            )
            return f"/{settings.MINIO_BUCKET}/{key}"
        except Exception:
            pass
    # local fallback
    name = f"{key.split('/')[0]}.bin"
    _ensure_local(name).write_bytes(data)
    return f"/storage/{name}"


def get_file(identifier: str) -> bytes:
    if _minio_ready and identifier.startswith("/" + settings.MINIO_BUCKET):
        key = identifier[len(settings.MINIO_BUCKET) + 2 :]
        try:
            resp = _client.get_object(settings.MINIO_BUCKET, key)
            return resp.read()
        except Exception:
            pass
    path = _LOCAL_ROOT / Path(identifier).name
    if path.exists():
        return path.read_bytes()
    return b""
