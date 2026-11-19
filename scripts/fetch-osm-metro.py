#!/usr/bin/env python3
"""Fetch real curved subway track geometry & stations from OpenStreetMap API 0.6.

Uses route_master relation IDs for Hong Kong MTR and Shenzhen Metro,
fetches one route relation per branch (avoiding duplicate return directions),
stitches contiguous ways into LineStrings, and writes public/data/metro.geojson.
"""
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "public" / "data" / "metro.geojson"
CACHE_DIR = Path("/tmp/osm_metro_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "hong-kong-wandering/1.0 (metro-builder)"}

HK_LINES = [
    (6452936, "观塘线", "#00AB4F"),
    (269670, "港岛线", "#007DC5"),
    (1139477, "迪士尼线", "#EB81B9"),
    (272132, "东铁线", "#69C7F4"),
    (9736612, "将军澳线", "#793E8C"),
    (269671, "东涌线", "#FFA500"),
    (269669, "荃湾线", "#FC0601"),
    (272133, "屯马线", "#871C2A"),
    (6827213, "南港岛线", "#B8D201"),
    (272078, "机场快线", "#008187"),
]

SZ_LINES = [
    (7913936, "1号线", "#00AB39"),
    (13176924, "2号线", "#B35A1F"),
    (9629887, "3号线", "#01A2E2"),
    (7713538, "4号线", "#CC0000"),
    (9645952, "5号线", "#96499A"),
    (11583149, "6号线", "#008187"),
    (14953716, "6号线支线", "#008187"),
    (9629866, "7号线", "#2249A3"),
    (13176926, "8号线", "#B35A1F"),
    (9699772, "9号线", "#86656D"),
    (11583622, "10号线", "#EB81B9"),
    (9318442, "11号线", "#741D51"),
    (14944729, "12号线", "#A192B2"),
    (18470806, "13号线", "#DD7E00"),
    (14764338, "14号线", "#F2C75C"),
    (15059918, "16号线", "#1E5192"),
    (13620411, "20号线", "#00B2A9"),
]


def fetch_json(url: str, cache_name: str) -> dict:
    cache_file = CACHE_DIR / cache_name
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.15)
    return data


def norm_color(raw: str, fallback: str) -> str:
    c = (raw or "").strip()
    if c.startswith("#") and len(c) == 7:
        return c.upper()
    if len(c) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in c):
        return "#" + c.upper()
    return fallback


def stitch_ways(way_node_lists: list[list[int]]) -> list[list[int]]:
    """Stitch contiguous OSM ways into longer polylines."""
    chains = [list(w) for w in way_node_lists if len(w) >= 2]
    if not chains:
        return []
    merged = True
    while merged:
        merged = False
        i = 0
        while i < len(chains):
            a = chains[i]
            j = i + 1
            while j < len(chains):
                b = chains[j]
                if a[-1] == b[0]:
                    a.extend(b[1:])
                    chains.pop(j)
                    merged = True
                    continue
                if a[-1] == b[-1]:
                    a.extend(reversed(b[:-1]))
                    chains.pop(j)
                    merged = True
                    continue
                if a[0] == b[-1]:
                    chains[i] = b[:-1] + a
                    a = chains[i]
                    chains.pop(j)
                    merged = True
                    continue
                if a[0] == b[0]:
                    chains[i] = list(reversed(b[1:])) + a
                    a = chains[i]
                    chains.pop(j)
                    merged = True
                    continue
                j += 1
            i += 1
    return chains


TRAD_TO_SIMP = str.maketrans({
    "環": "环", "龍": "龙", "灣": "湾", "東": "东", "啟": "启", "圍": "围",
    "學": "学", "奧": "奥", "運": "运", "臺": "台", "寶": "宝", "將": "将",
    "軍": "军", "恆": "恒", "會": "会", "機": "机", "場": "场", "島": "岛",
    "園": "园", "烏": "乌", "頭": "头", "硤": "硖", "門": "门", "嶺": "岭",
    "紅": "红", "羅": "罗", "興": "兴", "藍": "蓝", "營": "营", "盤": "盘",
    "觀": "观", "調": "调", "鐘": "钟", "銅": "铜", "鑼": "锣", "錦": "锦",
    "鑽": "钻", "長": "长", "顯": "显", "徑": "径", "馬": "马", "黃": "黄",
    "鐵": "铁", "線": "线", "館": "馆", "聯": "联", "萬": "万", "華": "华",
})


