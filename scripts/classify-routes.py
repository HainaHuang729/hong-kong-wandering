"""Apply editorial route features based on the existing verified stops."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1];out=R/'public/data'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
categories=read(R/'data/editorial/route-categories.json');routes=read(out/'routes.json');areas=read(out/'areas.json');places=read(out/'places.geojson')
assert set(categories)=={r['id'] for r in routes}
for r in routes:
 r['categoryNotes']=categories[r['id']];r['categories']=list(r['categoryNotes'])
 for interest,cat in [('逛小店','小店闲逛'),('看天际线','高楼与海港')]:
  if cat in r['categories'] and interest not in r['interests']:r['interests'].append(interest)
for a in areas:a['categories']=list(dict.fromkeys(c for r in routes if r['areaId']==a['id'] for c in r['categories']))
legacy={'城市漫步':'城市街巷','人文寻踪':'历史建筑','离岛出走':'离岛慢游','山林漫游':'山海之间','黄昏出逃':None,'山海之间':'山海之间'}
for f in places['features']:
 p=f['properties'];p['categories']=list(dict.fromkeys(legacy.get(c,c) for c in p['categories'] if legacy.get(c,c)))
 if p['id'] in ['stanley-market','pmq','central-market','apliu','temple-street'] and '小店闲逛' not in p['categories']:p['categories'].append('小店闲逛')
 if p['id']=='clocktower' and '高楼与海港' not in p['categories']:p['categories'].append('高楼与海港')
 if not p['categories']:p['categories']=['城市街巷']
write(out/'routes.json',routes);write(out/'areas.json',areas);write(out/'places.geojson',places)
print({c:sum(c in r['categories'] for r in routes) for c in ['城市街巷','山海之间','小店闲逛','高楼与海港','离岛慢游','历史建筑']})
