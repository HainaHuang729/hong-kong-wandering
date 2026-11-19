"""Add CUHK (香港中文大学) campus restaurants, canteens and cafes with OSM Nominatim building coordinates."""
import json
import math
import pathlib
import subprocess
import time
import urllib.parse

R = pathlib.Path(__file__).resolve().parents[1]
CACHE_PATH = R / 'data/raw/xhs-geocode-cache.json'
SPOTS_PATH = R / 'public/data/xhs-spots.json'

CUHK_SOURCE_URL = 'https://www.cuhk.edu.hk/chinese/campus/catering.html'

# (id_slug, name, category, building_query, address, note_title, snippet)
CUHK_DINING = [
    ('bf-student', '范克廉樓學生膳堂（大膳堂）', '吃喝探店', '范克廉樓 香港中文大學', '香港沙田香港中文大学范克廉楼地下', '中大校园餐饮指南 · 中央校园', '提供大众化港式快餐、烧味及早午晚餐，中大中央校园核心大食堂。'),
    ('bf-veg', '范克廉樓素食餐廳（LG14）', '吃喝探店', '范克廉樓 香港中文大學', '香港沙田香港中文大学范克廉楼低层地下LG14', '中大校园餐饮指南 · 中央校园', '位于范克廉楼低层地下，主打中大校内平价素食餐点。'),
    ('bf-staff', '范克廉樓教職員餐廳', '吃喝探店', '范克廉樓 香港中文大學', '香港沙田香港中文大学范克廉楼地下', '中大校园餐饮指南 · 中央校园', '提供特色米线、川沪菜肴及中式小菜（部分时段开放予公众）。'),
    ('bf-coffee', '范克廉樓咖啡閣（Coffee Corner）', '咖啡甜品', '范克廉樓 香港中文大學', '香港沙田香港中文大学范克廉楼地下', '中大校园餐饮指南 · 中央校园', '提供简餐、西式包点与咖啡饮品。'),
    ('fulton-untitled', '流白咖啡 Untitled Coffee（富爾敦樓）', '咖啡甜品', '富爾敦樓 香港中文大學', '香港沙田香港中文大学富尔敦楼LG05号铺', '中大校园餐饮指南 · 接棒山承原址', '2026 年 8 月接替原“山承咖啡厅”开业的 CU-SuCCeSS 新一届学生咖啡店，主打酸种面包与单品手冲咖啡。'),
    ('lsk-snack', '李兆基樓小食店 / 咖啡室', '咖啡甜品', '李兆基樓 香港中文大學', '香港沙田香港中文大学李兆基楼低层地下', '中大校园餐饮指南 · 中央校园', '提供三文治、沙律、意粉、餐汤及咖啡。'),
    ('med-can', '李卓敏基本醫學大樓小食店（Med Can）', '吃喝探店', '李卓敏基本醫學大樓 香港中文大學', '香港沙田香港中文大学李卓敏基本医学大楼地下', '中大校园餐饮指南 · 中央校园', '医学院师生热门聚点，提供简餐及小食。'),
    ('psc-paper', '龐萬倫學生中心 Paper & Coffee（龐Can）', '咖啡甜品', '龐萬倫學生中心 香港中文大學', '香港沙田香港中文大学庞万伦学生中心2楼', '中大校园餐饮指南 · 崇基/中央校园', '文青风格校园咖啡室，提供精品咖啡及西式轻食。'),
    ('yia-cafe330', '康本國際學術園 Café 330（YIA Café）', '咖啡甜品', '康本國際學術園 香港中文大學', '香港沙田香港中文大学康本国际学术园1楼101A室', '中大校园餐饮指南 · 近港铁大学站', '社会企业咖啡店，提供轻食、咖啡及烘焙包点。'),
    ('lwc-cafe', '李慧珍樓咖啡室', '咖啡甜品', '李慧珍樓 香港中文大學', '香港沙田香港中文大学李慧珍楼G04室', '中大校园餐饮指南 · 崇基学院区', '位于信和楼旁李慧珍楼，提供咖啡及简餐。'),
    ('lwc-halal', '李慧珍樓清真餐廳（Halal Food Outlet）', '吃喝探店', '李慧珍樓 香港中文大學', '香港沙田香港中文大学李慧珍楼地下', '中大校园餐饮指南 · 崇基学院区', '中大校园内符合清真（Halal）标准的餐厅。'),
    ('lwc-ebeneezer', 'Ebeneezer’s Kebabs & Pizzeria（中大店）', '吃喝探店', '李慧珍樓 香港中文大學', '香港沙田香港中文大学李慧珍楼G05室', '中大校园餐饮指南 · 崇基学院区', '提供中东烤肉卷（Kebabs）及现烤薄饼（Pizza）。'),
    ('cc-chungchitang', '眾志堂（崇基學院學生膳堂）', '吃喝探店', '眾志堂 香港中文大學', '香港沙田香港中文大学崇基学院众志堂', '中大校园餐饮指南 · 崇基学院', '崇基学院核心学生大饭堂，提供多款早午晚餐及宵夜。'),
    ('cc-orchid', '蘭苑（Orchid Lodge）', '咖啡甜品', '蘭苑 香港中文大學', '香港沙田香港中文大学崇基学院兰苑', '中大校园餐饮指南 · 崇基学院', '崇基学院西式餐室，环境清幽，适合轻食与下午茶。'),
    ('cc-staff', '崇基學院教職員聯誼會會所', '吃喝探店', '崇基學院禮拜堂 香港中文大學', '香港沙田香港中文大学崇基学院礼拜堂对面', '中大校园餐饮指南 · 崇基学院', '提供中西餐点与聚会用餐（主要招待会员及教职员）。'),
    ('cyt-stage', '鄭裕彤樓 The Stage', '咖啡甜品', '鄭裕彤樓 香港中文大學', '香港沙田香港中文大学郑裕彤楼3楼', '中大校园餐饮指南 · 近港铁大学站', '位于商学院郑裕彤楼，提供西式简餐、咖啡与轻食。'),
    ('univ-maxims', '美心MX（港鐵大學站）', '吃喝探店', '大學站 香港中文大學', '香港沙田港铁大学站出口旁', '中大校园餐饮指南 · 出入口快餐', '位于港铁大学站出口旁，出站进校最便捷的快餐选择。'),
    ('cumc-cafe', '中大醫院 Cafe Yuanyang & Inspire', '咖啡甜品', '香港中文大學醫院', '香港沙田香港中文大学医院地下及低层地下', '中大校园餐饮指南 · 医疗中心', '校内外人士均可前往的餐饮与咖啡空间。'),
    ('na-canteen', '新亞書院學生餐廳（新亞Can）', '吃喝探店', '新亞書院 香港中文大學', '香港沙田香港中文大学新亚书院', '中大校园餐饮指南 · 新亚书院', '位于山顶，坐拥吐露港开阔海景，提供地道烧味与港式快餐。'),
    ('na-coffee', '新亞書院咖啡店', '咖啡甜品', '新亞書院 香港中文大學', '香港沙田香港中文大学新亚书院', '中大校园餐饮指南 · 新亚书院', '课间休憩喝咖啡与简餐好去处。'),
    ('na-yunchi', '雲起軒（新亞書院）', '吃喝探店', '雲起軒 香港中文大學', '香港沙田香港中文大学新亚书院水塔旁', '中大校园餐饮指南 · 新亚书院', '新亚书院地标景观餐厅（主要招待会员）。'),
    ('uc-canteen', '聯合書院學生餐廳（開心軒）', '吃喝探店', '張祝珊師生康樂大樓 香港中文大學', '香港沙田香港中文大学联合书院张祝珊师生康乐大楼地下', '中大校园餐饮指南 · 联合书院', '提供多元早午晚餐及粉面档。'),
    ('uc-staff', '聯合書院教職員餐廳（聚賢軒）', '吃喝探店', '張祝珊師生康樂大樓 香港中文大學', '香港沙田香港中文大学联合书院张祝珊师生康乐大楼地下', '中大校园餐饮指南 · 联合书院', '联合书院教职员餐厅。'),
    ('uc-siyuan', '思源館（Si Yuan Amenities Centre）', '酒吧饮品', '思源館 香港中文大學', '香港沙田香港中文大学联合书院思源馆', '中大校园餐饮指南 · 联合书院', '中大校园内唯一领有酒牌的休闲会所，提供小食、特饮及啤酒。'),
    ('shaw-seeyou', 'SeeYou@Shaw（逸夫書院學生餐廳）', '吃喝探店', '逸夫書院 香港中文大學', '香港沙田香港中文大学逸夫书院', '中大校园餐饮指南 · 逸夫书院', '提供多样化快餐、饭盒及 Fusion Dining 堂食。'),
    ('ms-canteen', '晨興書院餐廳（晨Can）', '吃喝探店', '晨興書院 香港中文大學', '香港沙田香港中文大学晨兴书院', '中大校园餐饮指南 · 晨兴书院', '晨兴书院宴会厅兼日常食堂。'),
    ('shho-canteen', '善衡書院學生飯堂（善Can）', '吃喝探店', '善衡書院 香港中文大學', '香港沙田香港中文大学善衡书院', '中大校园餐饮指南 · 善衡书院', '空间现代化，提供高性价比港式及特色套餐。'),
    ('cwc-canteen', '敬文書院餐廳', '吃喝探店', '敬文書院 香港中文大學', '香港沙田香港中文大学敬文书院', '中大校园餐饮指南 · 敬文书院', '规模精巧的书院食堂，主要服务敬文书院师生。'),
    ('lws-canteen', '伍宜孫書院學生飯堂 & 咖啡店', '吃喝探店', '伍宜孫書院 香港中文大學', '香港沙田香港中文大学伍宜孙书院', '中大校园餐饮指南 · 伍宜孙书院', '含学生饭堂、咖啡店及教职员饭堂。'),
    ('ws-pavilion', '和聲書院 WS Pavilion（和Can）', '吃喝探店', '和聲書院 香港中文大學', '香港沙田香港中文大学和声书院', '中大校园餐饮指南 · 和声书院', '提供丰富的中西快餐与面食。'),
    ('ws-shanghai', '和聲滬軒（中大上海菜）', '吃喝探店', '和聲書院 香港中文大學', '香港沙田香港中文大学和声书院', '中大校园餐饮指南 · 和声书院', '中大校内知名上海菜馆，招牌小笼包与沪菜点心。'),
    ('ws-tolo', 'Café Tolo（和聲書院咖啡）', '咖啡甜品', '和聲書院 香港中文大學', '香港沙田香港中文大学和声书院', '中大校园餐饮指南 · 和声书院', '提供咖啡及轻食，近吐露港风光。'),
]


