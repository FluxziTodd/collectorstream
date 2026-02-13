#!/usr/bin/env python3
"""Generate CollectorStream app icons with black background, green trend arrow, text"""

from PIL import Image, ImageDraw, ImageFont
import os

# Colors
BLACK = (10, 10, 10)
GREEN = (16, 185, 129)  # #10b981
WHITE = (255, 255, 255)

def create_icon(size, output_path):
    """Create app icon with upward trending chart logo"""
    img = Image.new('RGB', (size, size), BLACK)
    draw = ImageDraw.Draw(img)

    scale = size / 1024.0

    # Icon positioning (centered, slightly above middle)
    icon_top = int(280 * scale)
    icon_left = int(size * 0.15)
    icon_width = int(size * 0.7)

    # Draw upward trending chart/arrow
    chart_height = int(120 * scale)
    line_width = max(2, int(8 * scale))

    # Start point (bottom left)
    x1, y1 = icon_left + int(icon_width * 0.1), icon_top + chart_height
    # Middle point (lower middle)
    x2, y2 = icon_left + int(icon_width * 0.35), icon_top + int(chart_height * 0.6)
    # High point (top right area)
    x3, y3 = icon_left + int(icon_width * 0.7), icon_top + int(chart_height * 0.1)

    # Draw the trending line
    draw.line([x1, y1, x2, y2], fill=GREEN, width=line_width)
    draw.line([x2, y2, x3, y3], fill=GREEN, width=line_width)

    # Draw arrow head at the end
    arrow_size = int(30 * scale)
    arrow_points = [
        (x3, y3),
        (x3 - arrow_size//2, y3 + arrow_size),
        (x3 + arrow_size//2, y3 + arrow_size)
    ]
    draw.polygon(arrow_points, fill=GREEN)

    # Draw small circles at data points
    dot_radius = int(12 * scale)
    draw.ellipse([x1-dot_radius, y1-dot_radius, x1+dot_radius, y1+dot_radius], fill=GREEN)
    draw.ellipse([x2-dot_radius, y2-dot_radius, x2+dot_radius, y2+dot_radius], fill=GREEN)
    draw.ellipse([x3-dot_radius, y3-dot_radius, x3+dot_radius, y3+dot_radius], fill=GREEN)

    # Add text "Collector" (white) + "Stream" (green)
    text_y = icon_top + chart_height + int(80 * scale)

    try:
        font_size = int(90 * scale)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        font_bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()
        font_bold = font

    # Calculate text positioning for horizontal layout
    text1 = "Collector"
    text2 = "Stream"

    # Get widths
    bbox1 = font.getbbox(text1)
    bbox2 = font.getbbox(text2)
    width1 = bbox1[2] - bbox1[0]
    width2 = bbox2[2] - bbox2[0]

    total_width = width1 + width2 + int(10 * scale)  # Small gap
    text_x = (size - total_width) // 2

    # Draw "Collector" in white
    draw.text((text_x, text_y), text1, fill=WHITE, font=font)

    # Draw "Stream" in green
    draw.text((text_x + width1 + int(10 * scale), text_y), text2, fill=GREEN, font=font)

    img.save(output_path, 'PNG', quality=100)
    print(f"✓ Created {size}x{size} icon")

def main():
    """Generate all required icon sizes"""
    output_dir = "icons"

    sizes = {
        'icon_1024x1024.png': 1024,
        'icon_180x180.png': 180,
        'icon_167x167.png': 167,
        'icon_152x152.png': 152,
        'icon_120x120.png': 120,
        'icon_76x76.png': 76,
    }

    for filename, size in sizes.items():
        output_path = os.path.join(output_dir, filename)
        create_icon(size, output_path)

    print(f"\n✅ All {len(sizes)} app icons created!")

if __name__ == '__main__':
    main()
