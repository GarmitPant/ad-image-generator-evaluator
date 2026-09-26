import io
import warnings
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

from .util import digest

MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 50_000_000
FORMATS = {"PNG", "JPEG", "WEBP"}


def normalize_image(data: bytes, *, reference=True):
    if not data or len(data) > MAX_BYTES:
        raise ValueError("image empty or exceeds 20 MiB")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as raw:
            if raw.format not in FORMATS or raw.width * raw.height > MAX_PIXELS:
                raise ValueError("unsupported format or image exceeds 50 MP")
            if getattr(raw, "n_frames", 1) != 1:
                raise ValueError("animated images are unsupported")
            fmt = raw.format
            raw.load()
            image = ImageOps.exif_transpose(raw)
            alpha = (
                image.convert("RGBA").getchannel("A")
                if image.mode in {"RGBA", "LA"} or "transparency" in image.info
                else None
            )
            profile = image.info.get("icc_profile")
            if profile:
                try:
                    image = ImageCms.profileToProfile(
                        image.convert("RGB") if image.mode in {"RGBA", "P"} else image,
                        ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                        ImageCms.createProfile("sRGB"),
                        outputMode="RGB",
                    )
                except Exception as exc:
                    raise ValueError("invalid or unsupported ICC profile") from exc
            else:
                image = image.convert("RGB")
            if alpha is not None:
                white = Image.new("RGB", image.size, "white")
                white.paste(image, mask=alpha)
                image = white
            original_size = image.size
            if not reference and image.width != image.height:
                raise ValueError("generated image is not square")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            # The converted sRGB profile embeds a creation timestamp; saving it would make the
            # PNG bytes (and every downstream hash, cache key and replay key) nondeterministic.
            image.info.pop("icc_profile", None)
            output = io.BytesIO()
            image.save(output, format="PNG")
            return output.getvalue(), {
                "original_format": fmt,
                "original_size": list(original_size),
                "size": list(image.size),
                "mime_type": "image/png",
                "color_space": "sRGB",
                "alpha_background": "white",
            }


def read_references(paths: list[str], base: Path):
    records = []
    seen = set()
    for declared in paths:
        path = (base / declared).resolve()
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("reference exceeds 20 MiB")
        original = path.read_bytes()
        sha = digest(original)
        if sha in seen:
            raise ValueError("duplicate product reference")
        seen.add(sha)
        rendition, metadata = normalize_image(original)
        records.append(
            {
                "declared_path": declared,
                "original_sha256": sha,
                "original": original,
                "rendition": rendition,
                **metadata,
            }
        )
    return records
