import copy
import hashlib
import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
build=module('build','tools/build_site.py');imports=module('imports','tools/import_release.py')

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True);self.tags=[];self.ids=[];self.lyrics=[];self.stories=[];self._capture=None;self._depth=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if 'id'in a:self.ids.append(a['id'])
        if tag=='div' and a.get('class')=='lyrics':self._capture=[];self._depth=1
        elif self._capture is not None and tag not in ('br','img','meta','link','input'):self._depth+=1
    def handle_endtag(self,tag):
        if self._capture is not None:
            self._depth-=1
            if self._depth==0:self.lyrics.append(''.join(self._capture));self._capture=None
    def handle_data(self,data):
        if self._capture is not None:self._capture.append(data)
    def attrs(self,tag):return [a for t,a in self.tags if t==tag]

class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.site,cls.records=build.load_content();cls.pages=build.outputs()
    def test_generated_pages_are_current(self):
        for path,text in self.pages.items():self.assertEqual((ROOT/path).read_text(),text,path)
    def test_catalog_contains_all_seven_existing_releases(self):
        doc=Document(self.pages['index.html']);cards=[a['data-release'] for a in doc.attrs('article') if 'data-release'in a]
        self.assertEqual(set(cards),{r['slug'] for r in self.records});self.assertEqual(len(cards),7)
    def test_two_pilot_release_pages_only(self):
        self.assertEqual(set(self.pages),{'index.html','releases/sacrilegium.html','releases/nos-creemos-algo.html'})
    def test_approved_editorial_hashes_unchanged(self):
        for r in self.records:
            if r['page_mode']=='pilot':self.assertEqual(build.editorial_hash(r),r['provenance']['editorial_sha256'])
    def test_generated_lyrics_are_verbatim(self):
        for r in self.records:
            if r['page_mode']=='pilot':self.assertEqual(Document(self.pages[f'releases/{r["slug"]}.html']).lyrics,[t['lyrics'] for t in r['tracks']])
    def test_legacy_pages_byte_identical(self):
        for r in self.records:
            if r['page_mode']=='legacy':self.assertEqual(hashlib.sha256((ROOT/f'releases/{r["slug"]}.html').read_bytes()).hexdigest(),r['provenance']['source_sha256'])
    def test_original_artwork_blobs_unchanged(self):
        original={'sacrilegium':'9c838818f7e43902269ffb8221c791e675f567c8','singularity':'aa27ba4457ba29354e73a11b0961ec8d46d11cee','deluded':'61a2aa406e2e334f118be4335ec1f61a5db8011a','both-sides':'e39a9820ff97ad99649f2715b4d818c1830dc8e9','hymns':'c6f69059645e1dec2866750b483286c2e922201f','heresy-parade':'53c0e1a2f8e6c2472e98c2d3181332161d7bc29f','nos-creemos-algo':'a32bd4b2d1280eeaa8dc5a2f033237fa7078f777'}
        for slug,expected in original.items():
            data=(ROOT/f'assets/{slug}.jpg').read_bytes();actual=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest();self.assertEqual(actual,expected)
    def test_landmarks_unique_ids_and_image_descriptions(self):
        for text in self.pages.values():
            doc=Document(text);self.assertEqual(len(doc.attrs('h1')),1);self.assertEqual(len(doc.attrs('main')),1);self.assertEqual(len(doc.ids),len(set(doc.ids)))
            for img in doc.attrs('img'):self.assertTrue(img.get('alt'));self.assertEqual(img.get('width'),img.get('height'))
    def test_internal_links_and_fragments_resolve(self):
        for path,text in self.pages.items():
            for tag,a in Document(text).tags:
                value=a.get('href') if tag in ('a','link') else a.get('src') if tag in ('img','script') else None
                if not value:continue
                url=urlsplit(value)
                if url.scheme or url.netloc:continue
                target=(ROOT/path).parent/unquote(url.path) if url.path else ROOT/path
                self.assertTrue(target.resolve().is_relative_to(ROOT),value);self.assertTrue(target.is_file(),str(target))
                if url.fragment:self.assertIn(unquote(url.fragment),Document(target.read_text()).ids,(path,value))
    def test_external_links_are_https_and_noopener(self):
        for text in self.pages.values():
            for a in Document(text).attrs('a'):
                u=urlsplit(a.get('href',''))
                if u.netloc:self.assertEqual(u.scheme,'https')
                if a.get('target')=='_blank':self.assertIn('noopener',a.get('rel',''))
    def test_only_one_disclosure_entry_per_page(self):
        for text in self.pages.values():self.assertEqual(sum(a.get('href','').endswith('disclosure.html') for a in Document(text).attrs('a')),1)
    def test_preview_is_noindex(self):
        self.assertTrue(self.site['preview'])
        for text in self.pages.values():self.assertIn('noindex, nofollow',text);self.assertIn('live site unchanged',text)
    def test_nos_has_artist_supplied_landr_url(self):
        r=next(r for r in self.records if r['slug']=='nos-creemos-algo');self.assertEqual(r['listen_url'],'https://release.landr.com/nos-creemos-algo');self.assertIn(r['listen_url'],self.pages['releases/nos-creemos-algo.html'])
    def test_no_autoplay_or_external_runtime_dependencies(self):
        for text in self.pages.values():
            doc=Document(text);self.assertFalse(doc.attrs('audio'));self.assertFalse(doc.attrs('iframe'))
            for tag in ('script','link'):
                for a in doc.attrs(tag):
                    value=a.get('src') if tag=='script' else a.get('href') if a.get('rel')=='stylesheet' else None
                    if value:self.assertFalse(urlsplit(value).scheme)
    def test_escape_external_text(self):self.assertEqual(build.esc('<script>"&'), '&lt;script&gt;&quot;&amp;')

