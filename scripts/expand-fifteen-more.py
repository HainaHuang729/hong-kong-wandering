"""Add 15 new routes across Hong Kong Island, Kowloon, AMO heritage trails, New Territories West and outlying islands."""
import json
import math
import pathlib
import subprocess
import time

R = pathlib.Path(__file__).resolve().parents[1]
O = R / 'public/data'
D = R / 'data/raw'

def read(p):
    return json.loads(p.read_text())

def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

e = read(R / 'data/editorial/expansion-fifteen-more.json')
S = e['sources']
new_areas = e['areas']

areas = read(O / 'areas.json')
routes = read(O / 'routes.json')
places = read(O / 'places.geojson')
ps = {f['properties']['id']: f['properties'] for f in places['features']}
guides = read(R / 'data/editorial/place-guides.json')
cats = read(R / 'data/editorial/route-categories.json')

services = {
    'tw-west-station': ('metro', '港铁屯马线', S['mtr'], 'D 出口（海滨长廊 / 丽城花园方向）'),
}
static_note = '静态资料，不含实时班次、临时改道或开放状态。候车、候船及往返交通时间另计。'

def areaof(pid):
    return next(a for a in new_areas if pid in a['placeIds'])

def add_place(pid, name, en, osm_id, src_key, mins, highlights, mode=None, service=None, exit_or_stop=None):
    a = areaof(pid)
    candidates = read(D / f'{pid}.json')
    x = next(i for i in candidates if i['osm_id'] == osm_id) if osm_id else candidates[0]
    coord = [float(x['lon']), float(x['lat'])]
    cs = f"https://www.openstreetmap.org/{x['osm_type']}/{x['osm_id']}"
    url = S[src_key] if src_key else cs
    arrival = [a['transport'], '按地图中的真实步行路线到此点；车站出口与现场围挡以指示为准。']
    g = dict(
        kind='transport' if mode else 'sightseeing',
        minutes=mins,
        durationNote='交通节点，站内步行和候车船另计。' if mode else '编辑建议，包含观看和休息；不含两站之间步行与往返交通。',
        highlights=highlights,
        arrivalSteps=arrival,
        transportSourceUrl=S[a['transportSource']],
        contentSourceUrl=url,
        checkedAt='2026-11-16',
        transportNote=static_note
    )
    p = dict(
        id=pid,
        nameZh=name,
        nameEn=en,
        coordinates=coord,
        district=a['id'],
        categories=list(a['categories']),
        description=('；'.join(highlights) + '。'),
        sourceUrl=url,
        coordinateSource=cs,
        coordinateKind='OSM 代表点，非保证无障碍入口；具体站口按现场指示。',
        verifiedAt='2026-11-16',
        priority=120 + list(z['id'] for z in new_areas).index(a['id']),
        visitDuration=round(sum(mins) / 2),
        visitGuide=g,
        dataLicense='https://opendatacommons.org/licenses/odbl/1-0/',
        attribution='© OpenStreetMap contributors'
    )
    if ps.get(pid, {}).get('photo'):
        p['photo'] = ps[pid]['photo']
    ps[pid] = p
    guides[pid] = g
    if mode:
        services[pid] = (mode, service, url, exit_or_stop)

for pid, name, en, osm_id, _fkey, src_key, mins, highlights in e['sights']:
    add_place(pid, name, en, osm_id, src_key, mins, highlights)

for pid, name, en, osm_id, mode, service, src_key, exit_or_stop in e['transport']:
    add_place(pid, name, en, osm_id, src_key, [0, 0], [service, '核对目的地方向与现场登车、登船位置'], mode, service, exit_or_stop)

