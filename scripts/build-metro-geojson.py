#!/usr/bin/env python3
"""Build public/data/metro.geojson from /tmp/xianggang-*.json and /tmp/shenzhen-*.json.

Coordinates from luxueyan/generate-china-subways-geojson are already in WGS84
(verified against OSM nodes for HK University Station and SZ Luohu Station).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "public" / "data" / "metro.geojson"

SOURCES = [
    ("hk", Path("/tmp/xianggang-line.json"), Path("/tmp/xianggang-station.json")),
    ("sz", Path("/tmp/shenzhen-line.json"), Path("/tmp/shenzhen-station.json")),
]


def round_coords(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 5), round(coords[1], 5)]
    return [round_coords(c) for c in coords]


def norm_color(raw: str) -> str:
    c = (raw or "666666").strip().lstrip("#")
    if len(c) == 6:
        return "#" + c.upper()
    return "#666666"


def main():
    features = []
    line_count = 0
    stations_by_key = {}

    for city, line_file, st_file in SOURCES:
        with open(line_file, encoding="utf-8") as f:
            lines_fc = json.load(f)
        for ft in lines_fc.get("features", []):
            props = ft.get("properties", {})
            geom = ft.get("geometry", {})
            if not geom.get("coordinates"):
                continue
            line_count += 1
            features.append({
                "type": "Feature",
                "properties": {
                    "kind": "line",
                    "city": city,
                    "name": props.get("name", ""),
                    "short": props.get("short", props.get("name", "")),
                    "color": norm_color(props.get("color", "")),
                },
                "geometry": {
                    "type": geom["type"],
                    "coordinates": round_coords(geom["coordinates"]),
                },
            })

        with open(st_file, encoding="utf-8") as f:
            st_fc = json.load(f)
        for ft in st_fc.get("features", []):
            props = ft.get("properties", {})
            geom = ft.get("geometry", {})
            coords = geom.get("coordinates")
            name = (props.get("name") or "").strip()
            if not coords or not name:
                continue
            key = (city, name)
            line_short = (props.get("pshort") or props.get("pname") or "").strip()
            color = norm_color(props.get("color", ""))
            if key not in stations_by_key:
                stations_by_key[key] = {
                    "type": "Feature",
                    "properties": {
                        "kind": "station",
                        "city": city,
                        "name": name,
                        "color": color,
                        "lines": [line_short] if line_short else [],
                        "interchange": False,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": round_coords(coords),
                    },
                }
            else:
                existing = stations_by_key[key]["properties"]
                if line_short and line_short not in existing["lines"]:
                    existing["lines"].append(line_short)
                existing["interchange"] = len(existing["lines"]) > 1

    for st in stations_by_key.values():
        st["properties"]["lineLabel"] = " / ".join(st["properties"].pop("lines"))
        features.append(st)

    out_fc = {"type": "FeatureCollection", "features": features}
    OUT_PATH.write_text(json.dumps(out_fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"Wrote {OUT_PATH} ({size_kb:.1f} KB): {line_count} line segments, {len(stations_by_key)} unique stations")


if __name__ == "__main__":
    main()
