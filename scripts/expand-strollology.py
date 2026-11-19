"""Add the 10 routes and 9 new districts from Hong Kong Strollology (《香港散步學》) without breaking existing IDs, routes, or local records."""
import json, pathlib, subprocess, time, math

R = pathlib.Path(__file__).resolve().parents[1]
O = R / 'public/data'
D = R / 'data/raw'

def read(p):
    return json.loads(p.read_text())

def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

e = read(R / 'data/editorial/expansion-strollology.json')
S = e['sources']
new_areas = e['areas']

areas = read(O / 'areas.json')
routes = read(O / 'routes.json')
places = read(O / 'places.geojson')
ps = {f['properties']['id']: f['properties'] for f in places['features']}
guides = read(R / 'data/editorial/place-guides.json')
cats = read(R / 'data/editorial/route-categories.json')

services = {
    'central-mtr': ('metro', '港铁港岛线 / 荃湾线', S['mtr']),
    'ssp-station': ('metro', '港铁荃湾线', S['mtr']),
    'st-station': ('metro', '港铁东铁线', S['mtr']),
}

static_note = '静态资料，不含实时班次、临时改道或开放状态。候车、候船及往返交通时间另计。'

def areaof(pid):
    return next(a for a in new_areas if pid in a['placeIds'])

def add_place(pid, name, en, osm_id, file_key, src_key, mins, highlights, mode=None, service=None):
    a = areaof(pid)
    candidates = read(D / (file_key + '.json'))
    x = next(x for x in candidates if x['osm_id'] == osm_id) if osm_id else candidates[0]
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
        priority=80 + list(z['id'] for z in new_areas).index(a['id']),
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
        services[pid] = (mode, service, url)

for args in e['sights']:
    add_place(*args)

for pid, name, en, osm_id, file_key, mode, service, src_key in e['transport']:
    add_place(pid, name, en, osm_id, file_key, src_key, [0, 0], [service, '核对目的地方向与现场登车、登船位置'], mode, service)

for idx, a in enumerate(new_areas):
    ids = a['placeIds']
    rid = a['routeId']
    file_name = a['rawFile']
    path = D / file_name
    url = 'https://routing.openstreetmap.de/routed-foot/route/v1/foot/' + ';'.join(','.join(map(str, ps[i]['coordinates'])) for i in ids) + '?overview=full&geometries=geojson&steps=true'
    if not path.exists():
        res = subprocess.run(['curl', '-fLsS', '--retry', '2', '--max-time', '40', '-A', 'HongKongWandering-MVP-Research/0.1', url], capture_output=True, check=True)
        x = json.loads(res.stdout)
        assert x.get('code') == 'Ok'
        path.write_bytes(res.stdout)
        time.sleep(1.2)
    raw = read(path)
    rr = raw['routes'][0]
    snap = max(w['distance'] for w in raw['waypoints'])
    print(rid, round(rr['distance']), math.ceil(rr['duration'] / 60), round(snap, 1), [(ids[i], round(w['distance'], 1)) for i, w in enumerate(raw['waypoints'])], flush=True)
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
    existing_area = next((x for x in areas if x['id'] == a['id']), None)
    if existing_area:
        combined_pids = list(dict.fromkeys(existing_area['placeIds'] + ids))
        all_coords = [ps[i]['coordinates'] for i in combined_pids if i in ps] + coords
        existing_area['placeIds'] = combined_pids
        existing_area['bounds'] = [
            min(c[0] for c in all_coords) - .002,
            min(c[1] for c in all_coords) - .002,
            max(c[0] for c in all_coords) + .002,
            max(c[1] for c in all_coords) + .002
        ]
        existing_area['categories'] = list(dict.fromkeys(existing_area['categories'] + list(a['categories'])))
    else:
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
            weather='建议干燥、凉爽天气；雷雨避免海岸、河边和山径。',
            timeOfDay='白天出发；海滨可选傍晚，山径应在天黑前完成。',
            priority=16 + idx,
            status='researched'
        )
        areas.append(area_obj)

    r = dict(
        id=rid,
        areaId=a['id'],
        title=a['title'],
        description=a['description'],
        placeIds=ids,
        categories=list(a['categories']),
        categoryNotes=a['categories'],
        status='network-checked',
        verificationNote='据《香港散步學》路线框架及官方景点/交通资料，使用独立 OSM 代表点与 FOSSGIS OSRM foot 路网核对；未实地踏查，不代表当天开放或无障碍保证。',
        distance=round(rr['distance']),
        walkingMinutes=math.ceil(rr['duration'] / 60),
        maxSnapMeters=snap,
        visitMinutes=a['visitMinutes'],
        transport=a['transport'],
        transportSource=S[a['transportSource']],
        sourceUrl=S[a['source']],
        verifiedAt='2026-11-16',
        timeOfDay='白天出发；海滨可选傍晚，山径应在天黑前完成。',
        notes=a['notes'],
        interests=a['interests'],
        preferences=a['preferences'],
        requestUrl=url,
        geometry=dict(type='FeatureCollection', features=[dict(type='Feature', properties=prop, geometry=rr['geometry'])]),
        transportNote=static_note + '只绘制真实步行路网，不绘制未经核实的巴士或海上接驳轨迹。',
        transportNodes=[],
        itineraryLegs=[dict(fromIndex=i, toIndex=i + 1, mode='walk', distance=round(l['distance']), minutes=math.ceil(l['duration'] / 60)) for i, l in enumerate(rr['legs'])]
    )
    for i, pid in enumerate(ids):
        if pid not in services:
            continue
        mode, service, src = services[pid]
        role = 'start' if i == 0 else 'end' if i == len(ids) - 1 else 'access'
        instruction = a['transport'] if role == 'start' else '在此结束步行，核对目的地方向与当天班次后离开。' if role == 'end' else '可在这里中途接入或提前乘渡轮离开；出发前核对服务和班次。'
        r['transportNodes'].append(dict(placeId=pid, stopIndex=i, role=role, mode=mode, service=service, instruction=instruction, sourceUrl=src))
    routes = [x for x in routes if x['id'] != rid] + [r]
    cats[rid] = a['categories']

save(O / 'areas.json', areas)
save(O / 'routes.json', routes)
save(O / 'places.geojson', dict(type='FeatureCollection', features=[dict(type='Feature', geometry=dict(type='Point', coordinates=p['coordinates']), properties=p) for p in ps.values()]))
save(O / 'routes.geojson', dict(type='FeatureCollection', features=[f for r in routes for f in r['geometry']['features']]))
save(R / 'data/editorial/place-guides.json', guides)
save(R / 'data/editorial/route-categories.json', cats)

planned = read(O / 'planned-areas.json')
completed_planned = {'北角—鲗鱼涌', '黄大仙—钻石山', '荃湾'}
save(O / 'planned-areas.json', [p for p in planned if p['nameZh'] not in completed_planned])
print(f'Added 10 strollology routes; now {len(areas)} areas, {len(ps)} places, {len(routes)} routes.')
