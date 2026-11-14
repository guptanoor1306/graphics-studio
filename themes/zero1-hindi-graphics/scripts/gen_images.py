#!/usr/bin/env python3
"""Generate every pending `gen:<key>` plate of a Zero1 Hindi spec with an image API — no Figma, no UI.

  python3 $K/scripts/gen_images.py spec.json                 # all pending plates
  python3 $K/scripts/gen_images.py spec.json --only kandivali_flat,local_train
  python3 $K/scripts/gen_images.py spec.json --force         # regenerate even if gen/<key>.png exists
  python3 $K/scripts/gen_images.py spec.json --dry-run       # build prompts + request bodies, no network

Provider (first key found wins, or force with --provider):
  GEMINI_API_KEY / GOOGLE_API_KEY  -> Google "Nano Banana" (gemini-2.5-flash-image; override IMG_MODEL)
  OPENAI_API_KEY                   -> OpenAI gpt-image-1 (images/edits with reference images)

Style lock: every request carries the kit's own prompt (build.prompt_text: world + figure + Arjun bible) AND
reference images from past episodes (3 house plates + the Arjun cut-out when Arjun is in the shot), so results
come back in the paper-3D stop-motion look, not a generic illustration. Spec keys may add `"refs": [...]`
(asset:plates/<file>.jpg or asset:characters/<file>.png) to steer a specific scene.

Output: gen/<key>.png next to spec.json — 16:9 plates cover-cropped to 1920x1080, `cutout` keys with the white
background removed (flood fill from the border, no extra dependency). A log is written to gen/_gen_log.json.
Only the Python standard library + Pillow are needed.
"""
import argparse, base64, io, json, os, sys, time, uuid, urllib.request, urllib.error
from collections import deque
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402  (kit's own prompt bible: build.prompt_text)

DEFAULT_STYLE_REFS = ["asset:plates/v2_63-64.jpg", "asset:plates/v2_21.jpg", "asset:plates/v1_10-11.jpg"]
ARJUN_REF = {"city": "asset:characters/arjun_city_neutral.png", "kerala": "asset:characters/arjun_kerala_neutral.png",
             "andhra": "asset:characters/arjun_andhra_neutral.png", "meghalaya": "asset:characters/arjun_meghalaya_neutral.png"}
REF_NOTE = ("Reference images: the first images show the exact visual style to match (handcrafted paper/clay/wood miniature "
            "diorama, stop-motion photo look, warm light, crumpled-paper sky). {arjun}Match their materials, lighting and "
            "camera feel; do not copy their layout or any text in them. Create this new scene: ")


def resolve(ref):
    if ref.startswith("asset:plates/"):
        name = ref.split("/", 1)[1]
        p = KIT / "assets/plates" / name
        if not p.exists():  # plates may ship packed in sheets; build.plates_dir() unpacks them once
            d = build.plates_dir()
            p = Path(d) / name if d else p
        return p if p.exists() else None
    if ref.startswith("asset:"):
        p = KIT / "assets" / ref.split(":", 1)[1]
        return p if p.exists() else None
    p = Path(ref)
    return p if p.exists() else None


def img_bytes(path, max_side=1024):
    im = Image.open(path)
    im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
    im.thumbnail((max_side, max_side))
    if im.mode == "RGBA":  # flatten cut-outs on white so models see the figure cleanly
        bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[3]); im = bg
    b = io.BytesIO(); im.save(b, "JPEG", quality=88)
    return b.getvalue()


def build_request(key, g, spec):
    prompt, aspect = build.prompt_text(key, g, spec.get("arjun", "city"))
    refs = list(g.get("refs") or DEFAULT_STYLE_REFS)
    has_arjun = g.get("arjun") is not None
    if has_arjun:
        refs.append(ARJUN_REF.get(g.get("arjun") or spec.get("arjun", "city"), ARJUN_REF["city"]))
    paths = [p for p in (resolve(r) for r in refs) if p]
    note = REF_NOTE.format(arjun="The last image is the main character ARJUN: keep his face, block head, cut-paper hair and costume exactly. " if has_arjun else "")
    return {"key": key, "prompt": note + prompt, "aspect": aspect, "refs": [str(p) for p in paths], "cutout": bool(g.get("cutout"))}


# ---------------------------------------------------------------- providers
def _post(url, body, headers, timeout=240):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def gemini(req, key):
    model = os.environ.get("IMG_MODEL", "gemini-2.5-flash-image")
    parts = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img_bytes(p)).decode()}} for p in req["refs"]]
    parts.append({"text": req["prompt"]})
    body = {"contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": req["aspect"]}}}
    data = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                 json.dumps(body).encode(), {"Content-Type": "application/json", "x-goog-api-key": key})
    for c in data.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            d = p.get("inlineData") or p.get("inline_data")
            if d and d.get("data"):
                return base64.b64decode(d["data"])
    raise RuntimeError("no image in Gemini response: " + json.dumps(data)[:400])


