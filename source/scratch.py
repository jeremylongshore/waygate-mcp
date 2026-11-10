"""Private scratch directories for file tools, separate from shared temp roots."""

import os
import stat
import tempfile
from pathlib import Path


class ScratchDirectory:
    def __init__(self) -> None:
        configured = os.getenv("WAYGATE_SCRATCH_DIR")
        self.temporary: tempfile.TemporaryDirectory[str] | None = None
        if configured is None:
            self.temporary = tempfile.TemporaryDirectory(prefix="waygate-tools-")
            self.path = Path(self.temporary.name)
            return
        path = Path(configured).expanduser()
        if not path.is_absolute() or path.is_symlink():
            raise ValueError(
                "WAYGATE_SCRATCH_DIR must be an absolute non-symlink directory"
            )
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = path.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise ValueError(
                "WAYGATE_SCRATCH_DIR must be owned by this user with mode 0700"
            )
        self.path = path.resolve()
