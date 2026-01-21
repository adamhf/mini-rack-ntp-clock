#!/usr/bin/env python3
"""
NTP Clock Display for MAX7219 8x8 LED Matrix Modules

Displays time in HH:MM:SS format using four cascaded MAX7219 8x8 dot matrix
LED modules (32x8 pixels total). Supports both hardware (Raspberry Pi) and
emulator modes for development/testing.

Usage:
    python ntpclock.py --emulator    # Run with Tkinter emulator
    python ntpclock.py               # Run on actual hardware (Raspberry Pi)
"""

import argparse
import time
import sys
from datetime import datetime

from PIL import Image, ImageDraw


# Custom 3x7 font for digits - tall and readable, fits 32px width
# Each digit is defined as a list of 7 rows, each row is 3 bits wide
# Layout: HH:MM:SS = 6 digits × 4px + 2 colons × 2px + trailing = 28px (centered)
DIGIT_FONT = {
    '0': [0b111, 0b101, 0b101, 0b101, 0b101, 0b101, 0b111],
    '1': [0b010, 0b110, 0b010, 0b010, 0b010, 0b010, 0b111],
    '2': [0b111, 0b001, 0b001, 0b111, 0b100, 0b100, 0b111],
    '3': [0b111, 0b001, 0b001, 0b111, 0b001, 0b001, 0b111],
    '4': [0b101, 0b101, 0b101, 0b111, 0b001, 0b001, 0b001],
    '5': [0b111, 0b100, 0b100, 0b111, 0b001, 0b001, 0b111],
    '6': [0b111, 0b100, 0b100, 0b111, 0b101, 0b101, 0b111],
    '7': [0b111, 0b001, 0b001, 0b001, 0b001, 0b001, 0b001],
    '8': [0b111, 0b101, 0b101, 0b111, 0b101, 0b101, 0b111],
    '9': [0b111, 0b101, 0b101, 0b111, 0b001, 0b001, 0b111],
    ':': [0b0, 0b0, 0b1, 0b0, 0b1, 0b0, 0b0],  # Colon separator (1 pixel wide)
}


def draw_char(draw, x, y, char, fill="white"):
    """Draw a single character from the custom font at position (x, y)."""
    if char not in DIGIT_FONT:
        return 0

    pattern = DIGIT_FONT[char]
    width = 3 if char.isdigit() else 1

    for row_idx, row in enumerate(pattern):
        for col_idx in range(width):
            bit_pos = width - 1 - col_idx
            if row & (1 << bit_pos):
                draw.point((x + col_idx, y + row_idx), fill=fill)

    return width


def draw_time_string(draw, time_str, y_offset=0):
    """
    Draw a time string (HH:MM:SS) centered on the display.

    Layout for 32x8 display with 3x7 font:
    - Each digit: 3 pixels wide
    - Colon: 1 pixel wide
    - Spacing: 1 pixel between all elements

    Total: 6 digits (18px) + 2 colons (2px) + 7 spaces (7px) = 27px
    Centered with 2-3px padding on each side.
    """
    x = 2  # Center the 27px content on 32px display

    for char in time_str:
        if char in DIGIT_FONT:
            width = draw_char(draw, x, y_offset, char)
            x += width + 1  # Add 1 pixel spacing after each character


