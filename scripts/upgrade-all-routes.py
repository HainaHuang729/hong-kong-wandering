"""Add 4 priority districts (Quarry Bay, West Kowloon, Kowloon City, Tai Po) and upgrade all 30 routes with exits, early exits, climb/effort tags, and separated timing."""
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

MTR = 'https://www.mtr.com.hk/en/customer/services/system_map.html'
TD = 'https://data.gov.hk/en-data/dataset/hk-td-tis_23-routes-fares-geojson'
KMB_TP = 'https://search.kmb.hk/KMBWebSite/?action=routesearch&route=72A&lang=en'
KMB_TW = 'https://search.kmb.hk/KMBWebSite/?action=routesearch&route=53&lang=en'
CTB_9 = 'https://mobile.citybus.com.hk/nwp3/?f=1&ds=9&dsmode=1&l=1'
CTB_260 = 'https://mobile.citybus.com.hk/nwp3/?f=1&ds=260&dsmode=1&l=1'
CTB_70 = 'https://mobile.citybus.com.hk/nwp3/?f=1&ds=70&dsmode=1&l=1'
FERRY = 'https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/ferries/service_details/index.html'
NLB_11 = 'https://www.nlb.com.hk/en/route/13'

areas = read(O / 'areas.json')
routes = read(O / 'routes.json')
places = read(O / 'places.geojson')
ps = {f['properties']['id']: f['properties'] for f in places['features']}
guides = read(R / 'data/editorial/place-guides.json')
cats = read(R / 'data/editorial/route-categories.json')

# 1. Add the 4 priority expansion districts
e = read(R / 'data/editorial/expansion-four-priority.json')
S = e['sources']
new_areas = e['areas']
services = {
    'np-station': ('metro', '港铁港岛线 / 将军澳线', MTR),
    'tkw-sungwongtoi-station': ('metro', '港铁屯马线', MTR),
    'spk-diamondhill-station': ('metro', '港铁观塘线 / 屯马线', MTR),
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
        priority=100 + list(z['id'] for z in new_areas).index(a['id']),
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
        res = subprocess.run(['curl', '-fLsS', '--retry', '4', '--retry-all-errors', '--max-time', '40', '-A', 'HongKongWandering-MVP-Research/0.1', url], capture_output=True, check=True)
        x = json.loads(res.stdout)
        assert x.get('code') == 'Ok'
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
        weather='建议干燥、凉爽天气；雷雨避免海岸、河边和山径。',
        timeOfDay='白天出发；海滨可选傍晚，山径应在天黑前完成。',
        priority=25 + idx,
        status='researched'
    )
    areas = [x for x in areas if x['id'] != a['id']] + [area_obj]

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
        instruction = a['transport'] if role == 'start' else '在此结束步行，核对目的地方向与当天班次后离开。' if role == 'end' else '可在这里中途接入或提前乘港铁离开；出发前核对出口方向。'
        r['transportNodes'].append(dict(placeId=pid, stopIndex=i, role=role, mode=mode, service=service, instruction=instruction, sourceUrl=src))
    routes = [x for x in routes if x['id'] != rid] + [r]
    cats[rid] = a['categories']