def openai(req, key):
    model = os.environ.get("IMG_MODEL", "gpt-image-1")
    size = {"16:9": "1536x1024", "1:1": "1024x1024", "9:16": "1024x1536"}.get(req["aspect"], "1536x1024")
    fields = {"model": model, "prompt": req["prompt"], "size": size, "quality": os.environ.get("IMG_QUALITY", "high"), "n": "1"}
    if req["cutout"]:
        fields["background"] = "transparent"
    bnd = uuid.uuid4().hex
    out = io.BytesIO()
    for k, v in fields.items():
        out.write(f"--{bnd}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    for i, p in enumerate(req["refs"]):
        out.write(f"--{bnd}\r\nContent-Disposition: form-data; name=\"image[]\"; filename=\"ref{i}.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
        out.write(img_bytes(p)); out.write(b"\r\n")
    out.write(f"--{bnd}--\r\n".encode())
    ep = "edits" if req["refs"] else "generations"
    if ep == "generations":  # JSON endpoint
        data = _post("https://api.openai.com/v1/images/generations", json.dumps(fields).encode(),
                     {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    else:
        data = _post("https://api.openai.com/v1/images/edits", out.getvalue(),
                     {"Content-Type": f"multipart/form-data; boundary={bnd}", "Authorization": f"Bearer {key}"})
    return base64.b64decode(data["data"][0]["b64_json"])


PROVIDERS = {"gemini": (gemini, ("GEMINI_API_KEY", "GOOGLE_API_KEY")), "openai": (openai, ("OPENAI_API_KEY",))}


def pick_provider(name):
    order = [name] if name else ["gemini", "openai"]
    for n in order:
        for env in PROVIDERS[n][1]:
            if os.environ.get(env):
                return n, PROVIDERS[n][0], os.environ[env]
    return None, None, None


# ---------------------------------------------------------------- post-processing
def cover(im, w=1920, h=1080):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def remove_white(im, tol=28, floor=205):
    im = im.convert("RGBA")
    if im.getextrema()[3][0] < 250:  # already transparent
        return im
    px, (W, H) = im.load(), im.size
    q, seen = deque(), bytearray(W * H)
    for x in range(W): q.extend(((x, 0), (x, H - 1)))
    for y in range(H): q.extend(((0, y), (W - 1, y)))
    while q:
        x, y = q.popleft()
        if not (0 <= x < W and 0 <= y < H) or seen[y * W + x]:
            continue
        seen[y * W + x] = 1
        r, g, b, a = px[x, y]
        if min(r, g, b) < floor or max(r, g, b) - min(r, g, b) > tol:
            continue
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def save(raw, req, dest):
    im = Image.open(io.BytesIO(raw))
    if req["cutout"]:
        im = remove_white(im)
        im.thumbnail((1920, 1920))
    else:
        im = cover(im.convert("RGB")) if req["aspect"] == "16:9" else im.convert("RGB")
    im.save(dest)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--provider", choices=list(PROVIDERS))
    ap.add_argument("--retries", type=int, default=2)
    a = ap.parse_args()

    spec_path = Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text())
    gen_dir = spec_path.parent / "gen"; gen_dir.mkdir(exist_ok=True)
    used = set()
    import re
    for f in spec["frames"]:
        used |= set(re.findall(r'"gen:([A-Za-z0-9_.-]+)"', json.dumps(f)))
    have = lambda k: any((gen_dir / (k + e)).exists() for e in (".png", ".jpg", ".jpeg", ".webp"))
    only = {k for k in a.only.split(",") if k}
    keys = sorted(k for k in used if k in spec.get("gen", {}) and (k in only if only else (a.force or not have(k))))
    missing = sorted(k for k in used if k not in spec.get("gen", {}))
    if missing:
        print("WARN no prompt in spec['gen'] for:", ", ".join(missing))
    if not keys:
        print("nothing pending"); return

    reqs = [build_request(k, spec["gen"][k], spec) for k in keys]
    if a.dry_run:
        out = gen_dir / "_requests_preview.json"
        out.write_text(json.dumps(reqs, indent=1, ensure_ascii=False))
        print(f"dry run: {len(reqs)} requests -> {out}")
        for r in reqs:
            print(f"  {r['key']:<22} {r['aspect']:<5} refs={len(r['refs'])} cutout={r['cutout']} prompt={len(r['prompt'])} chars")
        return

    name, fn, key = pick_provider(a.provider)
    if not fn:
        sys.exit("No image API key found. Set GEMINI_API_KEY (Google, recommended) or OPENAI_API_KEY, then rerun. "
                 "Use --dry-run to check prompts without a key.")
    print(f"provider: {name} · {len(reqs)} images")
    log = []
    for r in reqs:
        dest = gen_dir / f"{r['key']}.png"
        for attempt in range(a.retries + 1):
            try:
                t0 = time.time()
                save(fn(r, key), r, dest)
                log.append({"key": r["key"], "ok": True, "provider": name, "secs": round(time.time() - t0, 1)})
                print(f"  ok   {r['key']}  ({log[-1]['secs']}s)")
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="ignore")[:300]
                err = f"HTTP {e.code}: {msg}"
                if e.code in (400, 401, 403):  # bad key / blocked prompt: retrying won't help
                    attempt = a.retries
            except Exception as e:  # network, timeout, empty response
                err = str(e)[:300]
            if attempt >= a.retries:
                log.append({"key": r["key"], "ok": False, "error": err})
                print(f"  FAIL {r['key']}: {err}")
                break
            time.sleep(4 * (attempt + 1))
    (gen_dir / "_gen_log.json").write_text(json.dumps(log, indent=1))
    bad = [l["key"] for l in log if not l["ok"]]
    print(f"done: {len(log) - len(bad)} ok, {len(bad)} failed" + (f" ({', '.join(bad)})" if bad else ""))
    print("Next: open each gen/<key>.png, check it against the character bible, rerun with --only <key> --force for misses, then rebuild.")


if __name__ == "__main__":
    main()
