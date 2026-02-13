#!/usr/bin/env python3
"""Create app icons using the exact logo from the app screenshot"""

from PIL import Image, ImageDraw, ImageFont
import os

BLACK = (0, 0, 0)
GREEN = (16, 185, 129)  # #10b981
WHITE = (255, 255, 255)

def draw_trend_arrow(draw, x, y, size, color, line_width):
    """Draw the upward trending chart arrow icon"""
    # Three points making an upward trend
    points = [
        (x, y + size),  # Start bottom left
        (x + size * 0.4, y + size * 0.5),  # Middle
        (x + size * 0.8, y)  # End top right
    ]

    # Draw the line segments
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=line_width)

    # Draw arrow head at the end
    arrow_x, arrow_y = points[-1]
    arrow_size = size * 0.25
    draw.line([arrow_x, arrow_y, arrow_x + arrow_size, arrow_y + arrow_size], fill=color, width=line_width)
    draw.line([arrow_x, arrow_y, arrow_x, arrow_y + arrow_size], fill=color, width=line_width)

def create_icon(size, output_path):
    """Create app icon matching the screenshot logo"""
    img = Image.new('RGB', (size, size), BLACK)
    draw = ImageDraw.Draw(img)

    scale = size / 1024.0

    # Icon and text centered vertically
    content_height = int(200 * scale)
    start_y = (size - content_height) // 2

    # Trend arrow icon on the left
    icon_size = int(80 * scale)
    icon_x = int(size * 0.15)
    icon_y = start_y + (content_height - icon_size) // 2
    line_width = max(2, int(6 * scale))

    draw_trend_arrow(draw, icon_x, icon_y, icon_size, GREEN, line_width)

    # Text next to icon
    try:
        font_size = int(70 * scale)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()

    text_x = icon_x + icon_size + int(20 * scale)
    text_y = start_y + (content_height - int(70 * scale)) // 2

    # Draw "Collector" in white
    draw.text((text_x, text_y), "Collector", fill=WHITE, font=font)

    # Calculate width of "Collector" to position "Stream"
    collector_width = draw.textlength("Collector", font=font)

    # Draw "Stream" in green right after
    draw.text((text_x + collector_width, text_y), "Stream", fill=GREEN, font=font)

    img.save(output_path, 'PNG', quality=100)
    print(f"✓ Created {size}x{size}")

def main():
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
        create_icon(size, os.path.join(output_dir, filename))

    print("\n✅ All app icons created with CollectorStream logo!")

if __name__ == '__main__':
    main()