for idx, a in enumerate(new_areas):
    ids = a['placeIds']
    rid = a['routeId']
    file_name = a['rawFile']
    path = D / file_name
    url = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot/' + ';'.join(','.join(map(str, ps[i]['coordinates'])) for i in ids) + '?overview=full&geometries=geojson&steps=true'
    if not path.exists():
        res = subprocess.run(['curl', '-fLsS', '--retry', '4', '--retry-all-errors', '--max-time', '40', '-A', 'HongKongWandering-MVP-Research/0.1', url], capture_output=True, check=True)
        x = json.loads(res.stdout)
        assert x.get('code') == 'Ok', (rid, x)
        path.write_bytes(res.stdout)
        time.sleep(1.2)
    raw = read(path)
    rr = raw['routes'][0]
    snap = max(w['distance'] for w in raw['waypoints'])
    assert snap <= 120, (rid, snap)
    prop = dict(
        mode='walk',
        routeId=rid,
        source='OSM / FOSSGIS OSRM foot',
        requestUrl=url,
        rawFile=file_name,
        placeIds=ids,
        distance=rr['distance'],
        duration=rr['duration'],
        maxSnapMeters=snap,
        license='https://opendatacommons.org/licenses/odbl/1-0/',
        attribution='© OpenStreetMap contributors / FOSSGIS OSRM'
    )
    coords = rr['geometry']['coordinates']
    area_obj = dict(
        id=a['id'],
        nameZh=a['nameZh'],
        nameEn=a['nameEn'],
        categories=list(a['categories']),
        description=a['description'],
        duration=a['duration'],
        transport=a['transport'],
        sourceUrl=S[a['source']],
        verifiedAt='2026-11-16',
        placeIds=list(dict.fromkeys(ids)),
        coordinates=ps[ids[0]]['coordinates'],
        bounds=[
            min(c[0] for c in coords) - .002,
            min(c[1] for c in coords) - .002,
            max(c[0] for c in coords) + .002,
            max(c[1] for c in coords) + .002
        ],
        boundsNote='精选步行路线及地点的浏览范围，不是行政边界。',
        weather='建议干燥、凉爽天气；雷雨避免海岸、海堤和山径。',
        timeOfDay='白天出发；海滨与山顶可选傍晚，注意回程末班时间。',
        priority=40 + idx,
        status='researched'
    )
    areas = [x for x in areas if x['id'] != a['id']] + [area_obj]

    sights_in_route = [ps[pid] for pid in dict.fromkeys(ids) if pid in ps and ps[pid]['visitGuide']['kind'] == 'sightseeing']
    stay_minutes = [
        sum(p['visitGuide']['minutes'][0] for p in sights_in_route),
        sum(p['visitGuide']['minutes'][1] for p in sights_in_route)
    ]
    prefs = [p for p in a.get('preferences', []) if p not in ('少爬坡', '不太累')]
    if a['climbLevel'] == 'flat':
        prefs.append('少爬坡')
    if a['effortLevel'] == 'easy':
        prefs.append('不太累')

    r = dict(
        id=rid,
        areaId=a['id'],
        title=a['title'],
        description=a['description'],
        placeIds=ids,
        categories=list(a['categories']),
        categoryNotes=a['categories'],
        status='network-checked',
        verificationNote='官方景点与交通资料、独立 OSM 代表点与 FOSSGIS OSRM foot 路网已核对；未实地踏查，不代表当天开放或无障碍保证。',
        distance=round(rr['distance']),
        walkingMinutes=math.ceil(rr['duration'] / 60),
        maxSnapMeters=snap,
        visitMinutes=a['visitMinutes'],
        stayMinutes=stay_minutes,
        climbLevel=a['climbLevel'],
        effortLevel=a['effortLevel'],
        climbNote=a['climbNote'],
        transport=a['transport'],
        transportSource=S[a['transportSource']],
        sourceUrl=S[a['source']],
        verifiedAt='2026-11-16',
        timeOfDay='白天出发；海滨与山顶可选傍晚，注意回程末班时间。',
        notes=a['notes'],
        interests=a['interests'],
        preferences=prefs,
        requestUrl=url,
        geometry=dict(type='FeatureCollection', features=[dict(type='Feature', properties=prop, geometry=rr['geometry'])]),
        transportNote=static_note + '只绘制真实步行路网，不绘制未经核实的巴士或海上接驳轨迹。',
        transportNodes=[],
        earlyExits=[a['earlyExit']],
        itineraryLegs=[dict(fromIndex=i, toIndex=i + 1, mode='walk', distance=round(l['distance']), minutes=math.ceil(l['duration'] / 60)) for i, l in enumerate(rr['legs'])]
    )
    for i, pid in enumerate(ids):
        if pid not in services:
            continue
        mode, service, src, exit_or_stop = services[pid]
        role = 'start' if i == 0 else 'end' if i == len(ids) - 1 else 'access'
        instruction = a['transport'] if role == 'start' else '在此结束步行，核对目的地方向与当天班次后离开。' if role == 'end' else '可在这里中途接入或提前乘车离开；出发前核对出口方向。'
        r['transportNodes'].append(dict(
            placeId=pid,
            stopIndex=i,
            role=role,
            mode=mode,
            exitOrStop=exit_or_stop,
            service=service,
            instruction=instruction,
            sourceUrl=src
        ))
    routes = [x for x in routes if x['id'] != rid] + [r]
    cats[rid] = a['categories']
    print(f"OK {rid:20s} | {r['distance']:5d}m ({r['walkingMinutes']:2d}m walk) | stay {stay_minutes[0]}-{stay_minutes[1]}m | snap {snap:.1f}m", flush=True)

save(O / 'areas.json', areas)
save(O / 'routes.json', routes)
save(O / 'places.geojson', dict(type='FeatureCollection', features=[dict(type='Feature', geometry=dict(type='Point', coordinates=p['coordinates']), properties=p) for p in ps.values()]))
save(O / 'routes.geojson', dict(type='FeatureCollection', features=[f for r in routes for f in r['geometry']['features']]))
save(R / 'data/editorial/place-guides.json', guides)
save(R / 'data/editorial/route-categories.json', cats)
print(f"Expanded to {len(areas)} areas, {len(ps)} places, {len(routes)} routes.")
