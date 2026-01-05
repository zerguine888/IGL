from pathlib import Path
from typing import Union


def read_file(file_path: Union[str, Path]) -> str:
    """Return the text contents of `file_path` using UTF-8 encoding."""
    p = Path(file_path)
    with p.open("r", encoding="utf-8") as f:
        return f.read()


def write_file(file_path: Union[str, Path], content: str) -> None:
    """Write `content` to `file_path`, creating parent directories if needed.

    The file is written using UTF-8 encoding and any existing file is overwritten.
    """
    p = Path(file_path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        f.write(content)
