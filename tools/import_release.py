#!/usr/bin/env python3
"""Prepare a review-only release candidate from a LANDR link and optional metadata.

This tool never edits the catalog, downloads cover art, imports lyrics, or deploys.
LANDR's public markup may change. A missing or incomplete source remains a draft.
"""
from __future__ import annotations
import argparse
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

LANDR_HOSTS = {'release.landr.com', 'artists.landr.com'}
STORE_HOSTS = {'music.apple.com','open.spotify.com','music.youtube.com','www.youtube.com','youtube.com','tidal.com','listen.tidal.com','music.amazon.com','music.amazon.co.uk','audiomack.com','www.iheart.com','iheart.com','www.deezer.com','deezer.com'}
MAX_BYTES = 2_000_000

def norm(value: str) -> str:
    text = unicodedata.normalize('NFKC', value).casefold().strip()
    text = re.sub(r'\s*[-–—]\s*single\s*$', '', text)
    return ' '.join(text.split())

def validate_landr_url(value: str) -> str:
    u = urlsplit(value)
    if u.scheme != 'https' or u.hostname not in LANDR_HOSTS or u.username or u.password or u.port not in (None,443) or not u.path.strip('/') or any(x in value for x in '\r\n'):
        raise ValueError('Use an HTTPS release.landr.com or artists.landr.com release link.')
    return value

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def fetch_landr(url: str) -> str:
    """Fetch only explicitly allowed LANDR hosts; do not follow arbitrary redirects."""
    opener = build_opener(NoRedirect())
    for _ in range(5):
        validate_landr_url(url)
        try:
            with opener.open(Request(url, headers={'User-Agent':'FaXto-Release-Review/1.0','Accept':'text/html'}), timeout=20) as response:
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES: raise ValueError('LANDR response exceeds the review size limit.')
                if 'text/html' not in response.headers.get('Content-Type',''):
                    raise ValueError('LANDR did not return an HTML page.')
                return raw.decode('utf-8', errors='replace')
        except HTTPError as error:
            if error.code not in (301,302,303,307,308): raise
            url = urljoin(url, error.headers.get('Location',''))
    raise ValueError('Too many LANDR redirects.')

class PromoParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}; self.links = []; self.structured = []; self._json = None
    def handle_starttag(self,tag,attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('property','').startswith('og:'):
            self.meta[a['property']] = a.get('content','')
        if tag == 'a':
            url = a.get('href',''); u = urlsplit(url)
            if u.scheme == 'https' and u.hostname in STORE_HOSTS and not u.username and not u.password:
                self.links.append(url)
        if tag == 'script' and a.get('type') == 'application/ld+json': self._json = []
    def handle_data(self,data):
        if self._json is not None: self._json.append(data)
    def handle_endtag(self,tag):
        if tag == 'script' and self._json is not None:
            try: self.structured.append(json.loads(''.join(self._json)))
            except json.JSONDecodeError: pass
            self._json = None

def verify_metadata(metadata: dict, artist: str, title: str) -> dict:
    if norm(metadata.get('artistName','')) != norm(artist) or norm(metadata.get('name','')) != norm(title):
        raise ValueError('Metadata does not match the requested artist and release title.')
    tracks = metadata.get('tracks',[])
    count = metadata.get('trackCount')
    if not isinstance(count,int) or count < 1 or len(tracks) != count:
        raise ValueError('Incomplete tracklist: retrieve every track before importing.')
    if metadata.get('isPrerelease') or metadata.get('isComplete') is False:
        raise ValueError('This metadata does not describe a complete live release.')
    identities = []
    for t in tracks:
        if norm(t.get('artistName',artist)) != norm(artist) or not t.get('name'):
            raise ValueError('A track does not match the requested artist.')
        disc, track = t.get('discNumber',1), t.get('trackNumber')
        if not isinstance(disc,int) or not isinstance(track,int) or disc < 1 or track < 1:
            raise ValueError('Track numbering is missing or invalid.')
        identities.append((disc,track))
    if len(set(identities)) != len(identities) or identities != sorted(identities):
        raise ValueError('Duplicate or unordered track numbers.')
    for disc in set(d for d,t in identities):
        numbers = [t for d,t in identities if d == disc]
        if numbers != list(range(1,len(numbers)+1)): raise ValueError('A disc has missing tracks.')
    return {'artist':artist,'title':title,'kind':'single' if metadata.get('isSingle') else 'album','track_count':count,'release_date':metadata.get('releaseDate'),'identifiers':{'upc':metadata.get('upc'),'apple_album_id':metadata.get('album_id')},'artwork_candidate':metadata.get('artwork'),'tracks':[{'number':t['trackNumber'],'disc':t.get('discNumber',1),'title':t['name'],'isrc':t.get('isrc'),'duration_ms':t.get('durationInMillis')} for t in tracks]}

def candidate(landr_url: str, slug: str, title: str, artist: str, metadata: dict | None = None, promo_html: str | None = None) -> dict:
    validate_landr_url(landr_url)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug): raise ValueError('Invalid release slug.')
    result = {'schema_version':1,'slug':slug,'approval':'pending','listen_url':landr_url,'artist':artist,'title':title,'missing':['rights-approved local artwork','artist identity/edition review','editorial approval'],'notes':['No existing content has been overwritten. Lyrics and personal commentary are not imported.'],'store_link_candidates':[]}
    if metadata is not None:
        result.update(verify_metadata(metadata,artist,title))
        result['source'] = {'type':metadata.get('source_type','supplied structured metadata'),'url':metadata.get('url'),'retrieved_date':metadata.get('retrieved_date')}
        result['notes'].append('Title, artist and complete track count match. This does not substitute for artist-profile or identifier review.')
    else:
        result['missing'].append('verified complete release metadata')
    if promo_html:
        parser = PromoParser(); parser.feed(promo_html)
        result['promo_metadata_candidates'] = parser.meta
        result['store_link_candidates'] = sorted(set(parser.links))
        result['notes'].append('Promo metadata and store links are unverified candidates, not approved release destinations.')
    return result

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--landr-url',required=True);p.add_argument('--slug',required=True);p.add_argument('--title',required=True);p.add_argument('--artist',default='FaXto');p.add_argument('--metadata',type=Path);p.add_argument('--offline',action='store_true');p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    validate_landr_url(args.landr_url)
    if args.out.exists(): raise ValueError('Output already exists; candidates never overwrite files.')
    root=Path(__file__).resolve().parents[1];out=args.out.resolve()
    if out.is_relative_to(root) and not out.is_relative_to(root/'content/imports'):
        raise ValueError('Inside the repository, write candidates only under content/imports/.')
    metadata=json.loads(args.metadata.read_text()) if args.metadata else None
    promo=None; fetch_error=None
    if not args.offline:
        try: promo=fetch_landr(args.landr_url)
        except (ValueError,URLError,TimeoutError) as error: fetch_error=str(error)
    draft=candidate(args.landr_url,args.slug,args.title,args.artist,metadata,promo)
    draft['landr_fetch']={'status':'offline' if args.offline else ('retrieved' if promo else 'unavailable'),'error':fetch_error}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as handle: json.dump(draft,handle,ensure_ascii=False,indent=2);handle.write('\n')
    print('Prepared a review-only candidate: '+str(args.out));return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,KeyError,json.JSONDecodeError,OSError) as error: raise SystemExit(f'Import stopped safely: {error}')
