"""Private storage port and a filesystem adapter for local runs and tests."""

import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Protocol


class ArtifactStorage(Protocol):
    def put(self, data: bytes) -> str: ...
    def get(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class FileArtifactStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, key: str) -> Path:
        if re.fullmatch(r"[0-9a-f]{32}", key) is None:
            raise ValueError("Invalid internal artifact key")
        return self.root / key

    def put(self, data: bytes) -> str:
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        key = uuid.uuid4().hex
        path = self._path(key)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return key

    def get(self, key: str) -> bytes:
        descriptor = os.open(self._path(key), os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, "rb") as stream:
            return stream.read()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
