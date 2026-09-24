import io
import math
import base64
from PIL import Image
from django.core.files.base import ContentFile
from .models import Product


def hex_to_rgb(hex_str):
    """Convert HEX color string (#RRGGBB) to (r, g, b) tuple."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c * 2 for c in hex_str])
    try:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        return (100, 100, 100)


def rgb_to_hex(rgb):
    """Convert (r, g, b) tuple to HEX string."""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2])).upper()


def color_distance(rgb1, rgb2):
    """Euclidean distance in weighted RGB space (perceptual approximation)."""
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    # Standard perceptual weights: Red 0.3, Green 0.59, Blue 0.11
    rmean = (r1 + r2) / 2
    dr = r1 - r2
    dg = g1 - g2
    db = b1 - b2
    return math.sqrt((2 + rmean / 256) * (dr ** 2) + 4 * (dg ** 2) + (2 + (255 - rmean) / 256) * (db ** 2))


def detect_dominant_colors(pil_image, count=3):
    """Resize image and extract top dominant colors."""
    img = pil_image.convert('RGB')
    # Resize down for speed
    img = img.resize((100, 100))
    # Quantize to find dominant colors
    quantized = img.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:count * 3]
    
    colors = []
    for i in range(0, len(palette), 3):
        rgb = (palette[i], palette[i+1], palette[i+2])
        colors.append(rgb)
    return colors


def get_color_family_name(rgb):
    """Return a descriptive human name for a given RGB."""
    r, g, b = rgb
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    lum = (max_c + min_c) / 2

    if lum < 35:
        return "Midnight Black / Deep Slate"
    if lum > 230 and (max_c - min_c) < 20:
        return "Ivory / Porcelain White"
    if (max_c - min_c) < 25:
        return "Nude / Neutral Slate"

    if r > 160 and g < 100 and b < 120:
        return "Crimson Red / Ruby"
    if r > 180 and g > 100 and b < 100:
        return "Warm Amber / Terracotta"
    if r > 180 and b > 140 and g < 140:
        return "Blush Rose / Berry"
    if g > 130 and g > r and g > b:
        return "Sage Green / Botanical"
    if b > 140 and b > r:
        return "Ocean Azure / Sapphire"
    if r > 160 and g > 160 and b < 120:
        return "Champagne / Warm Gold"
    return "Luxe Hue"


def search_similar_products(image_file_or_data, department_filter=None, limit=8):
    """
    Given an image (UploadedFile or base64 dataURI), extract visual color profiles
    and match against products in the catalog.
    Returns:
        {
            'dominant_hex': str,
            'color_name': str,
            'palette': list of hex colors,
            'matches': list of (Product, match_percentage, reason)
        }
    """
    try:
        if isinstance(image_file_or_data, str) and (image_file_or_data.startswith('data:image') or ';base64,' in image_file_or_data):
            # Parse data URI and enforce the same 10MB application limit used for uploads.
            header, encoded = image_file_or_data.split(';base64,', 1)
            image_data = base64.b64decode(encoded, validate=True)
            if len(image_data) > 10 * 1024 * 1024:
                raise ValueError('Image is larger than 10MB.')
            pil_image = Image.open(io.BytesIO(image_data))
        elif hasattr(image_file_or_data, 'read'):
            image_data = image_file_or_data.read()
            if len(image_data) > 10 * 1024 * 1024:
                raise ValueError('Image is larger than 10MB.')
            pil_image = Image.open(io.BytesIO(image_data))
        else:
            pil_image = Image.open(image_file_or_data)
    except Exception as e:
        # Fallback if image parsing fails
        return {
            'error': f'Failed to process image: {str(e)}',
            'dominant_hex': '#E11D48',
            'color_name': 'Velvet Rose',
            'palette': ['#E11D48', '#FDA4AF', '#1E293B'],
            'matches': []
        }

    dominant_rgbs = detect_dominant_colors(pil_image, count=3)
    primary_rgb = dominant_rgbs[0] if dominant_rgbs else (180, 50, 80)
    primary_hex = rgb_to_hex(primary_rgb)
    color_name = get_color_family_name(primary_rgb)
    palette_hexes = [rgb_to_hex(c) for c in dominant_rgbs]

    # Query products
    products = Product.objects.select_related('department', 'category', 'brand').prefetch_related('variants')
    if department_filter:
        products = products.filter(department__slug=department_filter)

    scored_products = []
    # Maximum theoretical color distance for normalization
    max_dist = 765.0  # Approx max perceptual distance

    for prod in products:
        prod_rgb = hex_to_rgb(prod.dominant_color_hex)
        dist = color_distance(primary_rgb, prod_rgb)

        # Baseline similarity based on dominant color
        color_similarity = max(0.0, 1.0 - (dist / max_dist))

        # Check secondary palette matches
        palette_bonus = 0.0
        for pal_rgb in dominant_rgbs[1:]:
            pal_dist = color_distance(pal_rgb, prod_rgb)
            if pal_dist < 150:
                palette_bonus += 0.08

        # Tag bonus if color matches keywords in product visual_tags
        tag_bonus = 0.0
        tags_lower = (prod.visual_tags or '').lower()
        if 'red' in color_name.lower() and ('red' in tags_lower or 'ruby' in tags_lower or 'crimson' in tags_lower):
            tag_bonus += 0.12
        elif 'rose' in color_name.lower() and ('rose' in tags_lower or 'pink' in tags_lower or 'blush' in tags_lower):
            tag_bonus += 0.12
        elif 'black' in color_name.lower() and ('black' in tags_lower or 'slate' in tags_lower or 'dark' in tags_lower):
            tag_bonus += 0.12
        elif 'gold' in color_name.lower() and ('gold' in tags_lower or 'champagne' in tags_lower or 'amber' in tags_lower):
            tag_bonus += 0.12
        elif 'green' in color_name.lower() and ('green' in tags_lower or 'botanical' in tags_lower or 'sage' in tags_lower):
            tag_bonus += 0.12

        final_score = min(0.98, max(0.60, (color_similarity * 0.70) + palette_bonus + tag_bonus + 0.15))
        percent_score = int(round(final_score * 100))

        scored_products.append({
            'product': prod,
            'match_score': percent_score,
            'match_label': f"{percent_score}% Visual Match",
            'distance': dist,
        })

    # Sort descending by match score
    scored_products.sort(key=lambda x: x['match_score'], reverse=True)

    return {
        'dominant_hex': primary_hex,
        'color_name': color_name,
        'palette': palette_hexes,
        'matches': scored_products[:limit],
    }