# 2. Exact exits / stops for all transport nodes
NODE_EXITS = {
    'repulse-bus': '浅水湾道往赤柱方向（南行站台）',
    'stanley-bus': '赤柱村道近赤柱广场（下车站）',
    'stanley-return': '赤柱村巴士总站（往中环方向）',
    'sheko-bus': '石澳巴士总站（往筲箕湾方向）',
    'kennedy-station': 'A / C 出口（卑路乍街）',
    'saiyingpun': 'A2 / B3 出口（第一街 / 皇后大道西）',
    'sheungwan-mtr': 'B 出口（西港城） / A2 出口（永乐街）',
    'central-mtr': 'C / D2 出口（毕打街 / 皇后大道中）',
    'wanchai-station': 'A3 出口（太原街 / 庄士敦道）',
    'ssp-station': 'C2 出口（鸭寮街） / B2 出口（北河街）',
    'yaumatei-mtr': 'B2 出口（窝打老道 / 油麻地戏院方向）',
    'jordan-mtr': 'A 出口（佐敦道 / 庙街南端）',
    'tst-mtr': 'E / L6 出口（弥敦道 / 梳士巴利道）',
    'cc-pier': '长洲渡轮码头（往返中环五号码头）',
    'yungshue': '榕树湾渡轮码头（往返中环四号码头）',
    'sokkwu': '索罟湾二号码头（往返中环四号码头）',
    'taio-bus': '大澳巴士总站（往东涌站方向）',
    'sk-bus': '西贡巴士总站（九巴 92 往钻石山站站位）',
    'st-station': 'A3 出口（经新城市广场往沙田公园）',
    'stw-station': 'A 出口（沙角邨方向）',
    'ntk-station': 'B6 出口（励业街往观塘海滨）',
    'kt-pier': '观塘渡轮码头（北角—观塘—启德线）',
    'kt-station': 'B3 出口（开源道）',
    'pc-pier': '坪洲渡轮码头（中环六号码头西侧航班）',
    'mw-pier': '梅窝渡轮码头（中环六号码头东侧航班）',
    'th-tinhau-station': 'B 出口（兴发街 / 皇仁书院方向）',
    'np-braemar-hill-bus': '宝马山巴士总站 / 宝马山道落客站',
    'np-ferry-pier': '北角（西）渡轮码头（往九龙城 / 红磡 / 观塘）',
    'np-station': 'A2 / B1 出口（春秧街 / 英皇道）',
    'mlw-hku-station': 'A2 出口（乘大学道升降机上旭龢道）',
    'alc-leitung-station': 'A1 出口（鸭脷洲大街 / 风之塔公园方向）',
    'abd-bus-terminus': '香港仔（湖南街）巴士总站（往中环 / 铜锣湾）',
    'ncw-choihung-station': 'C2 出口（牛池湾街市 / 彩虹邨方向）',
    'spk-diamondhill-station': 'A1 / C2 出口（大磡道 / 凤德道方向）',
    'skm-station': 'A / B1 出口（窝仔街 / 伟智街）',
    'tkw-station': 'B 出口（落山道 / 靠背垄道方向）',
    'tkw-sungwongtoi-station': 'D 出口（宋王台花园） / B2 出口（衙前围道）',
    'st-taiwai-station': 'A 出口（村南道 / 城门河大围端）',
    'tko-tiukengleng-station': 'A2 出口（香港知专设计学院平台）',
    'tko-station': 'B1 出口（唐俊街 / 唐明街公园方向）',
    'tw-west-station': 'D 出口（海滨长廊 / 丽城花园方向）',
    'tw-sham-tseng-bus': '青山公路「深井村」巴士站（往荃湾方向）',
    'qb-station': 'A / C 出口（英皇道 / 模范里）',
    'qb-taikoo-station': 'B / D1 出口（太古城 / 英皇道）',
    'wk-austin-station': 'E 出口（行人隧道直通戏曲中心）',
    'wk-kowloon-station': 'C1 / E4 出口（圆方行人天桥往艺术公园）',
    'kc-lokfu-station': 'B 出口（横头磡南道 / 贾炳达道方向）',
    'tp-taiwo-station': 'B 出口（太和广场往香港铁路博物馆）',
    'tp-market-station': 'A2 出口（南运路 / 达运道）',
    'tp-waterfront-bus': '大埔工业邨 / 完善路巴士站（往大埔墟站方向）',
    'tt-wong-nai-chung-bus': '黄泥涌水塘公园巴士站（大潭水塘道入口）',
    'tt-bus': '大潭水塘（北）巴士站（城巴 14 往西湾河站 / 赤柱）',
    'tc-station': 'A / B 出口（往海滨及东涌小炮台）',
    'tc-yat-tung-bus': '逸东邨巴士总站（新大屿山巴士 37 / 38 往东涌站）',
    'wts-station': 'B2 出口（龙翔道 / 黄大仙祠广场）',
}