def query_nominatim(cache, query):
    ckey = f'hk:{query}'
    if ckey not in cache:
        u = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({
            'q': query,
            'format': 'jsonv2',
            'limit': 3,
            'viewbox': '114.195,22.408,114.222,22.432',
            'bounded': 1,
            'accept-language': 'zh-CN,en',
        })
        res = subprocess.run(['curl', '-fLsS', '--max-time', '15', '-A', 'HongKongWandering-XHS/0.1', u], capture_output=True, text=True)
        cache[ckey] = json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else []
        time.sleep(1.05)
    return cache[ckey]


def main():
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    spots = json.loads(SPOTS_PATH.read_text())
    existing_ids = {s['id'] for s in spots}

    # Fallback coordinate: CUHK central campus
    fallback_hits = query_nominatim(cache, '香港中文大學')
    bldg_coords = {}
    added = 0
    seen_coords = {}

    for slug, name, cat, bquery, addr, ntitle, snip in CUHK_DINING:
        sid = f'xhs-cuhk-{slug}'
        if sid in existing_ids:
            continue
        if bquery not in bldg_coords:
            hits = query_nominatim(cache, bquery)
            if not hits:
                # Try shorter query without 香港中文大學 suffix if needed, else fallback
                short_q = bquery.replace(' 香港中文大學', '') + ' 沙田 香港'
                hits = query_nominatim(cache, short_q) or fallback_hits
            bldg_coords[bquery] = hits[0] if hits else None

        best = bldg_coords[bquery]
        if not best:
            continue
        lon, lat = float(best['lon']), float(best['lat'])
        # Apply small deterministic spiral offset if multiple outlets share the exact building point
        ck = (round(lon, 5), round(lat, 5))
        idx = seen_coords.get(ck, 0)
        seen_coords[ck] = idx + 1
        if idx > 0:
            angle = idx * 2.1
            lon += math.cos(angle) * 0.00018
            lat += math.sin(angle) * 0.00015

        spots.append({
            'id': sid,
            'city': 'hk',
            'name': name,
            'category': cat,
            'coordinates': [round(lon, 6), round(lat, 6)],
            'address': addr,
            'source': '中大官方餐饮名录 + OSM',
            'sourceUrl': f"https://www.openstreetmap.org/{best['osm_type']}/{best['osm_id']}",
            'noteId': f'cuhk-{slug}',
            'noteTitle': ntitle,
            'noteUrl': CUHK_SOURCE_URL,
            'snippet': snip,
        })
        existing_ids.add(sid)
        added += 1

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    SPOTS_PATH.write_text(json.dumps(spots, ensure_ascii=False, indent=2))
    hk_n = sum(1 for s in spots if s['city'] == 'hk')
    sz_n = sum(1 for s in spots if s['city'] == 'sz')
    print(f'Added {added} CUHK dining spots -> total {len(spots)} spots ({hk_n} HK, {sz_n} SZ)')


if __name__ == '__main__':
    main()
