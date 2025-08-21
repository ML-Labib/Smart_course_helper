from pathlib import Path
from uuid import uuid4
from typing import Iterable

from fastapi import UploadFile, HTTPException

# Points to the "app" directory
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"


def _ensure_upload_dir(subdir: str) -> Path:
    target = UPLOAD_DIR / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


async def save_upload(
    file: UploadFile,
    subdir: str,
    allowed_types: Iterable[str] = ("image/jpeg", "image/png", "image/webp"),
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
) -> str:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    data = await file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB).")

    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }
    ext = ext_map.get(file.content_type) or (Path(file.filename).suffix or ".bin")

    folder = _ensure_upload_dir(subdir)
    name = f"{uuid4().hex}{ext}"
    path = folder / name

    with open(path, "wb") as f:
        f.write(data)

    # Return the URL clients can use
    return f"/static/uploads/{subdir}/{name}"