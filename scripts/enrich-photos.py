"""Attach reviewed Commons photographs to existing POIs; record verified EXIF GPS camera position when available."""
import html
import json
import math
import pathlib
import re

R = pathlib.Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())

def clean(s):
    return html.unescape(re.sub('<[^>]+>', '', s)).strip()

def haversine(lon1, lat1, lon2, lat2):
    rad = math.pi / 180
    return 6371000 * 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) * rad / 2) ** 2 +
        math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin((lon2 - lon1) * rad / 2) ** 2
    ))

selected = read(R / 'data/editorial/place-photos.json')
data = read(R / 'public/data/places.geojson')

verified_count = 0
doc_rows = []

for f in data['features']:
    p = f['properties']
    selection = selected.get(p['id'])
    p.pop('photo', None)
    if not selection:
        continue
    raw = read(R / 'data/raw/photos' / selection['rawFile'])
    page = raw['query']['pages'][str(selection['pageId'])]
    i = page['imageinfo'][0]
    m = i['extmetadata']
    assert m['LicenseShortName']['value'].startswith(('CC BY', 'CC0', 'Public domain'))
    assert page['title'].lower().endswith(('.jpg', '.jpeg', '.png'))
    lic_url = m['LicenseUrl']['value'].replace('http://creativecommons.org/', 'https://creativecommons.org/')
    photo_obj = {
        'url': i['thumburl'],
        'sourceUrl': i['descriptionurl'],
        'author': clean(m['Artist']['value']),
        'license': m['LicenseShortName']['value'],
        'licenseUrl': lic_url,
        'caption': selection['caption'],
        'width': i['thumbwidth'],
        'height': i['thumbheight'],
        'capturedAt': clean(m.get('DateTimeOriginal', {}).get('value', ''))[:120],
        'checkedAt': '2026-11-16',
        'locationKind': 'poi-representative',
    }
    gps_lat = m.get('GPSLatitude', {}).get('value')
    gps_lon = m.get('GPSLongitude', {}).get('value')
    if gps_lat and gps_lon:
        try:
            clat = float(gps_lat)
            clon = float(gps_lon)
            dist = haversine(p['coordinates'][0], p['coordinates'][1], clon, clat)
            if dist <= 350:
                photo_obj['cameraCoordinates'] = [round(clon, 6), round(clat, 6)]
                photo_obj['cameraDistanceMeters'] = round(dist)
                photo_obj['locationKind'] = 'camera-verified'
                verified_count += 1
        except Exception:
            pass
    p['photo'] = photo_obj
    loc_label = f"已核实拍摄机位（距代表点约 {photo_obj['cameraDistanceMeters']} m）" if photo_obj['locationKind'] == 'camera-verified' else '景点代表位置'
    doc_rows.append((selection['caption'], photo_obj['author'], photo_obj['license'], photo_obj['licenseUrl'], photo_obj['sourceUrl'], loc_label))

(R / 'public/data/places.geojson').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

# Update docs/PHOTOS.md
md_lines = [
    '# 地点照片来源',
    '',
    f'2026-11-16 核对。共 {len(doc_rows)} 张实景照片（其中 {verified_count} 张含经过距离校验 <= 350m 的 EXIF 拍摄机位坐标，其余采用 POI 代表位置，不推断未提供坐标的机位）。按需加载 Commons 缩略图，保留作者、原图与许可；局部裁切展示，不修改源图。',
    '',
    '| 地点 / 画面 | 摄影作者 | 授权 | 机位核实 | 原图 |',
    '| --- | --- | --- | --- | --- |',
]
for cap, author, lic, lic_url, src_url, loc_label in doc_rows:
    safe_cap = cap.replace('|', '\\|')
    safe_auth = author.replace('|', '\\|')
    md_lines.append(f'| {safe_cap} | {safe_auth} | [{lic}]({lic_url}) | {loc_label} | [Commons]({src_url}) |')

md_lines.append('')
md_lines.append('编辑源：`data/editorial/place-photos.json`；原始元数据：`data/raw/photos/`；升级与重建：`python3 scripts/upgrade-photos.py && python3 scripts/enrich-photos.py`。照片不代表实时现场；加载失败时仍保留定位与路线功能。')
(R / 'docs/PHOTOS.md').write_text('\n'.join(md_lines) + '\n')

print(f'Attached {len(doc_rows)} reviewed photographs ({verified_count} with verified camera GPS).')
