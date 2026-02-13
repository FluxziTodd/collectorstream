#!/usr/bin/env python3
"""
Generate CollectorStream app icons in all required sizes.
Uses PIL to create a simple but professional icon with the app branding.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# App colors
BG_COLOR = "#0a0a0a"  # Black background
ACCENT_COLOR = "#10b981"  # Green accent
CARD_COLOR = "#151515"  # Card background

# Icon sizes needed for App Store
SIZES = {
    "App Store": 1024,
    "iPhone 3x": 180,
    "iPhone 2x": 120,
    "iPad Pro": 167,
    "iPad": 152,
    "iPad 2x": 76,
}

def create_icon(size):
    """Create a CollectorStream icon at the specified size."""
    # Create image with black background
    img = Image.new('RGB', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    padding = size * 0.15
    card_width = size * 0.35
    card_height = size * 0.50
    corner_radius = size * 0.08

    # Draw two overlapping cards to represent a collection
    # Card 1 (back card)
    card1_x = padding
    card1_y = padding + (size * 0.05)
    draw_rounded_rectangle(
        draw,
        [(card1_x, card1_y), (card1_x + card_width, card1_y + card_height)],
        corner_radius,
        fill=CARD_COLOR,
        outline=ACCENT_COLOR,
        width=int(size * 0.02)
    )

    # Card 2 (front card)
    card2_x = size - padding - card_width
    card2_y = padding
    draw_rounded_rectangle(
        draw,
        [(card2_x, card2_y), (card2_x + card_width, card2_y + card_height)],
        corner_radius,
        fill=CARD_COLOR,
        outline=ACCENT_COLOR,
        width=int(size * 0.02)
    )

    # Draw accent elements (representing card scanner viewfinder)
    viewfinder_size = size * 0.4
    viewfinder_x = (size - viewfinder_size) / 2
    viewfinder_y = (size - viewfinder_size) / 2 + (size * 0.08)
    corner_len = viewfinder_size * 0.25
    line_width = int(size * 0.025)

    # Top-left corner
    draw.line([(viewfinder_x, viewfinder_y), (viewfinder_x + corner_len, viewfinder_y)],
              fill=ACCENT_COLOR, width=line_width)
    draw.line([(viewfinder_x, viewfinder_y), (viewfinder_x, viewfinder_y + corner_len)],
              fill=ACCENT_COLOR, width=line_width)

    # Top-right corner
    draw.line([(viewfinder_x + viewfinder_size - corner_len, viewfinder_y),
               (viewfinder_x + viewfinder_size, viewfinder_y)],
              fill=ACCENT_COLOR, width=line_width)
    draw.line([(viewfinder_x + viewfinder_size, viewfinder_y),
               (viewfinder_x + viewfinder_size, viewfinder_y + corner_len)],
              fill=ACCENT_COLOR, width=line_width)

    # Bottom-left corner
    draw.line([(viewfinder_x, viewfinder_y + viewfinder_size - corner_len),
               (viewfinder_x, viewfinder_y + viewfinder_size)],
              fill=ACCENT_COLOR, width=line_width)
    draw.line([(viewfinder_x, viewfinder_y + viewfinder_size),
               (viewfinder_x + corner_len, viewfinder_y + viewfinder_size)],
              fill=ACCENT_COLOR, width=line_width)

    # Bottom-right corner
    draw.line([(viewfinder_x + viewfinder_size, viewfinder_y + viewfinder_size - corner_len),
               (viewfinder_x + viewfinder_size, viewfinder_y + viewfinder_size)],
              fill=ACCENT_COLOR, width=line_width)
    draw.line([(viewfinder_x + viewfinder_size - corner_len, viewfinder_y + viewfinder_size),
               (viewfinder_x + viewfinder_size, viewfinder_y + viewfinder_size)],
              fill=ACCENT_COLOR, width=line_width)

    return img

def draw_rounded_rectangle(draw, coords, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1 = coords[0]
    x2, y2 = coords[1]

    # Draw rectangles for sides and center
    draw.rectangle([(x1 + radius, y1), (x2 - radius, y2)], fill=fill)
    draw.rectangle([(x1, y1 + radius), (x2, y2 - radius)], fill=fill)

    # Draw circles for corners
    draw.ellipse([(x1, y1), (x1 + radius * 2, y1 + radius * 2)], fill=fill)
    draw.ellipse([(x2 - radius * 2, y1), (x2, y1 + radius * 2)], fill=fill)
    draw.ellipse([(x1, y2 - radius * 2), (x1 + radius * 2, y2)], fill=fill)
    draw.ellipse([(x2 - radius * 2, y2 - radius * 2), (x2, y2)], fill=fill)

    # Draw outline if specified
    if outline:
        # Top and bottom
        draw.arc([(x1, y1), (x1 + radius * 2, y1 + radius * 2)], 180, 270, fill=outline, width=width)
        draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
        draw.arc([(x2 - radius * 2, y1), (x2, y1 + radius * 2)], 270, 360, fill=outline, width=width)

        draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)
        draw.arc([(x2 - radius * 2, y2 - radius * 2), (x2, y2)], 0, 90, fill=outline, width=width)
        draw.line([(x2 - radius, y2), (x1 + radius, y2)], fill=outline, width=width)

        draw.arc([(x1, y2 - radius * 2), (x1 + radius * 2, y2)], 90, 180, fill=outline, width=width)
        draw.line([(x1, y2 - radius), (x1, y1 + radius)], fill=outline, width=width)

def main():
    output_dir = "icons"
    os.makedirs(output_dir, exist_ok=True)

    print("🎨 Generating CollectorStream app icons...\n")

    for name, size in SIZES.items():
        print(f"Creating {name} icon ({size}x{size})...")
        icon = create_icon(size)
        filename = f"{output_dir}/icon_{size}x{size}.png"
        icon.save(filename, "PNG")
        print(f"✅ Saved: {filename}")

    print(f"\n✨ All icons generated successfully!")
    print(f"\nNext steps:")
    print(f"1. Review icons in the '{output_dir}' directory")
    print(f"2. In Xcode, go to Assets.xcassets → AppIcon")
    print(f"3. Drag and drop each icon into its corresponding slot")
    print(f"4. The 1024x1024 icon is for App Store listing")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("❌ Error: PIL (Pillow) not installed")
        print("Install with: pip3 install Pillow")
        print("\nAlternatively, use an online tool like:")
        print("- https://appicon.co")
        print("- https://makeappicon.com")
        print("\nJust upload a 1024x1024 icon and it will generate all sizes for you.")
