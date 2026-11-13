import base64
import io
import math

from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Product


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def hex_to_rgb(hex_str):
    """Convert HEX color string (#RRGGBB) to an RGB tuple."""
    hex_str = (hex_str or "").lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(char * 2 for char in hex_str)
    try:
        if len(hex_str) != 6:
            raise ValueError("Invalid HEX color")
        return tuple(int(hex_str[index:index + 2], 16) for index in (0, 2, 4))
    except (TypeError, ValueError):
        return (100, 100, 100)


def rgb_to_hex(rgb):
    """Convert an RGB tuple to a HEX string."""
    return "#{:02x}{:02x}{:02x}".format(*(int(value) for value in rgb)).upper()


def color_distance(rgb1, rgb2):
    """Euclidean distance in weighted RGB space (perceptual approximation)."""
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    rmean = (r1 + r2) / 2
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    return math.sqrt(
        (2 + rmean / 256) * (dr ** 2)
        + 4 * (dg ** 2)
        + (2 + (255 - rmean) / 256) * (db ** 2)
    )


def detect_dominant_colors(pil_image, count=3):
    """Resize a validated image and extract its dominant colors."""
    image = pil_image.convert("RGB")
    image.thumbnail((100, 100))
    quantized = image.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:count * 3]
    return [
        (palette[index], palette[index + 1], palette[index + 2])
        for index in range(0, len(palette), 3)
    ]


def get_color_family_name(rgb):
    """Return a descriptive human name for an RGB color."""
    red, green, blue = rgb
    maximum, minimum = max(rgb), min(rgb)
    luminance = (maximum + minimum) / 2

    if luminance < 35:
        return "Midnight Black / Deep Slate"
    if luminance > 230 and (maximum - minimum) < 20:
        return "Ivory / Porcelain White"
    if (maximum - minimum) < 25:
        return "Nude / Neutral Slate"
    if red > 160 and green < 100 and blue < 120:
        return "Crimson Red / Ruby"
    if red > 180 and green > 100 and blue < 100:
        return "Warm Amber / Terracotta"
    if red > 180 and blue > 140 and green < 140:
        return "Blush Rose / Berry"
    if green > 130 and green > red and green > blue:
        return "Sage Green / Botanical"
    if blue > 140 and blue > red:
        return "Ocean Azure / Sapphire"
    if red > 160 and green > 160 and blue < 120:
        return "Champagne / Warm Gold"
    return "Luxe Hue"


def _read_image_bytes(image_file_or_data):
    if isinstance(image_file_or_data, str):
        if not image_file_or_data.startswith("data:image/") or ";base64," not in image_file_or_data:
            raise ValueError("Unsupported image input.")
        header, encoded = image_file_or_data.split(";base64,", 1)
        mime_type = header[5:].lower()
        if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValueError("Only JPEG, PNG, and WEBP images are supported.")
        image_data = base64.b64decode(encoded, validate=True)
    elif hasattr(image_file_or_data, "read"):
        image_data = image_file_or_data.read(MAX_IMAGE_BYTES + 1)
    else:
        raise ValueError("Unsupported image input.")

    if not image_data:
        raise ValueError("The uploaded image is empty.")
    if len(image_data) > MAX_IMAGE_BYTES:
        raise ValueError("Image is larger than 10MB.")
    return image_data


def _load_validated_image(image_data):
    with Image.open(io.BytesIO(image_data)) as source:
        if source.format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError("Only JPEG, PNG, and WEBP images are supported.")
        width, height = source.size
        if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
            raise ValueError("Image dimensions are too large.")
        source.verify()

    with Image.open(io.BytesIO(image_data)) as source:
        if source.format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError("Unsupported image format.")
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1000, 1000))
        return image.copy()


def search_similar_products(image_file_or_data, department_filter=None, limit=8):
    """Match a validated user image against the catalog's dominant colors."""
    try:
        image_data = _read_image_bytes(image_file_or_data)
        pil_image = _load_validated_image(image_data)
        dominant_rgbs = detect_dominant_colors(pil_image, count=3)
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        return {
            "error": "The image could not be processed. Use a valid JPEG, PNG, or WEBP image under 10MB.",
            "dominant_hex": "#E11D48",
            "color_name": "Velvet Rose",
            "palette": ["#E11D48", "#FDA4AF", "#1E293B"],
            "matches": [],
        }

    primary_rgb = dominant_rgbs[0] if dominant_rgbs else (180, 50, 80)
    primary_hex = rgb_to_hex(primary_rgb)
    color_name = get_color_family_name(primary_rgb)
    palette_hexes = [rgb_to_hex(color) for color in dominant_rgbs]

    products = Product.objects.select_related(
        "department", "category", "brand"
    ).prefetch_related("variants")
    if department_filter:
        products = products.filter(department__slug=department_filter)

    scored_products = []
    max_dist = 765.0
    for product in products:
        product_rgb = hex_to_rgb(product.dominant_color_hex)
        distance = color_distance(primary_rgb, product_rgb)
        color_similarity = max(0.0, 1.0 - (distance / max_dist))

        palette_bonus = sum(
            0.08 for palette_rgb in dominant_rgbs[1:]
            if color_distance(palette_rgb, product_rgb) < 150
        )
        tags = (product.visual_tags or "").lower()
        color_name_lower = color_name.lower()
        tag_bonus = 0.0
        tag_groups = (
            (("red",), ("red", "ruby", "crimson")),
            (("rose",), ("rose", "pink", "blush")),
            (("black",), ("black", "slate", "dark")),
            (("gold",), ("gold", "champagne", "amber")),
            (("green",), ("green", "botanical", "sage")),
        )
        for triggers, keywords in tag_groups:
            if any(trigger in color_name_lower for trigger in triggers) and any(keyword in tags for keyword in keywords):
                tag_bonus = 0.12
                break

        final_score = min(0.98, max(0.60, color_similarity * 0.70 + palette_bonus + tag_bonus + 0.15))
        percent_score = int(round(final_score * 100))
        scored_products.append({
            "product": product,
            "match_score": percent_score,
            "match_label": f"{percent_score}% Visual Match",
            "distance": distance,
        })

    scored_products.sort(key=lambda item: item["match_score"], reverse=True)
    return {
        "dominant_hex": primary_hex,
        "color_name": color_name,
        "palette": palette_hexes,
        "matches": scored_products[:max(1, min(int(limit), 24))],
    }
