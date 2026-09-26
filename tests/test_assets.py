import io

import pytest
from PIL import Image

from adgen.assets import normalize_image, read_references


def encoded(image, fmt="PNG", **kwargs):
    output = io.BytesIO()
    image.save(output, format=fmt, **kwargs)
    return output.getvalue()


def test_orientation_normalization_and_no_upscale():
    image = Image.new("RGB", (40, 80), "red")
    exif = Image.Exif()
    exif[274] = 6
    data, meta = normalize_image(encoded(image, "JPEG", exif=exif))
    assert meta["size"] == [80, 40]
    assert Image.open(io.BytesIO(data)).getexif().get(274) is None


def test_large_reference_supported_and_rendition_bounded():
    data, meta = normalize_image(encoded(Image.new("RGB", (5304, 7952), "red"), "JPEG"))
    assert max(meta["size"]) == 1024
    assert Image.open(io.BytesIO(data)).mode == "RGB"


def test_alpha_composited_over_white():
    data, _ = normalize_image(encoded(Image.new("RGBA", (20, 20), (0, 0, 0, 0))))
    assert Image.open(io.BytesIO(data)).getpixel((0, 0)) == (255, 255, 255)


def test_reject_animation_corrupt_non_square():
    image = Image.new("RGB", (20, 20), "red")
    other = Image.new("RGB", (20, 20), "blue")
    with pytest.raises(ValueError, match="animated"):
        normalize_image(encoded(image, save_all=True, append_images=[other], duration=100))
    with pytest.raises(Exception):
        normalize_image(b"not an image")
    with pytest.raises(ValueError, match="square"):
        normalize_image(encoded(Image.new("RGB", (20, 30))), reference=False)


def test_duplicate_reference_rejected(tmp_path):
    (tmp_path / "a.png").write_bytes(encoded(Image.new("RGB", (20, 20))))
    with pytest.raises(ValueError, match="duplicate"):
        read_references(["a.png", "a.png"], tmp_path)


def test_icc_profile_preserves_alpha_compositing():
    from PIL import ImageCms

    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    data, _ = normalize_image(
        encoded(Image.new("RGBA", (20, 20), (0, 0, 0, 0)), icc_profile=profile)
    )
    assert Image.open(io.BytesIO(data)).getpixel((0, 0)) == (255, 255, 255)


def test_icc_tagged_reference_normalizes_deterministically(monkeypatch):
    # LittleCMS stamps the converted sRGB profile with the current time; if that profile were
    # embedded, identical references would hash differently and break caching and replay.
    from PIL import ImageCms

    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    data = encoded(Image.new("RGB", (64, 48), (200, 30, 30)), "JPEG", icc_profile=profile)
    first, _ = normalize_image(data)
    monkeypatch.setattr("time.time", lambda: 4_102_444_800.0)  # a different creation second
    second, _ = normalize_image(data)
    assert first == second
    assert "icc_profile" not in Image.open(io.BytesIO(first)).info
