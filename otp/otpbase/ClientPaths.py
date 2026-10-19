"""Keep mutable client files outside a signed, read-only iOS app bundle."""
import os
from pathlib import Path


def client_path(*parts):
    root = Path(os.environ.get('TOONTOWN_USER_DATA', '.')).expanduser()
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)
