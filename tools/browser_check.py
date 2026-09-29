#!/usr/bin/env python3
"""Chromium checks for the isolated pilot; optional offline in-memory rendering."""
from __future__ import annotations
import argparse
import base64
import functools
import hashlib
import json
import mimetypes
import os
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
PAGES=['index.html','releases/sacrilegium.html','releases/nos-creemos-algo.html']
WIDTHS=[320,390,768,1024,1440,1920]

def embedded(path: str) -> str:
    """Render local source without opening network/file URLs in restricted runtimes.
    Only this QA representation is inlined; published HTML stays unchanged.
    """
    file=ROOT/path;text=file.read_text()
    def uri(p: Path) -> str:
        mime=mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
        return 'data:'+mime+';base64,'+base64.b64encode(p.read_bytes()).decode()
    def css_link(match):
        csspath=(file.parent/match[1]).resolve();css=csspath.read_text()
        css=re.sub(r'url\([\'\"]?([^\)\'\"]+)[\'\"]?\)',lambda m:'url("'+uri((csspath.parent/m[1]).resolve())+'")',css)
        return '<style>'+css+'</style>'
    text=re.sub(r'<link rel="stylesheet" href="([^"]+)">',css_link,text)
    text=re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")',lambda m:m[1]+uri((file.parent/m[2]).resolve())+m[3],text)
    text=re.sub(r'<script src="([^"]+)" defer></script>',lambda m:'<script>'+(file.parent/m[1]).resolve().read_text()+'</script>',text)
    return re.sub(r'<link rel="icon"[^>]*>','',text)

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--memory',action='store_true');p.add_argument('--out',type=Path,default=Path('qa/browser'));args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    server=None;report={'transport':'in-memory' if args.memory else 'http','layout_cases':[],'checks':[],'browser':'Chromium'}
    if not args.memory:
        handler=functools.partial(SimpleHTTPRequestHandler,directory=str(ROOT))
        server=ThreadingHTTPServer(('127.0.0.1',0),handler);threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
    def load(page,path,fragment=''):
        if args.memory:
            page.set_content(embedded(path),wait_until='load')
            if fragment:page.evaluate('(hash)=>{location.hash=hash}',fragment)
        else:page.goto(base+path+fragment,wait_until='networkidle')
        page.evaluate('document.fonts.ready')
    with sync_playwright() as pw:
        options={'headless':True}
        if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):options['executable_path']=os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser=pw.chromium.launch(**options)
        for width in WIDTHS:
            for path in PAGES:
                page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
                errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
                load(page,path)
                for img in page.locator('img').all():
                    img.scroll_into_view_if_needed();img.evaluate("el=>{el.loading='eager'}")
                page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
                page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),(width,path,'horizontal overflow')
                assert page.locator('h1').count()==1,(width,path,'h1')
                assert not errors,errors
                # Artwork remains square in the actual rendered layout, not only metadata.
                for img in page.locator('img').all():
                    box=img.bounding_box();assert abs(box['width']-box['height'])<=1,(width,path,'art ratio')
                if width in (390,1440):
                    page.screenshot(path=str(args.out/f'{Path(path).stem}-{width}.png'),full_page=True)
                report['layout_cases'].append({'page':path,'width':width,'status':'pass','images':page.locator('img').count()})
                page.close()
        page=browser.new_page(viewport={'width':390,'height':844});load(page,'index.html')
        menu=page.locator('.menu-toggle');menu.click();assert menu.get_attribute('aria-expanded')=='true';assert page.locator('#primary-nav').is_visible()
        page.keyboard.press('Escape');assert menu.get_attribute('aria-expanded')=='false';assert page.locator('.menu-toggle').evaluate('el=>el===document.activeElement')
        menu.click()
        if not args.memory:
            page.locator('#primary-nav a').first.click();assert menu.get_attribute('aria-expanded')=='false'
        else:page.keyboard.press('Escape')
        report['checks'].append('Mobile menu opens, closes, and restores keyboard focus')
        for kind,count in [('album',2),('single',5),('all',7)]:
            page.locator(f'[data-filter="{kind}"]').click();assert page.locator('[data-release]:visible').count()==count
        report['checks'].append('Catalog filters show 2 albums, 5 singles, and all 7 releases')
        field=page.locator('[data-cosmic-field]');field.scroll_into_view_if_needed();page.wait_for_timeout(200)
        pause=page.locator('[data-motion-toggle]');pause.click();page.wait_for_timeout(100)
        get_canvas=lambda:page.locator('canvas').evaluate('canvas=>canvas.toDataURL()')
        still=get_canvas();page.wait_for_timeout(200);assert still==get_canvas();assert pause.get_attribute('aria-pressed')=='true'
        page.locator('[data-cosmic-mode="1"]').click();page.wait_for_timeout(100);assert get_canvas()!=still;assert pause.get_attribute('aria-pressed')=='true'
        field.focus();page.keyboard.press('ArrowRight');assert page.locator('[data-cosmic-mode="2"]').get_attribute('aria-pressed')=='true'
        pause.click();page.wait_for_timeout(100);moving=get_canvas();page.wait_for_timeout(200);assert moving!=get_canvas()
        page.emulate_media(reduced_motion='reduce');page.wait_for_timeout(100);still=get_canvas();page.wait_for_timeout(200);assert still==get_canvas();assert pause.is_disabled()
        report['checks'].append('Field animation, pause/resume, paused mode changes, keyboard modes, and reduced motion')
        page.close()
        for path,anchor in [('releases/sacrilegium.html','#track-01-hollow-show'),('releases/nos-creemos-algo.html','#track-01-nos-creemos-algo')]:
            page=browser.new_page(viewport={'width':390,'height':844});load(page,path,anchor);page.wait_for_timeout(100)
            assert page.locator(anchor+' details').get_attribute('open') is not None
            page.locator(anchor+' summary').click();assert page.locator(anchor+' details').get_attribute('open') is None;page.close()
        report['checks'].append('Direct lyric fragments open the correct native disclosure and remain collapsible')
        for path in PAGES:
            context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});page=context.new_page()
            if args.memory:page.set_content(embedded(path),wait_until='load')
            else:page.goto(base+path,wait_until='load')
            assert page.locator('#primary-nav').is_visible();assert page.locator('h1').is_visible()
            if path=='index.html':assert page.locator('[data-release]').count()==7;assert not page.locator('.filters').is_visible()
            else:
                summary=page.locator('summary').first;summary.scroll_into_view_if_needed();summary.click();assert page.locator('details').first.get_attribute('open') is not None
            context.close()
        report['checks'].append('Navigation, catalog, and native lyrics remain usable without JavaScript')
        browser.close()
    if server:server.shutdown()
    report['status']='pass';(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
