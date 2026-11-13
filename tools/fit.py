"""Fit an image to the contest limits: at most 1 MiB and 1024x1024.

Dev-time helper, needs Pillow:
    uv run --quiet --with pillow python tools/fit.py SRC DST
Tries an optimized PNG first, then the best baseline JPEG (4:4:4) that fits.
The output keeps the DST name either way; the contest reads the format from the first bytes.
"""
import io
import sys

from PIL import Image

MAX_BYTES = 1048576
MAX_SIDE = 1024


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: fit.py SRC DST")
    src, dst = sys.argv[1], sys.argv[2]
    img = Image.open(src)
    img.load()
    img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    fmt, quality = "PNG", None
    if buf.tell() > MAX_BYTES:
        rgb = img.convert("RGB")
        for quality in range(95, 0, -1):
            buf = io.BytesIO()
            rgb.save(buf, "JPEG", quality=quality, subsampling=0, progressive=False, optimize=True)
            if buf.tell() <= MAX_BYTES:
                fmt = "JPEG"
                break
        else:
            sys.exit("no JPEG quality fits the size limit")

    data = buf.getvalue()
    with open(dst, "wb") as f:
        f.write(data)
    print(f"{fmt} quality={quality or '-'} {len(data)} bytes {img.size[0]}x{img.size[1]} -> {dst}")


if __name__ == "__main__":
    main()
