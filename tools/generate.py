"""Generate candidate images for every prompt x model pair through OpenRouter.

Usage: python -u tools/generate.py MODEL [MODEL ...] [--ids a,b] [--reps N]
Reads OPENROUTER_API_KEY from the environment and prompts from tools/prompts.json.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://openrouter.ai/api/v1/images"
TIMEOUT = 240
EXT = {"image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp"}


def post(key, body):
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')}") from None


def generate(key, item, model, suffix=""):
    body = {"model": model, "prompt": item["prompt"], "aspect_ratio": "1:1"}
    if model.startswith("openai/"):
        body["quality"] = "medium"
    else:
        body["resolution"] = "1K"
    data = post(key, body)
    if "error" in data:
        raise RuntimeError(json.dumps(data["error"]))
    image = data["data"][0]
    mime = image.get("media_type") or "image/png"
    ext = EXT.get(mime, mime.split("/")[-1])
    path = os.path.join(ROOT, "candidates", f"{item['id']}__{model.replace('/', '_')}{suffix}.{ext}")
    raw = base64.b64decode(image["b64_json"])
    with open(path, "wb") as f:
        f.write(raw)
    return path, len(raw), float((data.get("usage") or {}).get("cost") or 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    parser.add_argument("--ids", help="comma-separated prompt ids (default: all)")
    parser.add_argument("--reps", type=int, default=1, help="images per prompt x model pair")
    args = parser.parse_args()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set")
    with open(os.path.join(ROOT, "tools", "prompts.json"), encoding="utf-8") as f:
        prompts = json.load(f)
    if args.ids:
        wanted = args.ids.split(",")
        unknown = set(wanted) - {p["id"] for p in prompts}
        if unknown:
            sys.exit(f"unknown prompt ids: {', '.join(sorted(unknown))}")
        prompts = [p for p in prompts if p["id"] in wanted]
    suffixes = [f"_r{i}" for i in range(1, args.reps + 1)] if args.reps > 1 else [""]
    os.makedirs(os.path.join(ROOT, "candidates"), exist_ok=True)
    jobs = [(p, m, s) for p in prompts for m in args.models for s in suffixes]
    total = 0.0
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = {pool.submit(generate, key, p, m, s): (p["id"] + s, m) for p, m, s in jobs}
        for fut in as_completed(futures):
            pid, model = futures[fut]
            try:
                path, size, cost = fut.result()
                total += cost
                print(f"OK   {os.path.relpath(path, ROOT)} {size} bytes ${cost:.4f}", flush=True)
            except Exception as e:
                msg = str(e).replace(key, "***")[:300]
                print(f"FAIL {pid} {model}: {msg}", flush=True)
    print(f"TOTAL cost ${total:.4f}", flush=True)


if __name__ == "__main__":
    main()
