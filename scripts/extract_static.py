#!/usr/bin/env python3
"""Convert the exported single-file FaXto bundle into a normal static site."""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "index.html"
ASSETS = ROOT / "assets"

MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "font/woff": ".woff",
    "font/woff2": ".woff2",
    "application/font-woff": ".woff",
    "application/javascript": ".js",
    "text/javascript": ".js",
    "text/css": ".css",
}

FRIENDLY_NAMES = {
    "4a79a1a1-eea1-44cb-8319-5da65d88022e": "singularity.jpg",
    "35d0c61b-258d-467a-a808-c4c344cf8ce2": "sacrilegium.jpg",
    "b3576a5f-e1d1-47cf-9e34-82d57a348429": "deluded.jpg",
    "b14f3e40-26ed-41eb-b1d0-16f6c50627cd": "both-sides.jpg",
    "645fe1e5-b356-48b2-9e6e-d6a984963a78": "hymns.jpg",
    "2f36a466-c22b-4016-8a67-4cb53b9be74b": "heresy-parade.jpg",
}


def extract_script_payload(source: str, script_type: str) -> str:
    pattern = rf'<script\s+type="{re.escape(script_type)}"\s*>\s*(.*?)\s*</script>'
    match = re.search(pattern, source, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        raise RuntimeError(f"Could not find {script_type!r} payload")
    return match.group(1)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    manifest = json.loads(extract_script_payload(source, "__bundler/manifest"))
    template = json.loads(extract_script_payload(source, "__bundler/template"))

    ASSETS.mkdir(exist_ok=True)
    replacements: dict[str, str] = {}

    for asset_id, entry in manifest.items():
        mime = entry.get("mime", "application/octet-stream")
        raw = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            raw = gzip.decompress(raw)

        # The exported runtime JavaScript is no longer needed after flattening.
        if mime in {"application/javascript", "text/javascript"}:
            continue

        filename = FRIENDLY_NAMES.get(asset_id)
        if not filename:
            filename = f"{asset_id}{MIME_EXTENSIONS.get(mime, '.bin')}"

        (ASSETS / filename).write_bytes(raw)
        replacements[asset_id] = f"assets/{filename}"

    for asset_id, path in replacements.items():
        template = template.replace(asset_id, path)

    helmet_match = re.search(r"<helmet>(.*?)</helmet>", template, flags=re.DOTALL | re.IGNORECASE)
    xdc_match = re.search(r"<x-dc>(.*?)</x-dc>", template, flags=re.DOTALL | re.IGNORECASE)
    if not helmet_match or not xdc_match:
        raise RuntimeError("Could not locate the exported page markup")

    helmet = helmet_match.group(1)
    styles = re.findall(r"<style[^>]*>(.*?)</style>", helmet, flags=re.DOTALL | re.IGNORECASE)
    stylesheet = "\n\n".join(style.strip() for style in styles).strip() + "\n"

    body = re.sub(
        r"<helmet>.*?</helmet>",
        "",
        xdc_match.group(1),
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()

    body = re.sub(
        r'<img class="cover"',
        '<img class="cover" width="132" height="132" loading="lazy" decoding="async"',
        body,
    )
    body = re.sub(
        r'<img class="single-cover"',
        '<img class="single-cover" width="78" height="78" loading="lazy" decoding="async"',
        body,
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FaXto</title>
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
</head>
<body>
{body}
</body>
</html>
'''

    script = '''document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", () => {
  const items = document.querySelectorAll(".reveal");
  const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  if (reduceMotion || !("IntersectionObserver" in window)) {
    items.forEach((item) => item.classList.add("in"));
    return;
  }

  const inView = (element) => {
    const rect = element.getBoundingClientRect();
    return rect.top < window.innerHeight && rect.bottom > 0;
  };

  items.forEach((item) => {
    if (inView(item)) item.classList.add("in");
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
  );

  items.forEach((item) => observer.observe(item));
});
'''

    (ROOT / "styles.css").write_text(stylesheet, encoding="utf-8")
    (ROOT / "script.js").write_text(script, encoding="utf-8")
    SOURCE.write_text(html, encoding="utf-8")
    (ROOT / ".nojekyll").touch()

    print(f"Extracted {len(replacements)} assets and rebuilt the static site.")


if __name__ == "__main__":
    main()