class TkinterEmulator:
    """
    A simple Tkinter-based LED matrix emulator.
    Displays pixels as circles to simulate LED dots.
    """

    def __init__(self, width=32, height=8, scale=15, led_color='red', bg_color='#1a1a1a'):
        import tkinter as tk

        self.width = width
        self.height = height
        self.scale = scale
        self.led_color = led_color
        self.bg_color = bg_color
        self.mode = '1'

        self.root = tk.Tk()
        self.root.title("LED Matrix Emulator - NTP Clock")
        self.root.configure(bg='#333333')
        self.root.resizable(False, False)

        # Calculate canvas size with padding for LED effect
        padding = 4
        canvas_width = width * scale + padding * 2
        canvas_height = height * scale + padding * 2

        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg=bg_color,
            highlightthickness=2,
            highlightbackground='#555555'
        )
        self.canvas.pack(padx=10, pady=10)

        # Pre-create LED circles for efficiency
        self.leds = []
        led_radius = scale // 2 - 2
        for y in range(height):
            row = []
            for x in range(width):
                cx = padding + x * scale + scale // 2
                cy = padding + y * scale + scale // 2
                led = self.canvas.create_oval(
                    cx - led_radius, cy - led_radius,
                    cx + led_radius, cy + led_radius,
                    fill='#2a2a2a',  # Off state (dim)
                    outline='#1a1a1a'
                )
                row.append(led)
            self.leds.append(row)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._running = True

    def _on_close(self):
        self._running = False
        self.root.destroy()

    def display(self, image):
        """Update the display with a PIL Image."""
        if not self._running:
            raise KeyboardInterrupt("Window closed")

        # Convert to 1-bit if needed
        if image.mode != '1':
            image = image.convert('1')

        pixels = image.load()

        for y in range(self.height):
            for x in range(self.width):
                pixel = pixels[x, y]
                # In mode '1': 255 = white (on), 0 = black (off)
                if pixel:
                    self.canvas.itemconfig(self.leds[y][x], fill=self.led_color)
                else:
                    self.canvas.itemconfig(self.leds[y][x], fill='#2a2a2a')

        self.root.update()

    def cleanup(self):
        """Clean up resources."""
        if self._running:
            self._running = False
            self.root.destroy()

    def contrast(self, value):
        """Adjust LED brightness (approximate with color intensity)."""
        intensity = int((value / 255) * 255)
        self.led_color = f'#{intensity:02x}0000'


class CanvasContext:
    """Context manager that mimics luma.core.render.canvas behavior."""

    def __init__(self, device):
        self.device = device
        self.image = Image.new('1', (device.width, device.height), 0)
        self.draw = ImageDraw.Draw(self.image)

    def __enter__(self):
        return self.draw

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.device.display(self.image)
        return False


def canvas(device):
    """Create a canvas context for drawing on the device."""
    return CanvasContext(device)


def get_device(emulator=False, width=32, height=8):
    """
    Create and return the appropriate display device.

    Args:
        emulator: If True, use Tkinter emulator; otherwise use real hardware
        width: Display width in pixels
        height: Display height in pixels

    Returns:
        Device instance (TkinterEmulator or MAX7219)
    """
    if emulator:
        device = TkinterEmulator(width=width, height=height, scale=15)
        print("Running in emulator mode (Tkinter)")
    else:
        from luma.core.interface.serial import spi, noop
        from luma.led_matrix.device import max7219
        from luma.core.render import canvas as luma_canvas

        # Replace our canvas with luma's canvas for hardware mode
        global canvas
        canvas = luma_canvas

        serial = spi(port=0, device=0, gpio=noop())
        device = max7219(
            serial,
            cascaded=4,
            block_orientation=-90,
            rotate=0,
            blocks_arranged_in_reverse_order=False
        )
        device.contrast(128)
        print("Running on hardware (MAX7219)")

    return device


def format_time(dt):
    """
    Format datetime as HH:MM:SS.

    Args:
        dt: datetime object

    Returns:
        Formatted time string
    """
    return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def run_clock(device):
    """
    Main clock loop - continuously update the display with current time.
    Syncs updates to the exact second boundary for precise timing.

    Args:
        device: luma device instance
    """
    print("Starting clock display... Press Ctrl+C to exit.")

    try:
        last_second = -1

        while True:
            now = datetime.now()

            # Only update display when the second changes
            if now.second != last_second:
                last_second = now.second
                time_str = format_time(now)

                with canvas(device) as draw:
                    draw_time_string(draw, time_str, y_offset=0)

            # Small sleep to avoid busy-waiting, but short enough to catch the change
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nClock stopped.")


def main():
    """Parse arguments and start the clock."""
    parser = argparse.ArgumentParser(
        description='NTP Clock Display for MAX7219 LED Matrix',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --emulator    Run with pygame emulator for testing
    %(prog)s               Run on Raspberry Pi hardware
    %(prog)s --brightness 64  Run with lower brightness
        """
    )

    parser.add_argument(
        '--emulator', '-e',
        action='store_true',
        help='Use pygame emulator instead of real hardware'
    )

    parser.add_argument(
        '--brightness', '-b',
        type=int,
        default=128,
        choices=range(0, 256),
        metavar='0-255',
        help='Display brightness (0-255, default: 128)'
    )

    args = parser.parse_args()

    try:
        device = get_device(emulator=args.emulator)

        if not args.emulator:
            device.contrast(args.brightness)

        run_clock(device)

    except ImportError as e:
        print(f"Import error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'device' in locals():
            device.cleanup()


if __name__ == '__main__':
    main()
