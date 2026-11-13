"""Copy the committed entry.png to the contest output directory."""
import os
import shutil
import sys

MAX_BYTES = 1048576
SIGNATURES = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "entry.png")
with open(src, "rb") as f:
    head = f.read(8)
if not head.startswith(SIGNATURES):
    sys.exit(f"{src} is not a PNG or JPEG file")
size = os.path.getsize(src)
if size > MAX_BYTES:
    sys.exit(f"{src} is {size} bytes, over the {MAX_BYTES} byte limit")

out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(out, exist_ok=True)
shutil.copyfile(src, os.path.join(out, "entry.png"))
