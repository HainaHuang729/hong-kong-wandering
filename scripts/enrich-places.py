"""Apply reviewed editorial visit guides without modifying coordinates or route geometries."""
import json,pathlib
R=pathlib.Path(__file__).resolve().parents[1]
p=R/'public/data/places.geojson';data=json.loads(p.read_text());guides=json.loads((R/'data/editorial/place-guides.json').read_text())
assert set(guides)=={f['properties']['id'] for f in data['features']}
for f in data['features']:
 g=guides[f['properties']['id']];f['properties']['visitGuide']=g
 f['properties']['visitDuration']=0 if g['kind']=='transport' else round(sum(g['minutes'])/2)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'Applied {len(guides)} editorial visit guides; geometry untouched.')
