"""Image normalization helpers for inbound media analysis."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import structlog

logger = structlog.get_logger(__name__)

try:
    from PIL import Image, ImageOps
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]

try:
    import pillow_heif  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    pillow_heif = None  # type: ignore[assignment]

if pillow_heif is not None:
    try:
        pillow_heif.register_heif_opener()
    except Exception:  # pragma: no cover - optional dependency failure
        logger.warning("heif_opener_registration_failed")

PASSTHROUGH_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@dataclass(slots=True)
class NormalizedImage:
    """Normalization output used by media pipeline."""

    ok: bool
    image_bytes: bytes
    mime_type: str
    reason: str = ""
    transformed: bool = False


def normalize_image_for_vision(
    *,
    image_bytes: bytes,
    mime_type: str,
    max_dimension: int,
) -> NormalizedImage:
    """Normalize image format and dimensions for stable vision analysis."""
    safe_mime = mime_type.lower().strip()
    if safe_mime in PASSTHROUGH_MIME_TYPES and Image is None:
        return NormalizedImage(ok=True, image_bytes=image_bytes, mime_type=safe_mime, transformed=False)

    if Image is None or ImageOps is None:
        return NormalizedImage(
            ok=False,
            image_bytes=b"",
            mime_type="",
            reason="IMAGE_NORMALIZER_UNAVAILABLE",
            transformed=False,
        )

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            prepared = ImageOps.exif_transpose(img)
            if max(prepared.size) > max_dimension:
                prepared.thumbnail((max_dimension, max_dimension))

            has_alpha = prepared.mode in {"RGBA", "LA"} or (
                prepared.mode == "P" and "transparency" in prepared.info
            )
            output = BytesIO()
            if has_alpha:
                prepared.save(output, format="PNG", optimize=True)
                return NormalizedImage(
                    ok=True,
                    image_bytes=output.getvalue(),
                    mime_type="image/png",
                    transformed=True,
                )

            prepared = prepared.convert("RGB")
            prepared.save(output, format="JPEG", quality=85, optimize=True)
            return NormalizedImage(
                ok=True,
                image_bytes=output.getvalue(),
                mime_type="image/jpeg",
                transformed=True,
            )
    except Exception as error:
        logger.warning("media_image_normalize_failed", error_type=type(error).__name__)
        return NormalizedImage(
            ok=False,
            image_bytes=b"",
            mime_type="",
            reason="IMAGE_NORMALIZE_FAILED",
            transformed=False,
        )

