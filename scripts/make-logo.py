#!/usr/bin/env python3
"""Render logo.png (256x256), the Cloudron app store icon.

No image library is available on a plain Cloudron packaging checkout, so the icon
is rasterised by hand with 3x3 supersampling and written out as a PNG.
"""

import struct
import zlib

SIZE = 256
SS = 3  # supersampling factor


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_rect(px, py, x0, y0, x1, y1, r):
    if px < x0 or px > x1 or py < y0 or py > y1:
        return False
    cx = min(max(px, x0 + r), x1 - r)
    cy = min(max(py, y0 + r), y1 - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def sample(px, py):
    """Colour of a single (supersampled) point."""
    top, bottom = (0x2B, 0x7F, 0xC4), (0x11, 0x44, 0x7A)
    page, fold, rule, accent = (0xFF, 0xFF, 0xFF), (0xC9, 0xDD, 0xF0), (0x8F, 0xA8, 0xC2), (0xF2, 0x9D, 0x38)

    if not rounded_rect(px, py, 6, 6, SIZE - 6, SIZE - 6, 52):
        return None  # transparent outside the squircle
    colour = lerp(top, bottom, py / SIZE)

    # sheet of paper, with the top right corner folded over
    px0, py0, px1, py1 = 70, 52, 186, 204
    cut = 38
    if rounded_rect(px, py, px0, py0, px1, py1, 8):
        if (px - (px1 - cut)) + (py0 - py) > 0:  # above the fold diagonal
            return colour
        colour = page
        if (px - (px1 - cut)) - (py - py0) > 0:  # the folded triangle itself
            colour = fold
        # text rules
        for ry in (104, 128, 152):
            if ry <= py <= ry + 9 and px0 + 18 <= px <= px1 - 18:
                colour = rule
        # accent bar: the "converted" line
        if 176 <= py <= 185 and px0 + 18 <= px <= px0 + 62:
            colour = accent

    return colour


def main():
    rows = []
    for y in range(SIZE):
        row = bytearray()
        for x in range(SIZE):
            r = g = b = a = 0
            for sy in range(SS):
                for sx in range(SS):
                    c = sample(x + (sx + 0.5) / SS, y + (sy + 0.5) / SS)
                    if c is not None:
                        r, g, b, a = r + c[0], g + c[1], b + c[2], a + 255
            n = SS * SS
            if a == 0:
                row += bytes(4)
            else:
                hits = a // 255
                row += bytes((r // hits, g // hits, b // hits, a // n))
        rows.append(row)

    raw = b"".join(b"\x00" + bytes(r) for r in rows)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9))
           + chunk(b"IEND", b""))

    with open("logo.png", "wb") as fh:
        fh.write(png)
    print("wrote logo.png (%d bytes)" % len(png))


if __name__ == "__main__":
    main()
