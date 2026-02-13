#!/usr/bin/env python3
"""Resize screenshots to exact App Store Connect requirements"""

from PIL import Image
import os

# App Store Connect requirement: 1284 × 2778px (iPhone 6.7" display)
TARGET_WIDTH = 1284
TARGET_HEIGHT = 2778

def resize_screenshot(input_path, output_path):
    """Resize screenshot to exact App Store dimensions"""
    img = Image.open(input_path)

    # Resize to exact dimensions
    resized = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # Save with high quality
    resized.save(output_path, 'PNG', quality=100, optimize=True)
    print(f"✓ Resized {os.path.basename(input_path)} → {TARGET_WIDTH}×{TARGET_HEIGHT}")

def main():
    desktop = os.path.expanduser("~/Desktop")
    output_dir = os.path.expanduser("~/Desktop/app_store_screenshots")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Screenshots to resize
    screenshots = [
        "01_login.png",
        "02_draft_board.png",
        "03_collection.png",
        "04_profile.png",
        "05_scanner.png"
    ]

    print(f"Resizing screenshots to {TARGET_WIDTH}×{TARGET_HEIGHT}px...\n")

    for filename in screenshots:
        input_path = os.path.join(desktop, filename)
        output_path = os.path.join(output_dir, filename)

        if os.path.exists(input_path):
            resize_screenshot(input_path, output_path)
        else:
            print(f"⚠️  Not found: {filename}")

    print(f"\n✅ All screenshots resized to App Store Connect requirements!")
    print(f"📁 Saved to: {output_dir}")
    print(f"\nYou can now upload these screenshots to App Store Connect.")

if __name__ == '__main__':
    main()
