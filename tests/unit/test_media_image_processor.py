"""Unit tests for media image normalization helpers."""

from velox.core import media_image_processor


def test_jpeg_passthrough_when_pil_unavailable() -> None:
    """JPEG should pass through when PIL dependency is unavailable."""
    if media_image_processor.Image is not None:
        return
    payload = b"\xff\xd8\xff\xdbfakejpeg"
    result = media_image_processor.normalize_image_for_vision(
        image_bytes=payload,
        mime_type="image/jpeg",
        max_dimension=2048,
    )
    assert result.ok is True
    assert result.image_bytes == payload
    assert result.mime_type == "image/jpeg"
    assert result.transformed is False


def test_webp_fails_when_normalizer_unavailable() -> None:
    """WEBP should fail safely when optional image dependencies are missing."""
    if media_image_processor.Image is not None:
        return
    result = media_image_processor.normalize_image_for_vision(
        image_bytes=b"not-an-image",
        mime_type="image/webp",
        max_dimension=2048,
    )
    assert result.ok is False
    assert result.reason == "IMAGE_NORMALIZER_UNAVAILABLE"
