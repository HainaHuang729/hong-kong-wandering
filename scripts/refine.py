import json,pathlib,urllib.request,urllib.parse,time
R=pathlib.Path(__file__).resolve().parents[1]; raw=R/'data/raw'; out=R/'public/data'
d=json.loads((out/'places.geojson').read_text()); areas=json.loads((out/'areas.json').read_text())
p={f['properties']['id']:f for f in d['features']}
for pid,q in [('yungshue','榕樹灣碼頭'),('sokkwu','索罟灣碼頭'),('taio-bridge','大澳涌行人橋')]:
 time.sleep(1.2)
 url='https://nominatim.openstreetmap.org/search?'+urllib.parse.urlencode({'q':q,'format':'json','limit':3,'viewbox':'113.8,22.6,114.45,22.15','bounded':1})
 req=urllib.request.Request(url,headers={'User-Agent':'HongKongWandering-MVP-Research/0.1'})
 try:
  path=raw/(pid+'-refined.json');results=json.loads(path.read_text()) if path.exists() else json.load(urllib.request.urlopen(req,timeout=25));(raw/(pid+'-refined.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2));print(pid,results,flush=True)
 except Exception as e: print(e)
