# NTP Clock for MAX7219 LED Matrix

A Python application that displays the current time in `HH:MM:SS` format using four cascaded MAX7219 8x8 dot matrix LED modules.

## Features

- Displays time in HH:MM:SS format
- Custom 3x7 pixel font optimized for 8-pixel-high displays
- Syncs display updates to second boundaries for accurate timing
- Emulator mode (Tkinter) for development/testing without hardware
- Hardware mode for Raspberry Pi deployment
- Adjustable brightness (0-255)

## Hardware Requirements

- Raspberry Pi (any model with SPI)
- 4x MAX7219 8x8 Dot Matrix LED Modules (cascaded)
- Jumper wires

### Wiring (Raspberry Pi to MAX7219)

| MAX7219 Pin | Raspberry Pi Pin |
|-------------|------------------|
| VCC         | 5V (Pin 2)       |
| GND         | GND (Pin 6)      |
| DIN         | MOSI (Pin 19)    |
| CS          | CE0 (Pin 24)     |
| CLK         | SCLK (Pin 23)    |

## Installation

### On Raspberry Pi

1. Clone or download this repository:
   ```bash
   cd ~/ntpclock
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Enable SPI:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options -> SPI -> Enable
   ```

5. Add your user to the SPI and GPIO groups:
   ```bash
   sudo usermod -a -G spi,gpio $USER
   ```
   Then log out and back in (or reboot).

6. Verify SPI is enabled:
   ```bash
   ls /dev/spi*
   # Should show /dev/spidev0.0 and /dev/spidev0.1
   ```

### For Emulator Only (development machine)

```bash
python3 -m venv venv
source venv/bin/activate
pip install Pillow
```

Note: The emulator only requires Pillow since it uses Tkinter (included with Python).

## Usage

### Emulator Mode (for development/testing)

```bash
python ntpclock.py --emulator
```

This opens a Tkinter window simulating the LED matrix display with red LED dots.

### Hardware Mode (on Raspberry Pi)

```bash
python ntpclock.py
```

### Options

```
usage: ntpclock.py [-h] [--emulator] [--brightness 0-255]

NTP Clock Display for MAX7219 LED Matrix

optional arguments:
  -h, --help            show this help message and exit
  --emulator, -e        Use Tkinter emulator instead of real hardware
  --brightness, -b 0-255
                        Display brightness (0-255, default: 128)
```

### Examples

```bash
# Run with emulator
python ntpclock.py -e

# Run on hardware with dim display (good for nighttime)
python ntpclock.py -b 16

# Run on hardware with full brightness
python ntpclock.py -b 255
```

## Display Layout

The display shows time in `HH:MM:SS` format across 32x8 pixels:

```
 ┌────────────────────────────────┐
 │  12:34:56                      │
 └────────────────────────────────┘
    └─┬─┘ └─┬─┘ └─┬─┘
    Hours Minutes Seconds
```

## Running at Boot (Raspberry Pi)

A systemd service file is included. To install:

```bash
# Copy the service file
sudo cp ntpclock.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable to start on boot
sudo systemctl enable ntpclock.service

# Start now
sudo systemctl start ntpclock.service
```

To check status or view logs:
```bash
sudo systemctl status ntpclock.service
journalctl -u ntpclock.service -f
```

To stop or disable:
```bash
sudo systemctl stop ntpclock.service
sudo systemctl disable ntpclock.service
```

**Note:** Edit the service file if you need to adjust the brightness or if your installation path differs from `/home/dietpi/ntpclock/`.

## Troubleshooting

### SPI Permission Denied
Add your user to the spi and gpio groups:
```bash
sudo usermod -a -G spi,gpio $USER
```
Then log out and back in (or reboot).

### Display Shows Nothing
- Check wiring connections
- Verify SPI is enabled: `ls /dev/spi*`
- Try increasing brightness: `python ntpclock.py -b 255`

### Display is Mirrored or Rotated
The code uses `block_orientation=-90` which works for most pre-assembled MAX7219 modules. If your display looks wrong, edit `ntpclock.py` and try:
- `block_orientation=90` (opposite rotation)
- `block_orientation=0` (no rotation)
- `blocks_arranged_in_reverse_order=True` (if modules are chained in reverse)

### Module Not Found: spidev
Install the spidev module:
```bash
pip install spidev
```

### Emulator Window Doesn't Open
The emulator uses Tkinter which comes with Python. On some Linux systems you may need:
```bash
sudo apt-get install python3-tk
```

## License

MIT License
