"""Import curated Hong Kong & Shenzhen Xiaohongshu spots from ../xhs/outputs/map-data.json."""
import json
import pathlib

XHS_DATA = pathlib.Path('/Users/amadeus/Documents/ChatGPT/工具/xhs/outputs/map-data.json')
OUT = pathlib.Path(__file__).resolve().parents[1] / 'public/data/xhs-spots.json'


def main():
    raw = json.loads(XHS_DATA.read_text())
    rows = raw if isinstance(raw, list) else raw.get('rows') or raw.get('notes') or raw.get('items') or []
    spots = []
    seen = set()
    for r in rows:
        locs = [l for l in (r.get('locations') or []) if l.get('lat') and (l.get('lng') or l.get('lon'))]
        for idx, l in enumerate(locs):
            lng = float(l.get('lng') or l.get('lon'))
            lat = float(l['lat'])
            if not (113.75 <= lng <= 114.68 and 22.15 <= lat <= 22.86):
                continue
            addr = str(l.get('address') or '')
            name = str(l.get('name') or '未命名地点').strip()
            is_hk = lat < 22.47 or '香港' in addr or any(k in name for k in ('香港', 'M+', '大馆', 'Fiata', 'Pizza Project', 'H Queen'))
            city = 'hk' if is_hk else 'sz'
            sid = f"xhs-{r['id']}-{idx}"
            if sid in seen:
                continue
            seen.add(sid)
            spots.append({
                'id': sid,
                'city': city,
                'name': name,
                'category': str(r.get('category') or '吃喝探店'),
                'coordinates': [round(lng, 6), round(lat, 6)],
                'address': addr,
                'source': str(l.get('source') or ''),
                'sourceUrl': str(l.get('source_url') or ''),
                'noteId': str(r['id']),
                'noteTitle': str(r.get('title') or ''),
                'noteUrl': str(r.get('url') or ''),
                'snippet': ' '.join(str(r.get('content') or '').split())[:200],
            })
    OUT.write_text(json.dumps(spots, ensure_ascii=False, indent=2) + '\n')
    hk = sum(1 for s in spots if s['city'] == 'hk')
    sz = sum(1 for s in spots if s['city'] == 'sz')
    print(f'Exported {len(spots)} XHS spots ({hk} HK, {sz} SZ) -> {OUT}')


if __name__ == '__main__':
    main()
