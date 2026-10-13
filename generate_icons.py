#!/usr/bin/env python3
"""
generate_icons.py
Generates PNG and SVG icons for PWA using standard library zlib and struct.
"""
import struct
import zlib
import os

def create_png(width, height, color_bg=(15, 23, 42), color_circle=(225, 29, 72)):
    # Simple PNG generator: dark slate background with a vibrant crimson red circle (like Japan sun)
    raw_data = bytearray()
    cx, cy = width / 2.0, height / 2.0
    radius = width * 0.35
    
    for y in range(height):
        raw_data.append(0) # filter type 0
        for x in range(width):
            dist = ((x - cx)**2 + (y - cy)**2)**0.5
            if dist <= radius:
                # Inside circle (crimson)
                raw_data.extend(color_circle)
                raw_data.append(255) # Alpha
            elif dist <= radius + 1.5:
                # Anti-alias edge
                blend = (dist - radius) / 1.5
                r = int(color_circle[0] * (1 - blend) + color_bg[0] * blend)
                g = int(color_circle[1] * (1 - blend) + color_bg[1] * blend)
                b = int(color_circle[2] * (1 - blend) + color_bg[2] * blend)
                raw_data.extend((r, g, b, 255))
            else:
                # Background slate
                raw_data.extend(color_bg)
                raw_data.append(255)

    def chunk(tag, data):
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xffffffff)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)) # 8-bit RGBA
    idat = chunk(b"IDAT", zlib.compress(bytes(raw_data)))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend

os.makedirs("icons", exist_ok=True)
with open("icons/icon-192.png", "wb") as f:
    f.write(create_png(192, 192))
with open("icons/icon-512.png", "wb") as f:
    f.write(create_png(512, 512))

print("Created icons/icon-192.png and icons/icon-512.png")