def clean_station_name(raw: str) -> str:
    n = (raw or "").strip()
    if n.startswith("MTR "):
        n = n[4:].strip()
    # Strip trailing English in mixed names like "中環 Central" -> keep Chinese part if present
    parts = n.split()
    if len(parts) > 1 and any("\u4e00" <= ch <= "\u9fff" for ch in parts[0]):
        n = parts[0]
    if n.endswith("站") and len(n) > 2:
        n = n[:-1]
    return n.translate(TRAD_TO_SIMP)


def select_branch_relations(master_rel: dict) -> list[int]:
    """Pick one route relation per distinct branch (avoiding reverse direction duplicates)."""
    if master_rel.get("tags", {}).get("route") == "subway":
        return [master_rel["id"]]
    rel_ids = [m["ref"] for m in master_rel.get("members", []) if m.get("type") == "relation"]
    if len(rel_ids) <= 1:
        return rel_ids
    chosen = []
    seen_pairs = set()
    for rid in rel_ids:
        data = fetch_json(f"https://api.openstreetmap.org/api/0.6/relation/{rid}.json", f"rel_{rid}.json")
        els = data.get("elements", [])
        if not els:
            continue
        tags = els[0].get("tags", {})
        if tags.get("route") != "subway":
            continue
        frm = tags.get("from", "").strip()
        to = tags.get("to", "").strip()
        pair = tuple(sorted([frm, to]))
        if frm and to and pair in seen_pairs:
            continue
        if frm and to:
            seen_pairs.add(pair)
        chosen.append(rid)
    return chosen or rel_ids[:1]


def process_city(city: str, lines: list[tuple[int, str, str]], stations_by_key: dict, features: list):
    for master_id, line_name, fallback_color in lines:
        try:
            mdata = fetch_json(
                f"https://api.openstreetmap.org/api/0.6/relation/{master_id}.json",
                f"rel_{master_id}.json",
            )
        except Exception as e:
            print(f"WARN: failed master {master_id} ({line_name}): {e}")
            continue
        m_el = mdata["elements"][0]
        m_tags = m_el.get("tags", {})
        color = norm_color(m_tags.get("colour", ""), fallback_color)

        branch_ids = select_branch_relations(m_el)
        print(f"[{city}] {line_name} ({color}): branches={branch_ids}")

        for rid in branch_ids:
            try:
                full = fetch_json(
                    f"https://api.openstreetmap.org/api/0.6/relation/{rid}/full.json",
                    f"full_{rid}.json",
                )
            except Exception as e:
                print(f"WARN: failed full {rid} ({line_name}): {e}")
                continue

            nodes = {}
            ways = {}
            rel_el = None
            for el in full.get("elements", []):
                t = el.get("type")
                if t == "node":
                    nodes[el["id"]] = el
                elif t == "way":
                    ways[el["id"]] = el
                elif t == "relation" and el["id"] == rid:
                    rel_el = el
            if not rel_el:
                continue

            r_tags = rel_el.get("tags", {})
            r_color = norm_color(r_tags.get("colour", ""), color)

            track_ways = []
            for mem in rel_el.get("members", []):
                mtype = mem.get("type")
                role = mem.get("role", "")
                ref = mem.get("ref")
                if mtype == "way" and role in ("", "forward", "backward"):
                    w = ways.get(ref)
                    if w and len(w.get("nodes", [])) >= 2:
                        # Skip platform ways if tagged as platform
                        wtags = w.get("tags", {})
                        if wtags.get("public_transport") == "platform" or wtags.get("railway") == "platform":
                            continue
                        track_ways.append(w["nodes"])
                elif mtype == "node" and "stop" in role:
                    nd = nodes.get(ref)
                    if not nd:
                        continue
                    ntags = nd.get("tags", {})
                    raw_name = ntags.get("name:zh-Hans") or ntags.get("name:zh") or ntags.get("name") or ""
                    st_name = clean_station_name(raw_name)
                    if not st_name:
                        continue
                    coord = [round(nd["lon"], 5), round(nd["lat"], 5)]
                    key = (city, st_name)
                    if key not in stations_by_key:
                        stations_by_key[key] = {
                            "type": "Feature",
                            "properties": {
                                "kind": "station",
                                "city": city,
                                "name": st_name,
                                "color": r_color,
                                "lines": [line_name],
                                "interchange": False,
                            },
                            "geometry": {"type": "Point", "coordinates": coord},
                            "_raw_coords": [coord],
                        }
                    else:
                        stations_by_key[key]["_raw_coords"].append(coord)
                        ex = stations_by_key[key]["properties"]
                        if line_name not in ex["lines"]:
                            ex["lines"].append(line_name)
                        ex["interchange"] = len(ex["lines"]) > 1

            stitched = stitch_ways(track_ways)
            coords_list = []
            for chain in stitched:
                pts = []
                for nid in chain:
                    nd = nodes.get(nid)
                    if nd:
                        pts.append([round(nd["lon"], 5), round(nd["lat"], 5)])
                if len(pts) >= 2:
                    coords_list.append(pts)

            if not coords_list:
                continue
            geom = (
                {"type": "LineString", "coordinates": coords_list[0]}
                if len(coords_list) == 1
                else {"type": "MultiLineString", "coordinates": coords_list}
            )
            features.append({
                "type": "Feature",
                "properties": {
                    "kind": "line",
                    "city": city,
                    "name": line_name,
                    "color": r_color,
                },
                "geometry": geom,
            })


