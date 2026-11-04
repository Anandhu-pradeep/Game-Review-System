import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_gradient_image(width, height, top_color, bottom_color, title_text, subtitle_text, dest_path):
    """Creates a sleek gaming gradient banner/cover using PIL."""
    image = Image.new("RGB", (width, height), top_color)
    draw = ImageDraw.Draw(image)

    # Vertical gradient
    r1, g1, b1 = top_color
    r2, g2, b2 = bottom_color
    for y in range(height):
        factor = y / height
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add subtle geometric gaming grid / accent lines
    accent_color = (max(0, r2 - 30), min(255, g2 + 50), min(255, b2 + 70))
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=(accent_color[0]//4, accent_color[1]//4, accent_color[2]//4), width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=(accent_color[0]//4, accent_color[1]//4, accent_color[2]//4), width=1)

    # Neon border
    draw.rectangle([(8, 8), (width - 9, height - 9)], outline=(138, 43, 226), width=3)
    draw.rectangle([(14, 14), (width - 15, height - 15)], outline=(0, 210, 255), width=1)

    # Decorative gamepad emblem or circles
    center_x = width // 2
    center_y = height // 2 - 40
    draw.ellipse([(center_x - 45, center_y - 45), (center_x + 45, center_y + 45)], outline=(0, 210, 255), width=3)
    draw.ellipse([(center_x - 30, center_y - 30), (center_x + 30, center_y + 30)], outline=(168, 85, 247), width=2)

    # Text rendering (using default font if custom font not available)
    try:
        font_large = ImageFont.load_default()
    except Exception:
        font_large = None

    # Text overlay
    title_words = title_text.upper()
    draw.text((width // 2, height // 2 + 50), title_words, fill=(255, 255, 255), anchor="mm")
    if subtitle_text:
        draw.text((width // 2, height // 2 + 80), subtitle_text.upper(), fill=(0, 210, 255), anchor="mm")

    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest_path, "JPEG", quality=90)
    return str(dest_path)


def generate_avatar_image(size, bg_color, text, dest_path):
    """Creates a circular-styled gaming avatar."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer circle
    draw.ellipse([(2, 2), (size - 3, size - 3)], fill=bg_color, outline=(0, 210, 255), width=3)
    
    # Inner emblem / initial
    draw.text((size // 2, size // 2), text.upper()[:2], fill=(255, 255, 255), anchor="mm")
    
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest_path, "PNG")
    return str(dest_path)