# 3. Route climb/effort metadata & verified earlyExits
ROUTE_META = {
    'route-repulse': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '两段步行主要沿沙滩边与赤柱海旁平路，仅泳滩与浅水湾道巴士站之间有梯级与缓坡上落。',
        'earlyExits': [
            {'atPlaceId': 'repulse-bus', 'stopIndex': 2, 'nameZh': '浅水湾泳滩巴士站（回程）', 'mode': 'bus', 'exitOrStop': '浅水湾道北行对面站台', 'service': '城巴 260 / 6 / 6X · 往中环或铜锣湾', 'instruction': '游览浅水湾后若不想继续前往赤柱，可过马路至北行站乘巴士直接返市区。', 'sourceUrl': CTB_260}
        ]
    },
    'route-sheko': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 0.8 km 均为村落平路与海滨通道，无长楼梯或陡坡，适合轻松慢走。',
        'earlyExits': [
            {'atPlaceId': 'sheko-temple', 'stopIndex': 2, 'nameZh': '石澳巴士总站（村内捷径）', 'mode': 'bus', 'exitOrStop': '石澳村道总站站位', 'service': '城巴 9 · 往筲箕湾站', 'instruction': '看完石澳天后庙后可直接向西步行约 150 米至巴士总站乘城巴 9 号离开。', 'sourceUrl': CTB_9}
        ]
    },
    'route-kennedy': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '沿坚尼地城与西营盘海旁平坦人行道及德辅道西行走，全线平缓无陡坡。',
        'earlyExits': [
            {'atPlaceId': 'belcher', 'stopIndex': 1, 'nameZh': '香港大学站 / 坚尼地城海旁电车站', 'mode': 'metro', 'exitOrStop': '港铁 C1 出口（卑路乍街）', 'service': '港铁港岛线 · 香港大学站或香港电车', 'instruction': '在卑路乍湾公园小憩后，往南穿过卑路乍街即可在港铁香港大学站 C1 出口或电车站提前乘车离开。', 'sourceUrl': MTR}
        ]
    },
    'route-sheungwan': {
        'climbLevel': 'moderate',
        'effortLevel': 'easy',
        'climbNote': '由西港城上行至荷李活道公园段有缓坡与短石阶，其余沿街路段平缓。',
        'earlyExits': [
            {'atPlaceId': 'hollywood-park', 'stopIndex': 2, 'nameZh': '上环 / 德辅道西电车站', 'mode': 'metro', 'exitOrStop': '水坑口街往下行至皇后大道中/德辅道', 'service': '港铁港岛线 · 上环站 A2 出口或电车', 'instruction': '在荷李活道公园结束即可顺水坑口街下坡返回德辅道中电车站或上环站。', 'sourceUrl': MTR}
        ]
    },
    'route-central': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多：上环楼梯街、荷李活道、元创方及大馆一带包含多段斜坡与石阶，穿好走鞋并留意下行扶梯方向。',
        'earlyExits': [
            {'atPlaceId': 'taikwun', 'stopIndex': 3, 'nameZh': '中环至半山扶梯往中环站', 'mode': 'metro', 'exitOrStop': '兰桂坊 / 皇后大道中 C / D2 出口', 'service': '港铁港岛线 / 荃湾线 · 中环站', 'instruction': '参观大馆后可直接走奥卑利街或荷李活道下坡，经行人通道前往中环站 D2 出口提前结束。', 'sourceUrl': MTR}
        ]
    },
    'route-wanchai': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 1.4 km 沿湾仔旧街与石水渠街平缓路面行走，仅北帝庙前有少量台阶。',
        'earlyExits': [
            {'atPlaceId': 'pakta-wan', 'stopIndex': 2, 'nameZh': '皇后大道东巴士廊', 'mode': 'bus', 'exitOrStop': '隆安街 / 石水渠街口', 'service': '城巴 6 / 10 / 15 · 往中环、铜锣湾或北角', 'instruction': '在湾仔北帝庙结束后可就近于皇后大道东乘巴士，或北行春园街返回湾仔站 A3 出口。', 'sourceUrl': MTR}
        ]
    },
    'route-shamshuipo': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线沿鸭寮街、钦州街与巴域街平路行走，仅嘉顿山旁美荷楼入口有短斜道。',
        'earlyExits': [
            {'atPlaceId': 'meiho', 'stopIndex': 2, 'nameZh': '石硖尾站', 'mode': 'metro', 'exitOrStop': 'C 出口（窝仔街 / 大埔道）', 'service': '港铁观塘线 · 石硖尾站', 'instruction': '参观美荷楼后无需折返深水埗站，向东沿巴域街及大埔道步行约 350 米即可到石硖尾站。', 'sourceUrl': MTR}
        ]
    },
    'route-yaumatei': {
        'climbLevel': 'flat',
        'effortLevel': 'moderate',
        'climbNote': '全线沿窝打老道、庙街、弥敦道与海旁平地步行，无明显爬坡，唯全长约 3.9 km。',
        'earlyExits': [
            {'atPlaceId': 'jordan-mtr', 'stopIndex': 3, 'nameZh': '佐敦站', 'mode': 'metro', 'exitOrStop': 'A 出口（佐敦道 / 庙街）', 'service': '港铁荃湾线 · 佐敦站', 'instruction': '逛完油麻地戏院与庙街后可在此提前结束行程，无需继续南行至尖沙咀海旁。', 'sourceUrl': MTR}
        ]
    },
    'route-cheungchau': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 1.3 km 均为长洲旧墟平坦街巷与海滨平路，老少皆宜。',
        'earlyExits': [
            {'atPlaceId': 'cc-paktai', 'stopIndex': 1, 'nameZh': '长洲渡轮码头（由新兴街返）', 'mode': 'ferry', 'exitOrStop': '中环 5 号码头渡轮航线', 'service': '新渡轮 · 长洲 ↔ 中环五号码头', 'instruction': '逛完北帝庙广场可沿新兴街南行约 400 米直接回码头，略过东湾泳滩段。', 'sourceUrl': FERRY}
        ]
    },
    'route-lamma': {
        'climbLevel': 'steep',
        'effortLevel': 'challenging',
        'climbNote': '爬坡较多：洪圣爷湾往索罟湾段需翻越南丫岛山地鞍部并上下多段长石阶，全程 4.9 km 须留足饮水与体力。',
        'earlyExits': [
            {'atPlaceId': 'hungshing', 'stopIndex': 1, 'nameZh': '洪圣爷湾折返榕树湾码头', 'mode': 'ferry', 'exitOrStop': '榕树湾大街原路返码头', 'service': '港九小轮 · 榕树湾 ↔ 中环四号码头', 'instruction': '抵达洪圣爷湾前路段平缓；若不想翻山前往索罟湾，建议在泳滩后原路折返榕树湾码头乘船。', 'sourceUrl': FERRY}
        ]
    },
    'route-taio': {
        'climbLevel': 'flat',
        'effortLevel': 'moderate',
        'climbNote': '沿大澳水道、市场街与石仔埗街平路步行，仅大涌行人桥微坡，但单程来回约 3 km 需留意时间。',
        'earlyExits': [
            {'atPlaceId': 'taio-temple', 'stopIndex': 2, 'nameZh': '大澳巴士总站（旧墟折返）', 'mode': 'bus', 'exitOrStop': '永安街跨大涌桥返回总站', 'service': '新大屿山巴士 11 · 往东涌站', 'instruction': '参观大澳关帝古庙与旧墟后可就近跨桥回大澳巴士总站，不必再沿海旁步行 1.5 公里往返大澳文物酒店。', 'sourceUrl': NLB_11}
        ]
    },
    'route-saikung': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 1.1 km 沿西贡旧墟平街与海滨公园步行，无坡道或阶梯障碍。',
        'earlyExits': [
            {'atPlaceId': 'sk-temple', 'stopIndex': 1, 'nameZh': '西贡巴士总站（宜春街出口）', 'mode': 'bus', 'exitOrStop': '福民路 / 普通道总站', 'service': '九巴 92 / 专线小巴 1A · 往钻石山或彩虹', 'instruction': '西贡墟天后庙距巴士总站与小巴总站仅约 250 米，可随时结束行程乘车离开。', 'sourceUrl': 'https://search.kmb.hk/KMBWebSite/?action=routesearch&route=92&lang=en'}
        ]
    },
    'route-shatin': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 1.6 km 沿沙田公园林荫步道与沥源桥（无障碍斜道与行人桥面）步行，平缓好走。',
        'earlyExits': [
            {'atPlaceId': 'st-park', 'stopIndex': 1, 'nameZh': '沙田站（新城市广场）', 'mode': 'metro', 'exitOrStop': 'A3 出口（穿过城市艺坊回站）', 'service': '港铁东铁线 · 沙田站', 'instruction': '在沙田公园休息后可直接西行返回沙田站乘东铁线，无需过河前往沙田围站。', 'sourceUrl': MTR}
        ]
    },
    'route-kwuntong': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '沿励业街、海滨长廊与开源道平缓步行，全线无山坡。',
        'earlyExits': [
            {'atPlaceId': 'kt-pier', 'stopIndex': 2, 'nameZh': '观塘渡轮码头 / 巴士总站', 'mode': 'ferry', 'exitOrStop': '海滨道末端码头泊位', 'service': '渡轮往北角 / 启德；基业街多条巴士线', 'instruction': '沿观塘海滨走到观塘码头即可乘渡轮前往北角，或在旁观塘码头巴士总站乘车离开。', 'sourceUrl': FERRY}
        ]
    },
    'route-pengchau': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多：村内永安街平缓，但登上手指山需连续攀登长石阶至海拔 95 米山顶凤萍亭，雨后石级湿滑。',
        'earlyExits': [
            {'atPlaceId': 'pc-temple', 'stopIndex': 1, 'nameZh': '坪洲渡轮码头（仅逛老街）', 'mode': 'ferry', 'exitOrStop': '永安街向西回码头', 'service': '港九小轮 · 坪洲 ↔ 中环六号码头', 'instruction': '参观天后宫与永安街小店后若不想攀登手指山，沿平街向南走 200 米即可回码头。', 'sourceUrl': FERRY}
        ]
    },
    'route-muiwo': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多：由银矿湾泳滩进入涌口村及瀑布花园后段有明显山边上坡步道，且全长约 4.1 km 需原路或环线返码头。',
        'earlyExits': [
            {'atPlaceId': 'mw-beach', 'stopIndex': 1, 'nameZh': '梅窝渡轮码头 / 巴士总站', 'mode': 'ferry', 'exitOrStop': '银矿湾路往码头方向', 'service': '新渡轮 · 梅窝 ↔ 中环六号码头', 'instruction': '在银矿湾泳滩漫步后若不想走内陆坡道上瀑布花园，可直接沿银矿湾路平路回码头。', 'sourceUrl': FERRY}
        ]
    },
    'route-taihang': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多：大坑街区为平路，但由第二巷经大坑道上山前往虎豹别墅及励德邨需连续爬坡，回程经莲花宫公园亦有长石阶下行。',
        'earlyExits': [
            {'atPlaceId': 'th-second-lane', 'stopIndex': 3, 'nameZh': '天后站 / 铜锣湾（平地结束）', 'mode': 'metro', 'exitOrStop': '沿浣纱街北行返铜锣湾道', 'service': '港铁港岛线 · 天后站 B 出口', 'instruction': '逛完大坑一二三巷与咖啡小店后若不想上大坑道爬坡，沿浣纱街折返即可回到平地干道及天后站。', 'sourceUrl': MTR},
            {'atPlaceId': 'th-lai-tak', 'stopIndex': 5, 'nameZh': '励德邨巴士 / 小巴站', 'mode': 'bus', 'exitOrStop': '励德邨道往铜锣湾方向站台', 'service': '城巴 25A / 专线小巴 21M · 往铜锣湾/天后', 'instruction': '在励德邨可直接在邨内巴士站乘下山巴士或小巴回铜锣湾，免走通往莲花宫的长石阶。', 'sourceUrl': 'https://mobile.citybus.com.hk/nwp3/?f=1&ds=25A&dsmode=1&l=1'}
        ]
    },
    'route-northpoint': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多（以下坡为主）：从宝马山起步经百福道长下坡及明园西街陡斜坡道下山至北角，请注意膝盖保护与湿滑斜道。',
        'earlyExits': [
            {'atPlaceId': 'np-ming-yuen-west', 'stopIndex': 4, 'nameZh': '炮台山站 / 英皇道电车站', 'mode': 'metro', 'exitOrStop': '沿明园西街直下英皇道', 'service': '港铁港岛线 · 炮台山站或北角站', 'instruction': '看完明园西街「半边楼」后下坡至英皇道即可搭电车或港铁，略过和富中心与码头段。', 'sourceUrl': MTR},
            {'atPlaceId': 'np-ferry-pier', 'stopIndex': 6, 'nameZh': '北角（西）渡轮码头', 'mode': 'ferry', 'exitOrStop': '码头泊位（往九龙城 / 红磡 / 观塘）', 'service': '渡轮 · 北角 ↔ 红磡 / 九龙城 / 观塘', 'instruction': '抵达北角海滨码头后可直接乘渡轮过维港，不必再南行至北角港铁站。', 'sourceUrl': FERRY}
        ]
    },
    'route-midlevelswest': {
        'climbLevel': 'steep',
        'effortLevel': 'challenging',
        'climbNote': '爬坡较多：须由香港大学站乘升降机或沿旭龢道爬坡至龙虎山，其后沿罗便臣道及己连拿利天桥、动植物公园阶梯起伏较多，全长 4.5 km。',
        'earlyExits': [
            {'atPlaceId': 'mlw-robinson-road', 'stopIndex': 2, 'nameZh': '半山自动扶梯（罗便臣道入口）', 'mode': 'metro', 'exitOrStop': '沿罗便臣道往东接半山扶梯下行', 'service': '行人扶梯通道往中环站 / 皇后大道中', 'instruction': '走到罗便臣道与西摩道一带可转入中环至半山自动扶梯系统下山（上午 10 时后改为下行），直达中环离开。', 'sourceUrl': MTR}
        ]
    },
    'route-aberdeen': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '鸭脷洲风之塔公园与香港仔海滨均为平路，仅上下鸭脷洲大桥行人天桥引道及香港仔市政大厦周边有缓坡与天桥楼梯。',
        'earlyExits': [
            {'atPlaceId': 'alc-wind-tower-park', 'stopIndex': 1, 'nameZh': '鸭脷洲大街街渡码头 / 利东站', 'mode': 'ferry', 'exitOrStop': '悦海街海旁街渡码头或利东站 A1', 'service': '香港仔—鸭脷洲街渡 · 往香港仔海滨', 'instruction': '游览风之塔公园后可乘街渡直接过海至香港仔海滨（免步行跨鸭脷洲大桥），或回利东站乘地铁。', 'sourceUrl': FERRY},
            {'atPlaceId': 'abd-promenade', 'stopIndex': 4, 'nameZh': '香港仔海滨公园巴士站', 'mode': 'bus', 'exitOrStop': '香港仔海傍道北行巴士站', 'service': '城巴 70 / 72 / 90B · 往中环或金钟', 'instruction': '沿香港仔海滨公园散步后即可在海傍道巴士站乘车离开，免再绕入香港仔中心街区。', 'sourceUrl': CTB_70}
        ]
    },
    'route-sanpokong': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '牛池湾街市、彩虹邨与启德河大部分为平路，仅跨公路天桥及进入凤德公园园景步道有局部楼梯或缓坡；全长 4.9 km。',
        'earlyExits': [
            {'atPlaceId': 'spk-kai-tak-river', 'stopIndex': 3, 'nameZh': '启德站 / 彩虹道巴士站', 'mode': 'metro', 'exitOrStop': '新蒲岗交汇处往太子道东行人隧道', 'service': '港铁屯马线 · 启德站 B 出口', 'instruction': '走完彩虹邨与启德河新蒲岗段后，可经景泰苑外行人路步行约 450 米至启德站提前离开。', 'sourceUrl': MTR}
        ]
    },
    'route-shekkipmei': {
        'climbLevel': 'steep',
        'effortLevel': 'moderate',
        'climbNote': '爬坡较多：需从棠荫街或巴域街上行主教山山径（泥石与石级），再经大坑东游乐场及南山邨多层平台楼梯转换高差。',
        'earlyExits': [
            {'atPlaceId': 'skm-nam-shan-estate', 'stopIndex': 3, 'nameZh': '石硖尾站（大坑东道出口）', 'mode': 'metro', 'exitOrStop': 'B2 出口（大坑东道 / 南山邨旁）', 'service': '港铁观塘线 · 石硖尾站', 'instruction': '南山邨平台西侧下楼即是大坑东道与石硖尾站 B2 出口，可在此随时结束前半段。', 'sourceUrl': MTR},
            {'atPlaceId': 'skm-jccac', 'stopIndex': 5, 'nameZh': '石硖尾站（白田街出口）', 'mode': 'metro', 'exitOrStop': 'C 出口（伟智街 / 窝仔街）', 'service': '港铁观塘线 · 石硖尾站', 'instruction': '参观完 JCCAC 后沿白田街南下 250 米即达石硖尾站 C 出口，不必再往南走到深水埗。', 'sourceUrl': MTR}
        ]
    },
    'route-tokwawan': {
        'climbLevel': 'steep',
        'effortLevel': 'challenging',
        'climbNote': '爬坡较多：全长 6.3 km 且穿插高山道公园山坡、靠背垄道及乐民新村山腰梯级，包含较大上下落差。',
        'earlyExits': [
            {'atPlaceId': 'tkw-market', 'stopIndex': 4, 'nameZh': '土瓜湾站（红苹果街市旁）', 'mode': 'metro', 'exitOrStop': 'A / D 出口（马头围道 / 落山道）', 'service': '港铁屯马线 · 土瓜湾站', 'instruction': '走完高山剧场与红苹果街市后，东行约 150 米即回到土瓜湾站，适合拆分为半程。', 'sourceUrl': MTR}
        ]
    },
    'route-shatin-stroll': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '城门河两岸为平坦河滨步道，但进出秦石邨、博康邨及沥源禾輋行人天桥系统有天桥斜道与楼梯，全长约 5.8 km。',
        'earlyExits': [
            {'atPlaceId': 'st-pok-hong', 'stopIndex': 3, 'nameZh': '沙田围站', 'mode': 'metro', 'exitOrStop': 'D / A 出口（博康邨东侧）', 'service': '港铁屯马线 · 沙田围站', 'instruction': '走出博康邨商场往东约 200 米即是港铁沙田围站，可作为南岸半程终点。', 'sourceUrl': MTR},
            {'atPlaceId': 'st-town-hall', 'stopIndex': 5, 'nameZh': '沙田站（新城市广场）', 'mode': 'metro', 'exitOrStop': 'A3 出口（沙田大会堂直入商场）', 'service': '港铁东铁线 · 沙田站', 'instruction': '在沙田大会堂结束后可直接进入新城市广场返回沙田站，省略过沥源桥至沥源邨环线。', 'sourceUrl': MTR}
        ]
    },
    'route-tseungkwano': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '海滨长廊与公园内部均平缓，仅知专设计学院平台扶梯及各区天桥连接段有坡道，全程约 6.2 km 环线。',
        'earlyExits': [
            {'atPlaceId': 'tko-sheung-ning', 'stopIndex': 4, 'nameZh': '坑口站', 'mode': 'metro', 'exitOrStop': 'B1 出口（常宁路北行）', 'service': '港铁将军澳线 · 坑口站', 'instruction': '走到常宁游乐场后若已感到疲倦，往北步行约 300 米即可至港铁坑口站提前离开。', 'sourceUrl': MTR}
        ]
    },
    'route-shamtseng': {
        'climbLevel': 'steep',
        'effortLevel': 'challenging',
        'climbNote': '爬坡较多：沿青山公路虽多为缓坡，但下行汀九村、泳滩及上行返回公路均有长石阶，且总步距达 6.7 km。',
        'earlyExits': [
            {'atPlaceId': 'tw-approach-beach', 'stopIndex': 2, 'nameZh': '近水湾巴士站', 'mode': 'bus', 'exitOrStop': '青山公路（油柑头 / 近水湾站）', 'service': '九巴 53 / 234B · 往荃湾西站', 'instruction': '在近水湾即可于青山公路旁巴士站乘车折返荃湾，提前结束漫长海岸路。', 'sourceUrl': KMB_TW},
            {'atPlaceId': 'tw-ting-kau-beach', 'stopIndex': 4, 'nameZh': '汀九巴士站', 'mode': 'bus', 'exitOrStop': '青山公路－汀九段东行站', 'service': '九巴 53 / 234B · 往荃湾西站', 'instruction': '在汀九湾仰望汀九桥后可直接回到青山公路旁站台乘车返荃湾，免走深井段。', 'sourceUrl': KMB_TW}
        ]
    },
    'route-quarrybay': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '春秧街、怪兽大厦及鲗鱼涌公园为全平路，仅林边红屋需由柏架山道走一段约 150 米的上山缓坡；全长约 6.1 km。',
        'earlyExits': [
            {'atPlaceId': 'qb-station', 'stopIndex': 2, 'nameZh': '鲗鱼涌站（中途分流）', 'mode': 'metro', 'exitOrStop': 'A 出口（英皇道）', 'service': '港铁港岛线 / 将军澳线 · 鲗鱼涌站', 'instruction': '从北角春秧街走来后可在鲗鱼涌站提前结束，或从此处直接切入怪兽大厦与红屋后半程。', 'sourceUrl': MTR}
        ]
    },
    'route-westkowloon': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线沿西九文化区无障碍海滨步道、草坪与跨路天桥步行，平坦宽阔无陡坡。',
        'earlyExits': [
            {'atPlaceId': 'wk-mplus', 'stopIndex': 2, 'nameZh': '九龙站（艺术广场天桥捷径）', 'mode': 'metro', 'exitOrStop': 'C1 / E4 出口（经圆方广场天桥）', 'service': '港铁东涌线 / 机场快线 · 九龙站', 'instruction': '参观 M+ 后如不想绕行艺术公园西端，可直接走 M+ 北侧天桥前往九龙站。', 'sourceUrl': MTR}
        ]
    },
    'route-kowlooncity': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线由宋皇臺站经九龙城矮层街区与九龙寨城公园平缓走至乐富站，公园内仅少数园林石阶，其余平缓好走。',
        'earlyExits': [
            {'atPlaceId': 'kc-market', 'stopIndex': 2, 'nameZh': '九龙城街市 / 宋皇臺站', 'mode': 'metro', 'exitOrStop': '南行约 450 米返宋皇臺站 B2 出口', 'service': '港铁屯马线 · 宋皇臺站 / 太子道西巴士', 'instruction': '在九龙城老街区用餐或逛小店后，可在太子道西或亚皆老街乘多线巴士离开，或南返宋皇臺站。', 'sourceUrl': MTR}
        ]
    },
    'route-taipo': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '旧墟、广福桥及海滨长廊全段平坦，但走入大埔海滨公园全段后步距较长（6.4 km），登回归纪念塔需步行螺旋坡道。',
        'earlyExits': [
            {'atPlaceId': 'tp-market-station', 'stopIndex': 4, 'nameZh': '大埔墟站（半程终点）', 'mode': 'metro', 'exitOrStop': 'A2 出口（南运路）', 'service': '港铁东铁线 · 大埔墟站', 'instruction': '逛完铁路博物馆、富善街旧墟与广福桥后可在此直接结束半天散步，免走约 3 公里的海滨公园延伸段。', 'sourceUrl': MTR}
        ]
    },
    'route-taitam': {
        'climbLevel': 'moderate',
        'effortLevel': 'moderate',
        'climbNote': '自黄泥涌水塘公园起步后整体沿大潭水塘道铺装林荫道缓步下山，唯前段经阳明山庄略有起伏且末段上大潭道需走上坡台阶，全长约 5.7 km。',
        'earlyExits': [
            {'atPlaceId': 'tt-wong-nai-chung-park', 'stopIndex': 1, 'nameZh': '黄泥涌水塘公园 / 阳明山庄站', 'mode': 'bus', 'exitOrStop': '大潭水塘道口返黄泥涌峡道', 'service': '城巴 6 / 66 / 41A · 往中环或北角', 'instruction': '进入水塘谷地后途中无车可乘，如体力有限可在水塘公园起点及第一段折返黄泥涌峡道乘车离开。', 'sourceUrl': 'https://mobile.citybus.com.hk/nwp3/?f=1&ds=14&dsmode=1&l=1'}
        ]
    },
    'route-tungchung': {
        'climbLevel': 'flat',
        'effortLevel': 'moderate',
        'climbNote': '沿东涌海滨、东澳古道海边步道、马湾涌与东涌炮台全线平缓步行，仅东涌炮台城墙入口有少量石阶，全长约 5.0 km。',
        'earlyExits': [
            {'atPlaceId': 'tc-ma-wan-chung', 'stopIndex': 3, 'nameZh': '逸东邨裕东路巴士站', 'mode': 'bus', 'exitOrStop': '黎淑英纪念广场东出裕东路站', 'service': '新大屿山巴士 38 · 往东涌站', 'instruction': '走完马湾涌渔村后如需提前返程，向东步出裕东路巴士站即可乘屿巴 38 号 8 分钟直达东涌站。', 'sourceUrl': 'https://www.nlb.com.hk/en/route/47'}
        ]
    },
    'route-wongtaisin': {
        'climbLevel': 'flat',
        'effortLevel': 'easy',
        'climbNote': '全线 2.7 km 沿龙翔道平坦人行道及南莲园池平缓园林步行，志莲净苑天桥设有电梯/扶梯，整体轻松好走。',
        'earlyExits': [
            {'atPlaceId': 'wts-nan-lian', 'stopIndex': 2, 'nameZh': '钻石山站（南莲园池西门旁）', 'mode': 'metro', 'exitOrStop': 'C2 出口（凤德道 / 荷里活广场）', 'service': '港铁观塘线 / 屯马线 · 钻石山站', 'instruction': '游览南莲园池后在凤德道西门出口斜对面即是钻石山站，可随时提前进站乘车离开。', 'sourceUrl': MTR}
        ]
    }
}

