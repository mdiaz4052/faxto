#!/usr/bin/env python3
"""Compare public preview responses with this commit. Never deploys or changes DNS."""
import argparse,hashlib,json,re,time
from pathlib import Path
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--sha',required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.sha):raise SystemExit('Expected a full immutable commit SHA')
    base=f'https://raw.githack.com/mdiaz4052/faxto/{args.sha}/';results=[]
    for path in ['index.html','css/brand.css','css/pilot.css','js/pilot.js','js/pilot-field.js','assets/sacrilegium.jpg','releases/sacrilegium.html','releases/nos-creemos-algo.html']:
        expected=hashlib.sha256((ROOT/path).read_bytes()).hexdigest();item={'path':path,'url':base+path}
        for attempt in range(3):
            try:
                with urlopen(Request(base+path,headers={'User-Agent':'FaXto-Preview-Check/1.0'}),timeout=25) as response:
                    data=response.read(2_000_001);actual=hashlib.sha256(data).hexdigest();item.update(status='pass' if actual==expected else 'content-mismatch',http_status=response.status,content_type=response.headers.get('Content-Type'),sha256=actual)
                if item['status']=='pass':break
            except Exception as error:item.update(status='unavailable',error=str(error))
            if attempt<2:time.sleep(3)
        results.append(item)
    report={'preview_url':base+'index.html','commit':args.sha,'status':'pass' if all(x['status']=='pass' for x in results) else 'review-required','resources':results}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    # Availability is reported separately from the site's deterministic correctness.
if __name__=='__main__':main()
