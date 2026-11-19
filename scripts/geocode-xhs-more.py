"""Second pass geocoding for remaining unlocated XHS hints using Traditional Chinese (HK) and landmark/mall aliases."""
import json
import pathlib
import re
import subprocess
import time
import urllib.parse

R = pathlib.Path(__file__).resolve().parents[1]
CACHE_PATH = R / 'data/raw/xhs-geocode-cache.json'
SPOTS_PATH = R / 'public/data/xhs-spots.json'
UNLOCATED_PATH = R / 'public/data/xhs-unlocated.json'

# Verified manual query mappings for remaining clear addresses/landmarks in xhs-unlocated.json
ALIASES = [
    ('园岭六街', 'sz', '园岭六街 深圳', '园岭'),
    ('正东名苑', 'sz', '正东名苑 深圳', '正东名苑'),
    ('八卦四路', 'sz', '八卦四路 深圳', '八卦四路'),
    ('南海汇', 'sz', '海上世界 深圳', '海上世界'),
    ('COCO Park', 'sz', 'COCO Park 深圳', 'COCO'),
    ('天安创新科技广场', 'sz', '天安数码城 深圳', '天安'),
    ('学府路', 'sz', '学府路 南山 深圳', '学府路'),
    ('深圳湾万象城', 'sz', '深圳湾万象城', '深圳湾万象城'),
    ('大围积富街', 'hk', '積富街 大圍 香港', '積富街'),
    ('积富街', 'hk', '積富街 大圍 香港', '積富街'),
    ('永新时代广场', 'sz', '南油 南山 深圳', '南油'),
    ('海上世界', 'sz', '海上世界 蛇口 深圳', '海上世界'),
    ('香港会议展览中心', 'hk', '香港會議展覽中心', '會議展覽中心'),
    ('侨城西街', 'sz', '侨城西街 深圳', '侨城西街'),
    ('富德楼', 'hk', '富德樓 灣仔 香港', '富德'),
    ('海下湾', 'hk', '海下灣 香港', '海下'),
    ('破边洲', 'hk', '破邊洲 香港', '破邊洲'),
    ('大屿山', 'hk', '大嶼山 香港', '大嶼山'),
    ('龙华花园新村', 'sz', '龙华公园 深圳', '龙华'),
]


def main():
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    spots = json.loads(SPOTS_PATH.read_text())
    unlocated = json.loads(UNLOCATED_PATH.read_text())
    existing_ids = {s['id'] for s in spots}

    still_unlocated = []
    added = 0

    for note in unlocated:
        blob = note['title'] + ' ' + ' '.join(note.get('hints') or [])
        matched = False
        for key, city, query, verify in ALIASES:
            if city != note['city']:
                continue
            if key not in blob:
                continue
            ckey = f'{city}:{query}'
            if ckey not in cache:
                vb = '113.8,22.15,114.45,22.6' if city == 'hk' else '113.75,22.42,114.65,22.86'
                u = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
                    'q': query, 'format': 'jsonv2', 'limit': 3, 'viewbox': vb, 'bounded': 1, 'accept-language': 'zh-CN,en'
                })
                res = subprocess.run(['curl', '-fLsS', '--max-time', '15', '-A', 'HongKongWandering-XHS/0.1', u], capture_output=True, text=True)
                cache[ckey] = json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else []
                time.sleep(1.05)

            hits = cache[ckey]
            best = next((c for c in hits if verify.lower() in ((c.get('name') or '') + ' ' + (c.get('display_name') or '')).lower()), None)
            if not best and hits:
                best = hits[0]
            if best:
                lon, lat = float(best['lon']), float(best['lat'])
                if city == 'hk' and not (113.8 < lon < 114.45 and 22.15 < lat < 22.6):
                    continue
                if city == 'sz' and not (113.75 < lon < 114.68 and 22.40 < lat < 22.86):
                    continue
                sid = f"xhs-{note['id'].replace('xhs-note-','')}-g2"
                if sid in existing_ids:
                    matched = True
                    break
                existing_ids.add(sid)
                hint0 = (note.get('hints') or [''])[0]
                name = re.split(r'[：:(（]', hint0)[0].strip() if hint0 else note['title']
                if len(name) < 2 or len(name) > 28:
                    name = note['title'][:28]
                spots.append({
                    'id': sid,
                    'city': city,
                    'name': name,
                    'category': note['category'] if note['category'] != '待分类' else '吃喝探店',
                    'coordinates': [round(lon, 6), round(lat, 6)],
                    'address': hint0 or note['title'],
                    'source': '小红书线索 + OSM Nominatim 核对',
                    'sourceUrl': f"https://www.openstreetmap.org/{best['osm_type']}/{best['osm_id']}",
                    'noteId': note['id'].replace('xhs-note-', ''),
                    'noteTitle': note['title'],
                    'noteUrl': note['noteUrl'],
                    'snippet': note['snippet'],
                })
                added += 1
                matched = True
                break
        if not matched:
            still_unlocated.append(note)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n')
    SPOTS_PATH.write_text(json.dumps(spots, ensure_ascii=False, indent=2) + '\n')
    UNLOCATED_PATH.write_text(json.dumps(still_unlocated, ensure_ascii=False, indent=2) + '\n')
    print(f'Second pass added {added} spots -> total {len(spots)} spots ({sum(s["city"]=="hk" for s in spots)} HK, {sum(s["city"]=="sz" for s in spots)} SZ), {len(still_unlocated)} unlocated left.')


if __name__ == '__main__':
    main()
