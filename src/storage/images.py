"""Optimización de imágenes antes de subirlas al almacenamiento."""

import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from src.core.exceptions import BadRequestError

# Lado mayor máximo tras redimensionar: suficiente para la galería en pantallas grandes.
MAX_DIMENSION_PX = 1600
WEBP_QUALITY = 80
WEBP_CONTENT_TYPE = "image/webp"
# Formatos de origen aceptados (según el contenido real del archivo, no su extensión).
_ACCEPTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
# Protección contra "bombas de descompresión": imágenes con dimensiones absurdas.
_MAX_PIXELS = 40_000_000

_INVALID_IMAGE = "El archivo no es una imagen JPG, PNG o WEBP válida"


def optimize_to_webp(content: bytes) -> bytes:
    """Valida la imagen, corrige su orientación, la reduce si es grande y la convierte a WebP."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in _ACCEPTED_FORMATS:
                    raise BadRequestError(
                        _INVALID_IMAGE, f"Unsupported image format {source.format}."
                    )
                if source.width * source.height > _MAX_PIXELS:
                    raise BadRequestError(
                        "La imagen tiene dimensiones demasiado grandes",
                        f"Image has {source.width}x{source.height} pixels.",
                    )
                source.load()
                # Respeta la rotación de las fotos de celular y descarta los metadatos EXIF
                # (pueden incluir la ubicación donde se tomó la foto).
                image = ImageOps.exif_transpose(source)
                has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.thumbnail((MAX_DIMENSION_PX, MAX_DIMENSION_PX), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format="WEBP", quality=WEBP_QUALITY, method=6)
                return output.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombWarning, OSError) as error:
        raise BadRequestError(_INVALID_IMAGE, str(error)) from error