class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.meta=json.loads((ROOT/'content/imports/nos-creemos-algo.json').read_text())
    def test_verified_one_track_candidate(self):
        x=imports.candidate(self.meta['landr_url'],'nos-creemos-algo','Nos Creemos Algo','FaXto',self.meta)
        self.assertEqual(x['track_count'],1);self.assertEqual(x['tracks'][0]['isrc'],'CAGOO2664363');self.assertEqual(x['approval'],'pending');self.assertNotIn('lyrics',x['tracks'][0])
    def test_rejects_similar_artist(self):
        x=copy.deepcopy(self.meta);x['artistName']='Fato'
        with self.assertRaises(ValueError):imports.verify_metadata(x,'FaXto','Nos Creemos Algo')
    def test_rejects_wrong_title(self):
        with self.assertRaises(ValueError):imports.verify_metadata(self.meta,'FaXto','Another Release')
    def test_rejects_incomplete_pagination(self):
        x=copy.deepcopy(self.meta);x['trackCount']=7
        with self.assertRaises(ValueError):imports.verify_metadata(x,'FaXto','Nos Creemos Algo')
    def test_rejects_unreleased_content(self):
        x=copy.deepcopy(self.meta);x['isPrerelease']=True
        with self.assertRaises(ValueError):imports.verify_metadata(x,'FaXto','Nos Creemos Algo')
    def test_rejects_unsafe_source_urls(self):
        for url in ['http://release.landr.com/test','https://localhost/test','https://release.landr.com.evil.example/test','https://user:pass@release.landr.com/test','https://release.landr.com:8080/test']:
            with self.assertRaises(ValueError):imports.validate_landr_url(url)
    def test_link_only_is_incomplete_not_fabricated(self):
        x=imports.candidate(self.meta['landr_url'],'nos-creemos-algo','Nos Creemos Algo','FaXto')
        self.assertIn('verified complete release metadata',x['missing']);self.assertEqual(x['approval'],'pending');self.assertNotIn('tracks',x)
    def test_scraped_links_remain_unverified(self):
        markup='<a href="https://open.spotify.com/album/example">Listen</a><a href="javascript:alert(1)">bad</a><script>throw Error("do not execute")</script>'
        x=imports.candidate(self.meta['landr_url'],'nos-creemos-algo','Nos Creemos Algo','FaXto',promo_html=markup)
        self.assertEqual(x['store_link_candidates'],['https://open.spotify.com/album/example']);self.assertEqual(x['approval'],'pending')
    def test_rejects_duplicate_track_positions(self):
        x=copy.deepcopy(self.meta);x['tracks']*=2;x['trackCount']=2
        with self.assertRaises(ValueError):imports.verify_metadata(x,'FaXto','Nos Creemos Algo')

if __name__=='__main__':unittest.main()