for r in routes:
    rid = r['id']
    meta = ROUTE_META[rid]
    r['climbLevel'] = meta['climbLevel']
    r['climbNote'] = meta['climbNote']
    r['effortLevel'] = meta['effortLevel']
    r['earlyExits'] = meta['earlyExits']

    # Calculate sightseeing stayMinutes range
    sights_in_route = [ps[pid] for pid in dict.fromkeys(r['placeIds']) if pid in ps and ps[pid]['visitGuide']['kind'] == 'sightseeing']
    r['stayMinutes'] = [
        sum(p['visitGuide']['minutes'][0] for p in sights_in_route),
        sum(p['visitGuide']['minutes'][1] for p in sights_in_route)
    ]

    # Attach exitOrStop to every transportNode
    for n in r['transportNodes']:
        n['exitOrStop'] = NODE_EXITS[n['placeId']]

    # Ensure preferences accurately reflect climbLevel and effortLevel
    prefs = [p for p in r.get('preferences', []) if p not in ('少爬坡', '不太累')]
    if r['climbLevel'] == 'flat':
        prefs.append('少爬坡')
    if r['effortLevel'] == 'easy':
        prefs.append('不太累')
    r['preferences'] = prefs

    # Verify earlyExits indices
    for ee in r['earlyExits']:
        assert r['placeIds'][ee['stopIndex']] == ee['atPlaceId'], (rid, ee)

save(O / 'areas.json', areas)
save(O / 'routes.json', routes)
save(O / 'places.geojson', dict(type='FeatureCollection', features=[dict(type='Feature', geometry=dict(type='Point', coordinates=p['coordinates']), properties=p) for p in ps.values()]))
save(O / 'routes.geojson', dict(type='FeatureCollection', features=[f for r in routes for f in r['geometry']['features']]))
save(R / 'data/editorial/place-guides.json', guides)
save(R / 'data/editorial/route-categories.json', cats)

planned = read(O / 'planned-areas.json')
completed_names = {'北角—鲗鱼涌', '尖沙咀—西九', '九龙城', '大埔', '大潭', '东涌', '黄大仙—钻石山'}
save(O / 'planned-areas.json', [p for p in planned if p['nameZh'] not in completed_names])
print(f"Upgraded {len(routes)} routes across {len(areas)} areas and {len(ps)} places. Remaining planned: {len(read(O / 'planned-areas.json'))}")