def _seg_intersect(a1, a2, b1, b2):
    """Return 2D intersection (x, y) of segments a1-a2 and b1-b2, or None."""
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def _nearest_on_seg(p, a, b):
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    d2 = dx * dx + dy * dy
    if d2 < 1e-15:
        return a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / d2))
    return (ax + t * dx, ay + t * dy)


def snap_stations(features: list, stations_by_key: dict):
    """Snap every station dot dead-center onto its rendered track(s)."""
    segs_by_line = {}
    for ft in features:
        if ft["properties"]["kind"] != "line":
            continue
        key = (ft["properties"]["city"], ft["properties"]["name"])
        geom = ft["geometry"]
        lines = [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]
        lst = segs_by_line.setdefault(key, [])
        for coords in lines:
            for i in range(len(coords) - 1):
                lst.append((coords[i], coords[i + 1]))

    snapped_count = 0
    for st in stations_by_key.values():
        raw_pts = st.pop("_raw_coords", [])
        if not raw_pts:
            continue
        cx = sum(p[0] for p in raw_pts) / len(raw_pts)
        cy = sum(p[1] for p in raw_pts) / len(raw_pts)
        city = st["properties"]["city"]
        line_names = st["properties"]["lines"]

        best_pt = None
        # For interchange stations, prefer exact track crossing within ~250m of stop centroid
        if len(line_names) >= 2:
            best_d2 = 0.0025 ** 2
            for i in range(len(line_names)):
                s1 = [s for s in segs_by_line.get((city, line_names[i]), []) if abs(s[0][0] - cx) < 0.01 and abs(s[0][1] - cy) < 0.01]
                for j in range(i + 1, len(line_names)):
                    s2 = [s for s in segs_by_line.get((city, line_names[j]), []) if abs(s[0][0] - cx) < 0.01 and abs(s[0][1] - cy) < 0.01]
                    for a1, a2 in s1:
                        for b1, b2 in s2:
                            ix = _seg_intersect(a1, a2, b1, b2)
                            if ix:
                                d2 = (ix[0] - cx) ** 2 + (ix[1] - cy) ** 2
                                if d2 < best_d2:
                                    best_d2 = d2
                                    best_pt = ix

        # Otherwise snap centroid onto nearest point of rendered tracks for this station's lines
        if best_pt is None:
            best_d2 = 0.003 ** 2
            for ln in line_names:
                for a, b in segs_by_line.get((city, ln), []):
                    if abs(a[0] - cx) > 0.01 and abs(b[0] - cx) > 0.01:
                        continue
                    q = _nearest_on_seg((cx, cy), a, b)
                    d2 = (q[0] - cx) ** 2 + (q[1] - cy) ** 2
                    if d2 < best_d2:
                        best_d2 = d2
                        best_pt = q

        if best_pt is not None:
            st["geometry"]["coordinates"] = [round(best_pt[0], 5), round(best_pt[1], 5)]
            snapped_count += 1
    print(f"Snapped {snapped_count}/{len(stations_by_key)} stations onto rendered tracks")


def main():
    features = []
    stations_by_key = {}
    process_city("hk", HK_LINES, stations_by_key, features)
    process_city("sz", SZ_LINES, stations_by_key, features)
    snap_stations(features, stations_by_key)

    for st in stations_by_key.values():
        st["properties"]["lineLabel"] = " / ".join(st["properties"].pop("lines"))
        features.append(st)

    out_fc = {"type": "FeatureCollection", "features": features}
    OUT_PATH.write_text(json.dumps(out_fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    line_feats = sum(1 for f in features if f["properties"]["kind"] == "line")
    print(f"Wrote {OUT_PATH} ({size_kb:.1f} KB): {line_feats} line geometries, {len(stations_by_key)} unique stations")


if __name__ == "__main__":
    main()
