"""Fetch real OSRM footway geometry for CUHK walking trails, shortcuts, and cycling paths."""
import json
import pathlib
import subprocess
import time

R = pathlib.Path(__file__).resolve().parents[1]
SPOTS_PATH = R / 'public/data/xhs-spots.json'

# Key verified CUHK building/node coordinates from xhs-spots.json
# Map spot_id -> list of [lon, lat] waypoints along the real path
TRAIL_WAYPOINTS = {
    'xhs-cuhk-fac-walk-yia-escalator': [
        [114.21020, 22.41330],  # 港铁大学站 A 口
        [114.21103, 22.41639],  # 康本国际学术园 YIA
        [114.20890, 22.41660],  # 崇基学院 / 文质堂
    ],
    'xhs-cuhk-fac-walk-erb-9f': [
        [114.20890, 22.41660],  # 崇基 / 善衡
        [114.20732, 22.41820],  # 蒙民伟工程学大楼 ERB
        [114.20630, 22.41950],  # 大学本部百万大道
    ],
    'xhs-cuhk-fac-walk-mmw-7f': [
        [114.20540, 22.41960],  # 大学图书馆
        [114.20780, 22.41970],  # 基本医学大楼
        [114.20915, 22.42017],  # 蒙民伟楼 MMW
        [114.20960, 22.42140],  # 新亚书院 / 合一亭
    ],
    'xhs-cuhk-fac-walk-lsk-3f': [
        [114.20540, 22.41960],  # 大学图书馆
        [114.20410, 22.41980],  # 李兆基楼 LSK
        [114.20490, 22.42100],  # 联合书院
    ],
    'xhs-cuhk-fac-walk-for-green': [
        [114.21020, 22.41330],  # 大学站
        [114.20890, 22.41620],  # 未圆湖
        [114.20520, 22.41840],  # 范克廉楼
        [114.20540, 22.41960],  # 大学图书馆
        [114.20900, 22.42120],  # 新亚书院
    ],
    'xhs-cuhk-fac-bike-track': [
        [114.21020, 22.41330],  # 港铁大学站
        [114.21160, 22.41850],  # 环迴东路
        [114.20720, 22.42580],  # 第39区北闸 / 罗桂祥综合生物医学大楼
    ],
    'xhs-cuhk-fac-trail-alumni': [
        [114.20712, 22.42029],  # 邵逸夫堂 / 金禧承泽园
        [114.20610, 22.41900],  # 润昌堂
        [114.20880, 22.41680],  # 崇基校友径
    ],
}


def fetch_osrm_foot(waypoints):
    coords_str = ';'.join(f'{lon},{lat}' for lon, lat in waypoints)
    url = f'https://routing.openstreetmap.de/routed-foot/route/v1/foot/{coords_str}?overview=full&geometries=geojson'
    res = subprocess.run(['curl', '-fLsS', '--max-time', '15', '-A', 'HongKongWandering-XHS/0.1', url], capture_output=True, text=True)
    if res.returncode != 0 or not res.stdout.strip():
        return None
    data = json.loads(res.stdout)
    routes = data.get('routes') or []
    if not routes:
        return None
    r = routes[0]
    geom = r['geometry']
    dist = round(r.get('distance', 0))
    return {
        'type': 'FeatureCollection',
        'features': [{
            'type': 'Feature',
            'properties': {'distance': dist, 'mode': 'walk'},
            'geometry': geom,
        }],
    }, dist


def main():
    spots = json.loads(SPOTS_PATH.read_text())
    by_id = {s['id']: s for s in spots}
    updated = 0
    for sid, wps in TRAIL_WAYPOINTS.items():
        if sid not in by_id:
            print('Missing spot:', sid)
            continue
        res = fetch_osrm_foot(wps)
        if not res:
            print('OSRM failed for:', sid)
            continue
        fc, dist = res
        by_id[sid]['geometry'] = fc
        pts = len(fc['features'][0]['geometry']['coordinates'])
        print(f'Updated {sid}: {pts} pts, ~{dist}m')
        updated += 1
        time.sleep(0.6)

    SPOTS_PATH.write_text(json.dumps(spots, ensure_ascii=False, indent=2))
    print(f'Done: updated geometry on {updated} CUHK trails/shortcuts')


if __name__ == '__main__':
    main()
