#!/usr/bin/env python3
"""Create app icons with stock chart L-axis and price line"""

from PIL import Image, ImageDraw, ImageFont
import os

BLACK = (0, 0, 0)
GREEN = (16, 185, 129)  # #10b981
WHITE = (255, 255, 255)

def create_icon(size, output_path):
    """Create app icon with stock chart design"""
    img = Image.new('RGB', (size, size), BLACK)
    draw = ImageDraw.Draw(img)

    scale = size / 1024.0
    line_width = max(2, int(6 * scale))

    # Logo area (icon + text)
    logo_area_height = int(180 * scale)
    logo_y = (size - logo_area_height) // 2

    # Chart icon dimensions
    chart_width = int(140 * scale)
    chart_height = int(100 * scale)
    chart_x = int(size * 0.12)
    chart_y = logo_y + (logo_area_height - chart_height) // 2

    # Draw L-shaped axis (vertical + horizontal)
    # Vertical line (Y-axis)
    y_axis_x = chart_x
    y_axis_top = chart_y
    y_axis_bottom = chart_y + chart_height
    draw.line([(y_axis_x, y_axis_top), (y_axis_x, y_axis_bottom)], fill=GREEN, width=line_width)

    # Horizontal line (X-axis)
    x_axis_y = y_axis_bottom
    x_axis_left = y_axis_x
    x_axis_right = chart_x + chart_width
    draw.line([(x_axis_left, x_axis_y), (x_axis_right, x_axis_y)], fill=GREEN, width=line_width)

    # Draw stock price line (zigzag going up with down movements)
    # Center the line in the chart area
    line_start_x = y_axis_x + int(15 * scale)
    line_y_center = chart_y + chart_height // 2  # Center vertically

    # Price points (x_offset, y_offset) - centered around middle
    price_points = [
        (0, 20 * scale),  # Start slightly below center
        (25 * scale, 0),  # Rise to center
        (50 * scale, 10 * scale),  # Dip a bit
        (75 * scale, -25 * scale),  # Big rise above center
        (100 * scale, -30 * scale),  # Continue rising
    ]

    # Draw the price line segments
    points = [(line_start_x + px, line_y_center + py) for px, py in price_points]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=GREEN, width=line_width)

    # Draw arrow at the end pointing RIGHT (>)
    last_x, last_y = points[-1]
    arrow_size = int(15 * scale)
    # Right-pointing arrow (>)
    draw.polygon([
        (last_x + arrow_size, last_y),  # Point
        (last_x, last_y - arrow_size//2),  # Top
        (last_x, last_y + arrow_size//2)   # Bottom
    ], fill=GREEN)

    # Text: "Collector" (white) + "Stream" (green)
    text_x = chart_x + chart_width + int(30 * scale)
    text_y = logo_y + (logo_area_height - int(60 * scale)) // 2

    try:
        font_size = int(70 * scale)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", font_size)
        except:
            # Skip text on very small icons
            if size >= 120:
                print(f"Warning: Using default font for {size}x{size}")
            img.save(output_path, 'PNG', quality=100)
            return

    # Draw "Collector" in white
    draw.text((text_x, text_y), "Collector", fill=WHITE, font=font)

    # Draw "Stream" in green right after
    try:
        collector_width = draw.textlength("Collector", font=font)
    except:
        collector_width = int(220 * scale)  # Fallback estimate

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

    print("Creating stock chart app icons...")
    for filename, size in sizes.items():
        create_icon(size, os.path.join(output_dir, filename))

    print("\n✅ All app icons created with stock chart logo!")

if __name__ == '__main__':
    main()
