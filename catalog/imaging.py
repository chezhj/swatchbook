"""Shared image handling for uploaded photos.

Phone photos arrive at 4000px+ and several megabytes. Nothing in the UI displays a
photo larger than a few hundred pixels, so downscaling on upload keeps MEDIA_ROOT
manageable without any visible quality cost.
"""

from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def resize_in_place(image_field):
    """Downscale and re-encode the file attached to an ImageField, if it needs it.

    Mutates the field's file. Call before super().save() so the resized bytes are what
    get written to storage. No-op when the image is already small enough.
    """
    if not image_field:
        return

    try:
        image_field.open()
        img = Image.open(image_field)
        img = ImageOps.exif_transpose(img)  # honour phone orientation before we drop EXIF
    except (OSError, ValueError):
        # Not a readable image; let Django's ImageField validation report it instead.
        return

    max_edge = settings.IMAGE_MAX_EDGE
    if max(img.size) <= max_edge and img.format == "JPEG":
        return

    img.thumbnail((max_edge, max_edge), Image.LANCZOS)

    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.convert("RGBA").split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=settings.IMAGE_JPEG_QUALITY, optimize=True)

    name = image_field.name.rsplit("/", 1)[-1].rsplit(".", 1)[0] + ".jpg"
    image_field.save(name, ContentFile(buffer.getvalue()), save=False)
