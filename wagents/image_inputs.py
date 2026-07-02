"""Image input optimization for model-bound harness payloads."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import secrets
import stat
import sys
from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from wagents import ROOT

CONFIG_PATH = ROOT / "config" / "image-input-optimizer.json"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "wagents" / "image-inputs"
DEFAULT_PROFILE = "general"
ALLOWED_SYMLINK_COMPONENTS = {
    Path("/private/tmp"),
    Path("/private/var"),
    Path("/tmp"),
    Path("/var"),
}
PROFILE_ALIASES = {
    "auto": "auto",
    "general": "general",
    "photo": "general",
    "screenshot": "screenshot-text",
    "text": "screenshot-text",
    "ocr": "screenshot-text",
    "transparent": "transparent",
    "thumbnail": "thumbnail",
}


class ImageOptimizationError(RuntimeError):
    """Raised when an image cannot be safely optimized."""


@dataclass(frozen=True)
class ImageInputResult:
    status: str
    profile: str
    source_path: str
    optimized_path: str | None
    source_bytes: int
    optimized_bytes: int | None
    source_width: int
    source_height: int
    optimized_width: int | None
    optimized_height: int | None
    source_format: str
    optimized_format: str | None
    changed: bool
    fits: bool
    cache_key: str | None
    reason: str

    def to_json(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "profile": self.profile,
            "sourcePath": self.source_path,
            "optimizedPath": self.optimized_path,
            "sourceBytes": self.source_bytes,
            "optimizedBytes": self.optimized_bytes,
            "sourceWidth": self.source_width,
            "sourceHeight": self.source_height,
            "optimizedWidth": self.optimized_width,
            "optimizedHeight": self.optimized_height,
            "sourceFormat": self.source_format,
            "optimizedFormat": self.optimized_format,
            "changed": self.changed,
            "fits": self.fits,
            "cacheKey": self.cache_key,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class SourceIdentity:
    device: int
    inode: int
    size: int
    mtime_ns: int

    @classmethod
    def from_json(cls, value: Any) -> SourceIdentity | None:
        if not isinstance(value, dict):
            return None
        try:
            return cls(
                device=int(value["device"]),
                inode=int(value["inode"]),
                size=int(value["size"]),
                mtime_ns=int(value["mtimeNs"]),
            )
        except (KeyError, TypeError, ValueError):
            return None


def _default_image_optimizer_config() -> dict[str, Any]:
    return {
            "version": 1,
            "cache_dir": str(DEFAULT_CACHE_DIR),
            "default_profile": DEFAULT_PROFILE,
            "profiles": {
                "general": {
                    "max_long_edge": 2000,
                    "max_pixels": 4000000,
                    "max_bytes": 4500000,
                    "quality_steps": [90, 85, 80, 75, 70],
                    "output_format": "jpeg",
                },
                "screenshot-text": {
                    "max_long_edge": 3000,
                    "max_pixels": 8000000,
                    "max_bytes": 4500000,
                    "quality_steps": [95, 90, 85, 80, 75],
                    "output_format": "jpeg",
                },
                "transparent": {
                    "max_long_edge": 3000,
                    "max_pixels": 8000000,
                    "max_bytes": 4500000,
                    "quality_steps": [95, 90, 85, 80, 75],
                    "output_format": "png",
                },
            },
            "profile_detection": {
                "screenshot_text_patterns": [
                    "screenshot",
                    "screen",
                    "ui",
                    "ocr",
                    "receipt",
                    "chart",
                    "diagram",
                    "code",
                ],
            },
        }


@lru_cache(maxsize=4)
def _load_image_optimizer_config_cached(cache_key: tuple[str, int, int]) -> dict[str, Any]:
    path = Path(cache_key[0])
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _default_image_optimizer_config()


def load_image_optimizer_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or CONFIG_PATH
    if not config_path.is_file():
        return _default_image_optimizer_config()
    return _load_image_optimizer_config_cached(
        (str(config_path.resolve()), config_path.stat().st_mtime_ns, config_path.stat().st_size)
    )


def _load_pillow():
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise ImageOptimizationError("Pillow is required for image optimization. Run `uv sync`.") from exc
    return Image, ImageOps, UnidentifiedImageError


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_identity(path: Path) -> SourceIdentity:
    try:
        file_stat = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ImageOptimizationError(f"Unable to inspect image input: {path}") from exc
    if not stat.S_ISREG(file_stat.st_mode):
        raise ImageOptimizationError(f"Image input is not a regular file: {path}")
    return SourceIdentity(
        device=int(file_stat.st_dev),
        inode=int(file_stat.st_ino),
        size=int(file_stat.st_size),
        mtime_ns=int(file_stat.st_mtime_ns),
    )


def _assert_source_identity(path: Path, expected: SourceIdentity) -> None:
    if _source_identity(path) != expected:
        raise ImageOptimizationError(f"Image input changed while it was being optimized: {path}")


def _has_alpha(image: Any) -> bool:
    if image.mode in {"RGBA", "LA"}:
        return True
    return image.mode == "P" and "transparency" in image.info


def _select_profile(config: dict[str, Any], requested: str, image: Any, source_path: Path, context: str) -> str:
    requested = PROFILE_ALIASES.get(requested, requested)
    profiles = config.get("profiles", {})
    if requested != "auto":
        if requested not in profiles:
            raise ImageOptimizationError(f"Unknown image optimization profile: {requested}")
        return requested
    if _has_alpha(image) and "transparent" in profiles:
        return "transparent"
    detection = config.get("profile_detection", {})
    haystack = f"{source_path.name} {context}".lower()
    for pattern in detection.get("screenshot_text_patterns", []):
        if str(pattern).lower() in haystack and "screenshot-text" in profiles:
            return "screenshot-text"
    return str(config.get("default_profile") or DEFAULT_PROFILE)


def _profile(config: dict[str, Any], profile_id: str, max_bytes: int | None) -> dict[str, Any]:
    profiles = config.get("profiles", {})
    if profile_id not in profiles:
        raise ImageOptimizationError(f"Missing image optimization profile: {profile_id}")
    profile = dict(profiles[profile_id])
    if max_bytes is not None:
        profile["max_bytes"] = max_bytes
    return profile


def _target_size(width: int, height: int, max_long_edge: int, max_pixels: int) -> tuple[int, int]:
    scale = 1.0
    long_edge = max(width, height)
    if long_edge > max_long_edge:
        scale = min(scale, max_long_edge / long_edge)
    pixels = width * height
    if pixels * scale * scale > max_pixels:
        scale = min(scale, math.sqrt(max_pixels / pixels))
    if scale >= 1:
        return width, height
    return max(1, int(width * scale)), max(1, int(height * scale))


def _format_for_profile(profile: dict[str, Any], has_alpha: bool) -> str:
    if has_alpha:
        return "PNG"
    output_format = str(profile.get("output_format") or "jpeg").upper()
    if output_format == "JPG":
        output_format = "JPEG"
    return output_format if output_format in {"JPEG", "PNG"} else "JPEG"


def _extension_for_format(output_format: str) -> str:
    return ".jpg" if output_format == "JPEG" else ".png"


def _prepare_for_save(image: Any, output_format: str) -> Any:
    if output_format == "PNG":
        return image
    if image.mode == "RGB":
        return image
    if _has_alpha(image):
        Image = _load_pillow()[0]
        background = Image.new("RGB", image.size, (255, 255, 255))
        alpha = image.getchannel("A") if "A" in image.getbands() else None
        background.paste(image.convert("RGBA"), mask=alpha)
        return background
    return image.convert("RGB")


def _save_bytes(image: Any, output_format: str, quality: int | None = None) -> bytes:
    buffer = BytesIO()
    prepared = _prepare_for_save(image, output_format)
    if output_format == "JPEG":
        prepared.save(buffer, format="JPEG", quality=quality or 85, optimize=True, progressive=True)
    else:
        prepared.save(buffer, format="PNG", optimize=True, compress_level=9)
    return buffer.getvalue()


def _resize(image: Any, size: tuple[int, int]) -> Any:
    if image.size == size:
        return image.copy()
    Image = _load_pillow()[0]
    resampling = getattr(Image, "Resampling", None)
    filter_value = resampling.LANCZOS if resampling is not None else 1
    return image.resize(size, filter_value)


def _is_allowed_system_symlink(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        return False
    return path in ALLOWED_SYMLINK_COMPONENTS or resolved in ALLOWED_SYMLINK_COMPONENTS


def _assert_no_symlink_components(path: Path, *, label: str = "image path") -> None:
    current = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts[1:] if path.is_absolute() else path.parts:
        current = current / part
        try:
            if current.is_symlink() and not _is_allowed_system_symlink(current):
                raise ImageOptimizationError(f"Unsafe symlink in {label}: {current}")
        except OSError as exc:
            raise ImageOptimizationError(f"Unable to inspect {label}: {current}") from exc


def _ensure_private_cache_dir(path: Path) -> Path:
    path = path.expanduser()
    existing_parent = path
    while not existing_parent.exists() and existing_parent != existing_parent.parent:
        existing_parent = existing_parent.parent
    _assert_no_symlink_components(existing_parent, label="image cache path")
    path.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(path, label="image cache path")
    if not path.is_dir():
        raise ImageOptimizationError(f"Image cache path is not a directory: {path}")
    path.chmod(0o700)
    return path


def _path_inside(path: Path, root: Path) -> bool:
    try:
        return path == root or root in path.parents
    except RuntimeError:
        return False


def _validate_cache_file(path: Path, cache_root: Path) -> None:
    _assert_no_symlink_components(path, label="image cache path")
    try:
        resolved_path = path.resolve(strict=True)
        resolved_root = cache_root.resolve(strict=True)
    except OSError as exc:
        raise ImageOptimizationError(f"Unable to inspect optimized image cache path: {path}") from exc
    if not _path_inside(resolved_path, resolved_root):
        raise ImageOptimizationError(f"Optimized image cache path escapes cache root: {path}")
    try:
        file_stat = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ImageOptimizationError(f"Unable to inspect optimized image cache file: {path}") from exc
    if not stat.S_ISREG(file_stat.st_mode):
        raise ImageOptimizationError(f"Optimized image cache path is not a regular file: {path}")
    if file_stat.st_mode & 0o077:
        path.chmod(0o600)


def _write_atomic(path: Path, data: bytes, cache_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_components(path.parent, label="image cache path")
    try:
        resolved_parent = path.parent.resolve(strict=True)
        resolved_root = cache_root.resolve(strict=True)
    except OSError as exc:
        raise ImageOptimizationError(f"Unable to inspect optimized image cache parent: {path.parent}") from exc
    if not _path_inside(resolved_parent, resolved_root):
        raise ImageOptimizationError(f"Optimized image cache parent escapes cache root: {path.parent}")
    path.parent.chmod(0o700)
    if path.is_symlink():
        raise ImageOptimizationError(f"Refusing to write optimized image through symlink: {path}")

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(8)}.tmp")
    try:
        fd = os.open(tmp, flags, 0o600)
    except OSError as exc:
        raise ImageOptimizationError(f"Unable to create private optimized image temp file: {tmp}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        try:
            os.link(tmp, path)
            _validate_cache_file(path, cache_root)
        except FileExistsError:
            _validate_cache_file(path, cache_root)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise ImageOptimizationError(f"Unable to commit optimized image cache file: {path}") from exc
            _validate_cache_file(path, cache_root)
    finally:
        with suppress(FileNotFoundError):
            tmp.unlink()


def _cache_root(config: dict[str, Any], override: Path | None) -> Path:
    if override is not None:
        return override.expanduser()
    raw = str(config.get("cache_dir") or DEFAULT_CACHE_DIR)
    return Path(raw).expanduser()


def _prepared_cache_root(config: dict[str, Any], override: Path | None) -> Path:
    return _ensure_private_cache_dir(_cache_root(config, override))


def _cache_key(file_digest: str, profile_id: str, profile: dict[str, Any], output_format: str) -> str:
    material = {
        "file_digest": file_digest,
        "profile": profile_id,
        "profile_config": profile,
        "output_format": output_format,
    }
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()


def _read_image_size(path: Path) -> tuple[int, int]:
    Image = _load_pillow()[0]
    with Image.open(path) as image:
        return image.size


def optimize_image_path(
    source_path: Path | str,
    *,
    profile: str = "auto",
    context: str = "",
    config_path: Path | None = None,
    cache_dir: Path | None = None,
    check_only: bool = False,
    max_bytes: int | None = None,
    expected_identity: SourceIdentity | dict[str, Any] | None = None,
) -> ImageInputResult:
    """Resize and transcode a model-bound image into a cache path when needed."""

    path = Path(source_path).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    _assert_no_symlink_components(path, label="image source path")
    try:
        path = path.resolve(strict=True)
    except OSError as exc:
        raise ImageOptimizationError(f"Image input does not exist or is not a file: {path}") from exc
    if not path.is_file():
        raise ImageOptimizationError(f"Image input does not exist or is not a file: {path}")
    source_identity = _source_identity(path)
    expected = (
        expected_identity
        if isinstance(expected_identity, SourceIdentity)
        else SourceIdentity.from_json(expected_identity)
    )
    if expected is not None and source_identity != expected:
        raise ImageOptimizationError(f"Image input changed before optimization could start: {path}")

    Image, ImageOps, UnidentifiedImageError = _load_pillow()
    Image.MAX_IMAGE_PIXELS = max(Image.MAX_IMAGE_PIXELS or 0, 60000000)
    config = load_image_optimizer_config(config_path)
    source_bytes = source_identity.size

    try:
        with Image.open(path) as opened:
            source_format = str(opened.format or path.suffix.lstrip(".") or "unknown").upper()
            image = ImageOps.exif_transpose(opened)
            image.load()
    except UnidentifiedImageError as exc:
        raise ImageOptimizationError(f"Unsupported or unreadable image input: {path}") from exc
    _assert_source_identity(path, source_identity)

    profile_id = _select_profile(config, profile, image, path, context)
    selected = _profile(config, profile_id, max_bytes)
    limit_bytes = int(selected["max_bytes"])
    max_long_edge = int(selected["max_long_edge"])
    max_pixels = int(selected["max_pixels"])
    target = _target_size(image.width, image.height, max_long_edge, max_pixels)
    output_format = _format_for_profile(selected, _has_alpha(image))
    acceptable_source_formats = {"JPEG", "JPG", "PNG", "WEBP"}
    needs_change = (
        source_bytes > limit_bytes
        or target != image.size
        or source_format not in acceptable_source_formats
    )

    if not needs_change:
        return ImageInputResult(
            status="ok",
            profile=profile_id,
            source_path=str(path),
            optimized_path=str(path),
            source_bytes=source_bytes,
            optimized_bytes=source_bytes,
            source_width=image.width,
            source_height=image.height,
            optimized_width=image.width,
            optimized_height=image.height,
            source_format=source_format,
            optimized_format=source_format,
            changed=False,
            fits=True,
            cache_key=None,
            reason="source image already fits input profile",
        )

    if check_only:
        return ImageInputResult(
            status="would-optimize",
            profile=profile_id,
            source_path=str(path),
            optimized_path=None,
            source_bytes=source_bytes,
            optimized_bytes=None,
            source_width=image.width,
            source_height=image.height,
            optimized_width=target[0],
            optimized_height=target[1],
            source_format=source_format,
            optimized_format=output_format,
            changed=True,
            fits=False,
            cache_key=None,
            reason="source image exceeds input profile",
        )

    cache_root = _prepared_cache_root(config, cache_dir)
    file_digest = _sha256_file(path)
    _assert_source_identity(path, source_identity)
    key = _cache_key(file_digest, profile_id, selected, output_format)
    optimized_path = cache_root / key[:2] / f"{key}{_extension_for_format(output_format)}"
    if optimized_path.exists() or optimized_path.is_symlink():
        _validate_cache_file(optimized_path, cache_root)
        width, height = _read_image_size(optimized_path)
        optimized_bytes = optimized_path.stat().st_size
        return ImageInputResult(
            status="optimized",
            profile=profile_id,
            source_path=str(path),
            optimized_path=str(optimized_path),
            source_bytes=source_bytes,
            optimized_bytes=optimized_bytes,
            source_width=image.width,
            source_height=image.height,
            optimized_width=width,
            optimized_height=height,
            source_format=source_format,
            optimized_format=output_format,
            changed=True,
            fits=optimized_bytes <= limit_bytes,
            cache_key=key,
            reason="cached optimized image",
        )

    quality_steps = [int(step) for step in selected.get("quality_steps", [90, 85, 80, 75, 70])]
    current_size = target
    best: tuple[bytes, tuple[int, int], bool] | None = None
    for attempt in range(8):
        resized = _resize(image, current_size)
        candidates: list[tuple[bytes, tuple[int, int], bool]] = []
        if output_format == "JPEG":
            for quality in quality_steps:
                data = _save_bytes(resized, output_format, quality)
                candidates.append((data, current_size, len(data) <= limit_bytes))
                if len(data) <= limit_bytes:
                    break
        else:
            data = _save_bytes(resized, output_format)
            candidates.append((data, current_size, len(data) <= limit_bytes))
        fit = next((candidate for candidate in candidates if candidate[2]), None)
        if fit is not None:
            best = fit
            break
        smallest = min(candidates, key=lambda candidate: len(candidate[0]))
        if best is None or len(smallest[0]) < len(best[0]):
            best = smallest
        if attempt == 7:
            break
        current_size = max(1, int(current_size[0] * 0.85)), max(1, int(current_size[1] * 0.85))

    if best is None:
        raise ImageOptimizationError(f"Unable to generate optimized image for {path}")

    data, optimized_size, fits = best
    _write_atomic(optimized_path, data, cache_root)
    return ImageInputResult(
        status="optimized",
        profile=profile_id,
        source_path=str(path),
        optimized_path=str(optimized_path),
        source_bytes=source_bytes,
        optimized_bytes=len(data),
        source_width=image.width,
        source_height=image.height,
        optimized_width=optimized_size[0],
        optimized_height=optimized_size[1],
        source_format=source_format,
        optimized_format=output_format,
        changed=True,
        fits=fits,
        cache_key=key,
        reason="optimized image written to cache",
    )


def optimize_image_batch(payload: dict[str, Any]) -> dict[str, Any]:
    images = payload.get("images")
    if not isinstance(images, list) or not images:
        raise ImageOptimizationError("Batch optimizer payload must include a non-empty images list.")
    results: list[dict[str, Any]] = []
    for item in images:
        if not isinstance(item, dict):
            raise ImageOptimizationError("Batch optimizer image entries must be objects.")
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ImageOptimizationError("Batch optimizer image entry missing path.")
        result = optimize_image_path(
            raw_path,
            profile=str(item.get("profile") or payload.get("profile") or "auto"),
            context=str(item.get("context") or ""),
            config_path=Path(payload["config"]) if payload.get("config") else None,
            cache_dir=Path(payload["cache_dir"]) if payload.get("cache_dir") else None,
            check_only=bool(item.get("check_only") or payload.get("check_only")),
            max_bytes=int(item["max_bytes"]) if item.get("max_bytes") is not None else None,
            expected_identity=SourceIdentity.from_json(item.get("identity")),
        )
        results.append(result.to_json())
    return {"status": "ok", "results": results}


def optimize_image_batch_inprocess(payload: dict[str, Any]) -> dict[str, Any]:
    """Run batch image optimization in-process (same contract as ``optimize_image_batch``)."""
    return optimize_image_batch(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optimize a model-bound image input.")
    parser.add_argument("image", nargs="?")
    parser.add_argument("--profile", default="auto")
    parser.add_argument("--context", default="")
    parser.add_argument("--config")
    parser.add_argument("--cache-dir")
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--batch-json-stdin", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.batch_json_stdin:
            payload = json.loads(sys.stdin.read() or "{}")
            output = optimize_image_batch(payload)
            json.dump(output, sys.stdout, separators=(",", ":"))
            print()
            return 0
        if not args.image:
            raise ImageOptimizationError("Image path is required unless --batch-json-stdin is used.")
        result = optimize_image_path(
            args.image,
            profile=args.profile,
            context=args.context,
            config_path=Path(args.config) if args.config else None,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None,
            check_only=args.check_only,
            max_bytes=args.max_bytes,
        )
    except ImageOptimizationError as exc:
        json.dump({"status": "error", "message": str(exc)}, sys.stderr, separators=(",", ":"))
        print(file=sys.stderr)
        return 2

    json.dump(result.to_json(), sys.stdout, separators=(",", ":"))
    print()
    return 0 if result.fits or result.status == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
