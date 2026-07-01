#!/usr/bin/env python3
"""Install the FaXto musical-note favicon across all static pages."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="FaXto musical notes">
  <rect width="64" height="64" rx="13" fill="#09090B"/>
  <path d="M27 14v30M48 9v30M27 14l21-5" fill="none" stroke="#C6A04A" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
  <ellipse cx="20" cy="45" rx="9" ry="7" transform="rotate(-18 20 45)" fill="#C6A04A"/>
  <ellipse cx="41" cy="40" rx="9" ry="7" transform="rotate(-18 41 40)" fill="#C6A04A"/>
</svg>
'''
(ROOT / "favicon.svg").write_text(favicon, encoding="utf-8")

pages = [
    (ROOT / "index.html", "favicon.svg"),
    (ROOT / "disclosure.html", "favicon.svg"),
    (ROOT / "releases" / "singularity.html", "../favicon.svg"),
    (ROOT / "releases" / "sacrilegium.html", "../favicon.svg"),
    (ROOT / "releases" / "deluded.html", "../favicon.svg"),
    (ROOT / "releases" / "both-sides.html", "../favicon.svg"),
    (ROOT / "releases" / "hymns.html", "../favicon.svg"),
    (ROOT / "releases" / "heresy-parade.html", "../favicon.svg"),
]

for page, href in pages:
    html = page.read_text(encoding="utf-8")
    if 'rel="icon"' in html:
        continue
    tag = f'<link href="{href}" rel="icon" type="image/svg+xml"/>'
    marker = '<link href="https://fonts.googleapis.com" rel="preconnect"/>'
    if marker not in html:
        raise RuntimeError(f"Could not find insertion point in {page}")
    html = html.replace(marker, f'{tag}\n{marker}', 1)
    page.write_text(html, encoding="utf-8")

for obsolete in (
    ROOT / "scripts" / "add_favicon.py",
    ROOT / ".github" / "workflows" / "add-favicon.yml",
):
    if obsolete.exists():
        obsolete.unlink()

print("Installed the FaXto favicon on eight pages.")
