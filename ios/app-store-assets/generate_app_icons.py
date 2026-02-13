#!/usr/bin/env python3
"""Generate CollectorStream app icons with black background, green bolt, white text"""

from PIL import Image, ImageDraw, ImageFont
import os

# Colors
BLACK = (10, 10, 10)  # Almost black
GREEN = (16, 185, 129)  # #10b981
WHITE = (255, 255, 255)

def create_icon(size, output_path):
    """Create app icon with logo"""
    # Create image with black background
    img = Image.new('RGB', (size, size), BLACK)
    draw = ImageDraw.Draw(img)

    # Scale everything based on icon size
    scale = size / 1024.0

    # Draw lightning bolt (simplified as a triangle/zigzag shape)
    bolt_width = int(180 * scale)
    bolt_height = int(280 * scale)
    bolt_x = (size - bolt_width) // 2
    bolt_y = int(200 * scale)

    # Lightning bolt path (approximation)
    bolt_points = [
        (bolt_x + bolt_width // 2, bolt_y),  # Top
        (bolt_x + int(bolt_width * 0.7), bolt_y + bolt_height // 2),  # Right middle
        (bolt_x + int(bolt_width * 0.55), bolt_y + bolt_height // 2),  # Center
        (bolt_x + bolt_width, bolt_y + bolt_height),  # Bottom right
        (bolt_x + int(bolt_width * 0.45), bolt_y + int(bolt_height * 0.65)),  # Left of center
        (bolt_x + int(bolt_width * 0.3), bolt_y + bolt_height // 2),  # Left middle
        (bolt_x + bolt_width // 2, bolt_y)  # Back to top
    ]

    draw.polygon(bolt_points, fill=GREEN)

    # Add text "CollectorStream"
    text = "CollectorStream"
    text_y = bolt_y + bolt_height + int(30 * scale)

    # Use default font (PIL built-in)
    try:
        # Try to use a nice system font
        font_size = int(80 * scale)
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()

    # Get text size and center it
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size - text_width) // 2

    # Draw text
    draw.text((text_x, text_y), text, fill=WHITE, font=font)

    # Save
    img.save(output_path, 'PNG', quality=100)
    print(f"✓ Created {size}x{size} icon: {output_path}")

def main():
    """Generate all required icon sizes"""
    output_dir = "icons"
    os.makedirs(output_dir, exist_ok=True)

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

    print(f"\n✅ All {len(sizes)} app icons created successfully!")

if __name__ == '__main__':
    main()
