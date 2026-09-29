#!/usr/bin/env python3
"""Generate the pilot's static HTML. No dependencies, network, or deployment.

content/site.json controls branding and the deliberately chosen featured record.
content/releases.json controls catalog entries; only page_mode=pilot pages are rebuilt.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)

def local_path(value: str) -> str:
    p = Path(value)
    if not value or p.is_absolute() or '..' in p.parts or '\\' in value or urlsplit(value).scheme:
        raise ValueError(f'Expected a relative repository path: {value!r}')
    if not (ROOT / p).is_file():
        raise ValueError(f'Missing local asset: {value}')
    return value

def https_url(value: str) -> str:
    u = urlsplit(value)
    if u.scheme != 'https' or not u.hostname or u.username or u.password or any(c in value for c in '\r\n'):
        raise ValueError(f'Expected a public HTTPS URL: {value!r}')
    return value

def track_id(track: dict) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', track['title'].lower()).strip('-')
    return f"track-{track['number']:02d}-{slug or 'untitled'}"

def editorial_hash(record: dict) -> str:
    value = {'tracks': record['tracks'], 'story': record['story']}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def load_content() -> tuple[dict, list[dict]]:
    site = json.loads((ROOT / 'content/site.json').read_text())
    catalog = json.loads((ROOT / 'content/releases.json').read_text())
    if site['schema_version'] != 1 or catalog['schema_version'] != 1:
        raise ValueError('Unsupported content schema')
    if not isinstance(site['preview'], bool):
        raise ValueError('Preview mode must be explicit')
    https_url(site['production_url'])
    for key in ('wordmark', 'symbol'):
        if site['brand'].get(key): local_path(site['brand'][key])
    records = catalog['releases']
    slugs = set()
    for r in records:
        slug = r['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or slug in slugs:
            raise ValueError('Invalid or duplicate release slug')
        slugs.add(slug)
        if r['artist'] != site['brand']['name'] or r['kind'] not in ('album', 'single'):
            raise ValueError(f'Unmatched artist or release kind: {slug}')
        if r['approval'] not in ('approved', 'approved-existing-content'):
            raise ValueError(f'Release is not approved: {slug}')
        https_url(r['listen_url'])
        local_path(r['artwork']['path'])
        if r['artwork']['width'] != r['artwork']['height']:
            raise ValueError(f'Artwork must retain its square framing: {slug}')
        if r['page_mode'] not in ('legacy', 'pilot'):
            raise ValueError(f'Unknown page mode: {slug}')
        if r['page_mode'] == 'pilot':
            if len(r['tracks']) != r['track_count'] or not r['tracks']:
                raise ValueError(f'Incomplete tracklist: {slug}')
            if [t['number'] for t in r['tracks']] != list(range(1, r['track_count'] + 1)):
                raise ValueError(f'Unexpected track order: {slug}')
            if r['approval'] == 'approved-existing-content' and editorial_hash(r) != r['provenance']['editorial_sha256']:
                raise ValueError(f'Approved lyrics or story changed: {slug}')
        else:
            local_path(f'releases/{slug}.html')
    if site['featured'] not in slugs:
        raise ValueError('The editorially selected featured release is missing')
    if site.get('secondary_featured') and site['secondary_featured'] not in slugs:
        raise ValueError('The secondary editorial selection is missing')
    return site, records

def brand_markup(site: dict, prefix: str) -> str:
    b = site['brand']; name = esc(b['name']); parts = []
    if b.get('symbol'):
        parts.append(f'<img class="brand-symbol" src="{esc(prefix+b["symbol"])}" alt="" aria-hidden="true">')
    if b.get('wordmark'):
        parts.append(f'<img class="brand-wordmark" src="{esc(prefix+b["wordmark"])}" alt="{name}">')
    else:
        parts.append(f'<span class="brand-text">{name}</span>')
    return ''.join(parts)

def shared(site: dict, prefix: str) -> dict:
    preview = ''
    if site['preview']:
        preview = f'<div class="preview-strip"><strong>DESIGN STUDY 01</strong><span>Preview only · live site unchanged</span><a href="{esc(site["production_url"])}" target="_blank" rel="noopener">Current site ↗<span class="sr-only">, opens a new tab</span></a></div>'
    header = f'''<header class="masthead"><div class="header-inner shell"><a class="brand" href="{prefix}index.html" aria-label="FaXto home">{brand_markup(site,prefix)}<span class="brand-note" aria-hidden="true">Experimental music<br>Absurdist liturgy</span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">Menu</button><nav id="primary-nav" class="main-nav" aria-label="Primary navigation"><a href="{prefix}index.html#catalog">Music</a><a href="{prefix}index.html#invocation">About</a><a class="nav-listen" href="{prefix}links.html">Listen / Follow <span aria-hidden="true">↗</span></a></nav></div></header>'''
    footer_brand = (f'<img class="brand-wordmark" src="{esc(prefix+site["brand"]["wordmark"])}" alt="{esc(site["brand"]["name"])}">' if site['brand'].get('wordmark') else esc(site['brand']['name']))
    footer = f'''<footer class="site-footer shell"><div class="footer-top"><a class="footer-brand" href="{prefix}index.html" aria-label="FaXto home">{footer_brand}</a><p class="footer-tagline">{esc(site['brand']['footer_line'])}</p></div><div class="footer-bottom"><nav aria-label="Footer navigation"><a href="mailto:{esc(site['contact'])}">Contact</a><a href="{prefix}links.html">Listen / Follow</a><a href="{prefix}disclosure.html">made with Suno AI</a></nav><span>© 2026 FaXto</span></div></footer>'''
    return {'preview': preview, 'header': header, 'footer': footer}

def head(site: dict, prefix: str, title: str, description: str, image: str, path: str) -> str:
    canonical = site['production_url'].rstrip('/') + '/' + path
    image_url = site['production_url'].rstrip('/') + '/' + image
    robots = '<meta name="robots" content="noindex, nofollow">' if site['preview'] else ''
    return f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#0c0c0b">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">{robots}
<link rel="canonical" href="{esc(canonical)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:image" content="{esc(image_url)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:type" content="website"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}css/brand.css"><link rel="stylesheet" href="{prefix}css/pilot.css">'''

def card(r: dict) -> str:
    page = f'releases/{r["slug"]}.html'; art = r['artwork']
    return f'''<article class="release-card" data-release="{esc(r['slug'])}" data-kind="{r['kind']}"><a class="card-art" href="{page}" aria-label="Explore {esc(r['title'])}"><img src="{esc(art['path'])}" alt="{esc(art['alt'])}" width="{art['width']}" height="{art['height']}" loading="lazy" decoding="async"></a><p class="card-label eyebrow"><span>{r['kind']}</span><span>{esc(r['catalog_id'])}</span></p><h3><a href="{page}">{esc(r['title'])}</a></h3><p class="card-description">{esc(r['summary'])}</p><div class="card-actions"><a href="{page}">Explore <span aria-hidden="true">→</span><span class="sr-only"> {esc(r['title'])}</span></a><a href="{esc(r['listen_url'])}" target="_blank" rel="noopener"><span><span aria-hidden="true">𝄞𝄢</span> Listen</span><span aria-hidden="true">↗</span><span class="sr-only"> to {esc(r['title'])} via LANDR, opens a new tab</span></a></div></article>'''

def render_home(site: dict, records: list[dict]) -> str:
    featured = next(r for r in records if r['slug'] == site['featured'])
    albums = sorted([r for r in records if r['kind'] == 'album'], key=lambda r:r['slug'] != site['featured'])
    singles = [r for r in records if r['kind'] == 'single']
    data = shared(site, '')
    data.update(head=head(site,'','FaXto — '+site['brand']['tagline'],'FaXto is an experimental absurdist music project. Explore the records, lyrics and stories.',featured['artwork']['path'],''), featured_title=esc(featured['title']), featured_id=esc(featured['catalog_id']), featured_count=featured['track_count'], featured_thesis=esc(featured['blurb']), featured_listen=esc(featured['listen_url']), featured_page=f'releases/{featured["slug"]}.html', featured_art=esc(featured['artwork']['path']), featured_alt=esc(featured['artwork']['alt']), featured_width=featured['artwork']['width'], featured_height=featured['artwork']['height'], tagline=esc(site['brand']['tagline']), catalog_counts=f'{len(albums):02d} albums / {len(singles):02d} singles', total_count=len(records), albums='\n'.join(map(card,albums)), singles='\n'.join(map(card,singles)))
    secondary = next((r for r in records if r['slug'] == site.get('secondary_featured')), None)
    data['secondary_record'] = (f'<a class="also-out" href="releases/{esc(secondary["slug"])}.html"><span class="eyebrow">Also in the catalog</span><span>{esc(secondary["title"])} <span aria-hidden="true">↗</span></span></a>' if secondary else '')
    data['featured_kind'] = featured['kind']
    data['featured_track_label'] = 'movements' if featured['kind'] == 'album' else 'track'
    inv = site['invocation']; method = site['method']
    data.update(invocation_heading=esc(inv['heading']), invocation_emphasis=esc(inv['emphasis']), invocation_body=esc(inv['body']), tenets=''.join(f'<article><span class="eyebrow">{i:02d}</span><h3>{esc(t["title"])}</h3><p>{esc(t["body"])}</p></article>' for i,t in enumerate(inv['tenets'],1)), method_heading=esc(method['heading']), method_emphasis=esc(method['emphasis']), method_body=esc(method['body']))
    return Template((ROOT/'templates/home.html').read_text()).substitute(data)

def render_release(site: dict, r: dict, records: list[dict]) -> str:
    data = shared(site, '../'); art = r['artwork']; pos = records.index(r)
    tracks = []
    for t in r['tracks']:
        anchor = track_id(t)
        tracks.append(f'''<li id="{anchor}"><details><summary><span class="track-number">{t['number']:02d}</span><span class="track-name">{esc(t['title'])}</span><span class="track-hint">Lyrics</span></summary><div class="lyrics" lang="{esc(r['language'])}">{esc(t['lyrics'])}</div><a class="track-permalink" href="#{anchor}">Link to this track <span aria-hidden="true">↗</span></a></details></li>''')
    def neighbor(other: dict, direction: str) -> str:
        label = '← Previous record' if direction == 'previous' else 'Next record →'
        return f'<a href="{esc(other["slug"])}.html"><span class="eyebrow">{label}</span><strong>{esc(other["title"])}</strong></a>'
    structured = {'@context':'https://schema.org','@type':'MusicAlbum','name':r['title'],'byArtist':{'@type':'MusicGroup','name':r['artist']},'numTracks':r['track_count'],'image':site['production_url'].rstrip('/')+'/'+art['path'],'track':[{'@type':'MusicRecording','name':t['title'],'position':t['number']} for t in r['tracks']]}
    metadata = head(site,'../','FaXto — '+r['title'],r['title']+' by FaXto — '+r['blurb'],art['path'],f'releases/{r["slug"]}.html')
    metadata += '\n<script type="application/ld+json">'+json.dumps(structured, ensure_ascii=False).replace('<','\\u003c')+'</script>'
    data.update(head=metadata,catalog_id=esc(r['catalog_id']),kind_label=r['kind'].capitalize(),track_count=r['track_count'],track_label=('movements' if r['kind']=='album' else 'track'),title=esc(r['title']),blurb=esc(r['blurb']),language=r['language'],art=esc(art['path']),alt=esc(art['alt']),width=art['width'],height=art['height'],listen=esc(r['listen_url']),tracks='\n'.join(tracks),story='\n'.join('<p>'+esc(p)+'</p>' for p in r['story']),previous=neighbor(records[(pos-1)%len(records)],'previous'),next=neighbor(records[(pos+1)%len(records)],'next'))
    return Template((ROOT/'templates/release.html').read_text()).substitute(data)

def outputs() -> dict[str,str]:
    site, records = load_content()
    result = {'index.html':render_home(site,records)}
    for r in records:
        if r['page_mode'] == 'pilot': result[f'releases/{r["slug"]}.html'] = render_release(site,r,records)
    return result

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Fail if generated HTML differs; do not write files')
    args=parser.parse_args(); changed=[]
    for path,text in outputs().items():
        target=ROOT/path
        if not target.exists() or target.read_text()!=text:
            changed.append(path)
            if not args.check: target.write_text(text,encoding='utf-8')
    if args.check and changed:
        print('Stale generated pages: '+', '.join(changed)); return 1
    print(('Verified' if args.check else 'Generated')+' static pilot pages; no deployment performed.')
    return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,KeyError,json.JSONDecodeError) as error:
        raise SystemExit(f'Content validation failed: {error}')
