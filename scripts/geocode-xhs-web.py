"""Geocode web-verified XHS store addresses via OSM Nominatim and move them from xhs-unlocated.json into xhs-spots.json."""
import json
import pathlib
import subprocess
import time
import urllib.parse

R = pathlib.Path(__file__).resolve().parents[1]
CACHE_PATH = R / 'data/raw/xhs-geocode-cache.json'
SPOTS_PATH = R / 'public/data/xhs-spots.json'
UNLOCATED_PATH = R / 'public/data/xhs-unlocated.json'

# (match_substr_in_unlocated, city, display_name, verified_address, nominatim_query, source_note)
WEB_VERIFIED = [
    ('Something Wild', 'hk', 'Something Wild 野玩田店', '香港尖沙咀彌敦道63號 iSQUARE 國際廣場 3樓 307號舖', 'iSQUARE 香港', '联网核对(OpenRice/官网) + OSM'),
    ('黄皮小馆', 'sz', '黄皮馆茶（光明店）', '深圳市光明区羊川路三巷6-7号', '光明 深圳', '联网核对(OpenRice) + OSM'),
    ('Hey Sea', 'sz', 'HEY SEA 熹遇·见海', '深圳市大鹏新区南澳街道田洋路3号院洋疇湾花园34栋', '南澳 大鹏 深圳', '联网核对 + OSM'),
    ('深圳手工意面', 'sz', 'LLASAGNEE / Dudley’s 意面', '罗湖万象城三期L3层T305 / 福田iN城市广场LG层', '深圳万象城 罗湖', '联网核对(OpenRice) + OSM'),
    ('LOFT53', 'sz', 'LOFT53（华侨城创意园南区）', '深圳市南山区华侨城创意文化园南区锦绣北街2号', '锦绣北街 深圳', '联网核对 + OSM'),
    ('一楽焼', 'sz', '一楽·烧肉居酒屋（世界之窗店）', '深圳市南山区侨城西街22号铺', '侨城西街 深圳', '联网核对 + OSM'),
    ("BB's Studio（门牌待核）", 'sz', "BB's Studio 班班甜点铺", '深圳市福田区泰然九路1号天地源盛唐大厦（下沙站C口）', '泰然九路 深圳', '联网核对 + OSM'),
    ('La Boca', 'sz', 'La Boca 墨西哥餐厅', '深圳市南山区香山东街华侨城创意园A3栋2楼', '香山东街 深圳', '联网核对 + OSM'),
    ('新汉记', 'hk', '新汉记饭店（联和墟）', '香港新界粉岭联和墟和丰街28号囍逸商场地下G01号铺', '和豐街 粉嶺 香港', '联网核对(旅发局/OpenRice) + OSM'),
    ('ideaology', 'hk', 'Ideaology（中大文物馆）', '香港沙田香港中文大学文物馆罗桂祥阁LG1楼', '香港中文大學 文物館', '联网核对(CUHK/OpenRice) + OSM'),
    ('麻吉士林', 'sz', '麻吉士林台湾小馆（皇庭广场店）', '深圳市福田区福华路皇庭广场B1层', '皇庭广场 深圳', '联网核对(OpenRice) + OSM'),
    ('香港仔渔人码头', 'hk', '浪游渔港1773（香港仔渔人码头）', '香港南区香港仔渔人码头6号码头', '香港仔海濱公園 香港', '联网核对 + OSM'),
    ('大無烧肉', 'sz', '大無烧肉 DAIMU（卓悦中心店）', '深圳市福田区福华路卓悦中心东区', '卓悦中心 深圳', '联网核对 + OSM'),
    ('BB\'s Studio／白屿秋', 'sz', "BB's Studio（车公庙/盛唐大厦）", '深圳市福田区泰然九路1号天地源盛唐大厦', '泰然九路 深圳', '联网核对 + OSM'),
    ('多抓鱼循环商店', 'sz', '多抓鱼循环商店（深圳湾店）', '深圳市南山区科苑南路2888号深圳湾万象城B区粉红大街B1层', '深圳湾万象城', '联网核对(官网) + OSM'),
    ('MIXY BAR', 'sz', 'MIXY BAR（秘世酒吧）', '深圳市南山区华侨城兴隆西街2号3楼', '华侨城 深圳', '联网核对(OpenRice) + OSM'),
    ('小南洋精致东北菜', 'sz', '小南洋餐厅（罗湖木棉花酒店）', '深圳市罗湖区宝安南路1001号（罗湖万象城西侧）', '深圳万象城 罗湖', '联网核对(官网) + OSM'),
    ('集口福', 'sz', '集口福·吃货馆', '深圳市福田区福宁街137号 / 华强南大门坊91-7号（赤尾站E口）', '赤尾 深圳', '联网核对(OpenRice) + OSM'),
    ('普宁（陈记）食店', 'sz', '普宁（陈记）食店', '深圳市福田区福田村福新坊7栋1楼', '福田 深圳', '联网核对(大众点评/OpenRice) + OSM'),
    ('太古食堂', 'hk', '香港大学太古食堂', '香港薄扶林香港大学太古楼', '香港大學', '联网核对 + OSM'),
    ('深圳园博园', 'sz', '深圳园博园·汇芳园', '深圳市福田区竹子林西深圳园博园', '园博园 深圳', '联网核对 + OSM'),
    ('南海意库', 'sz', '南海意库街区', '深圳市南山区蛇口兴华路6号南海意库', '南海意库', '联网核对 + OSM'),
    ('徐记海鲜', 'sz', '徐记海鲜（车公庙NEO店）', '深圳市福田区深南大道6011号车公庙NEO大厦A座2层', '车公庙 深圳', '联网核对 + OSM'),
    ('空洞造咖', 'sz', 'Hollow Curry 空洞造咖', '深圳市南山区海德二道正东名苑2栋A座126', '正东名苑 深圳', '小红书线索 + OSM'),
    ('盐田海滨栈道｜是谁还没看过', 'sz', '盐田海滨栈道（全段路线参考）', '盐田海鲜街—大梅沙—小梅沙—背仔角海滨栈道', '大梅沙海滨公园', '小红书线索 + OSM'),
    ('Pasteako', 'hk', 'Pasteako（元创方）', '香港中环鸭巴甸街35号元创方B座HG01-05铺', '元創方', '联网核对(OpenRice/PMQ) + OSM'),
    ('Butlery', 'hk', 'Butlery（新城市广场）', '香港沙田正街18-19号新城市广场一期4楼479A号铺', '新城市廣場 沙田', '联网核对(OpenRice) + OSM'),
    ('Shabu Shabu Letasu', 'hk', 'Shabu Shabu Letasu（新城市广场）', '香港沙田新城市广场', '新城市廣場 沙田', '小红书线索 + OSM'),
    ('一鸣丼食堂', 'hk', '一鳴丼食堂（大埔墟）', '香港大埔运头街20-26号广安大厦地下F号铺', '運頭街 大埔 香港', '联网核对(OpenRice) + OSM'),
    ('佰味山西刀削面', 'hk', '佰味山西刀削面（大埔墟）', '香港大埔大明里1-27号宝华楼地下4A号铺', '大明里 大埔 香港', '联网核对(OpenRice) + OSM'),
    ('不做外卖的披萨店', 'sz', 'Kyta by Kytaly（万象天地）', '深圳市南山区深南大道9668号华润城万象天地', '万象天地 深圳', '联网核对 + OSM'),
    ('水库新村最最最好吃的小龙虾', 'sz', '水库新村小龙虾', '深圳市罗湖区东湖街道水库新村', '水库新村 深圳', '小红书线索 + OSM'),
    ('东海朗庭', 'sz', '深圳东海朗廷酒店法甜', '深圳市福田区深南大道7888号东海朗廷酒店', '东海朗廷酒店 深圳', '小红书线索 + OSM'),
    ('已经进场南头古城', 'sz', '南头古城胶片自扫店', '深圳市南山区南头古城', '南头古城', '小红书线索 + OSM'),
    ('深圳鸭川', 'sz', '大望村梧桐绿道 / 布吉河段', '深圳市罗湖区大望村梧桐绿道', '大望村 深圳', '小红书线索 + OSM'),
    ('沙田拉面指北', 'hk', '沙田新城市广场米其林拉面', '香港沙田新城市广场一期一楼', '新城市廣場 沙田', '小红书线索 + OSM'),
    ('happyroller', 'hk', 'Happy Roller（旺角店）', '香港九龙旺角广东道1000号地下', '廣東道 旺角 香港', '联网核对(OpenRice) + OSM'),
    ('大围小馆', 'hk', '大围小馆（大围总店）', '香港新界大围积福街92号地铺', '積福街 大圍 香港', '联网核对(官网) + OSM'),
    ('偶屋', 'sz', 'ouur 偶屋（下梅林金梅花园店）', '深圳市福田区梅林路159-13号金梅花园1栋', '下梅林 深圳', '联网核对(OpenRice) + OSM'),
    ('Sliver spoon', 'sz', 'Silver Spoon 银勺咖啡', '深圳市福田区香蜜湖特发小区11栋（香梅北站）', '香梅北 深圳', '联网核对(HK01) + OSM'),
    ('崎本的店', 'sz', '崎本的店·烘焙小镇（深圳湾）', '深圳市南山区深圳湾万象城B区粉红大街B1层', '深圳湾万象城', '联网核对(OpenRice) + OSM'),
    ('农畉LONFOOD', 'sz', 'concerto 协奏曲 / 山与 / 农畉', '福田区商报东路49号 / 华侨城创意园 / 卓悦中心', '商报东路 深圳', '联网核对(OpenRice) + OSM'),
    ('张记', 'sz', '黄贝岭潮汕炸鸡（张记）', '深圳市罗湖区黄贝岭', '黄贝岭 深圳', '小红书线索 + OSM'),
    ('华侨城创意文化园必须拥有姓名', 'sz', '华侨城创意文化园（扫街）', '深圳市南山区华侨城创意文化园北区/南区', '华侨城创意文化园', '小红书线索 + OSM'),
    ('在园岭新村里畅游', 'sz', '园岭新村漫步路线', '深圳市福田区园岭新村', '园岭新村 深圳', '小红书线索 + OSM'),
    ('深圳梅林散步学', 'sz', '梅林社区与公园散步', '深圳市福田区下梅林/梅林公园', '梅林公园 深圳', '小红书线索 + OSM'),
    ('盐田港日出', 'sz', '盐田港日出观景机位', '深圳市盐田区盐田港海滨', '盐田港 深圳', '小红书线索 + OSM'),
    ('🏖️深圳新开的', 'sz', '大鹏所城海边观海点', '深圳市大鹏新区大鹏所城海岸', '大鹏所城 深圳', '小红书线索 + OSM'),
    ('大西里生鲜肉铺', 'sz', '大西里生鲜肉铺（太子路店）', '深圳市南山区太子路8号碧涛中心103', '海上世界 深圳', '小红书线索 + OSM'),
    ('深业上城笔架山公园营地', 'sz', '深业上城·笔架山公园营地', '深圳市福田区皇岗路5001号深业上城/笔架山公园', '深业上城 深圳', '小红书线索 + OSM'),
    ('古董艺术馆里的一场旧梦', 'sz', '寻洋派古董艺术馆（永新汇店）', '深圳市南山区永新汇（南油西站C口）', '南油 深圳', '联网核对 + OSM'),
    ('山承咖啡店', 'hk', '山承咖啡厅 The Infinity Room（中大）', '香港沙田香港中文大学富尔敦楼LG05号铺', '香港中文大學', '联网核对(CUHK) + OSM'),
    ('香港鸟会地址', 'hk', '香港观鸟会（荔枝角）', '香港九龙荔枝角青山道532号伟基大厦7楼C室', '荔枝角 香港', '联网核对(官网) + OSM'),
    ('扎哈·哈迪德建筑无垠的魅力', 'sz', '深圳市当代艺术与城市规划馆（MOCAUP）', '深圳市福田区福中路184号', '福中路 深圳', '联网核对 + OSM'),
    ('大班楼订不到就来这吧', 'hk', '唐人馆 China Tang（置地广场）', '香港中环皇后大道中15号置地广场中庭4楼411-413号铺', '置地廣場 香港', '联网核对(旅发局) + OSM'),
    ('IceKey草台冰屋', 'sz', 'Ice-key 草台氷屋（园岭店）', '深圳市福田区红荔路园岭新村106栋101-1', '园岭新村 深圳', '联网核对(OpenRice) + OSM'),
    ('四喜面包', 'hk', '四喜面包西饼 Say Hey Bakery（长沙湾）', '香港长沙湾青山道500号百美工业大厦地下B6-8号铺', '青山道 長沙灣 香港', '联网核对(官网) + OSM'),
    ('贰陆/貳陆 恰巴塔三明治', 'sz', '贰陆 Sandwich·恰巴塔三明治', '深圳市福田区南园街道东园路77号', '东园路 深圳', '联网核对(OpenRice) + OSM'),
    ('富德楼', 'hk', '富德楼 Foo Tak Building（艺鹄）', '香港湾仔轩尼诗道365-367号', '軒尼詩道 灣仔 香港', '联网核对 + OSM'),
    ('官湖沙滩', 'sz', '官湖沙滩 / 金沙湾沙滩', '深圳市大鹏新区葵涌官湖海滩', '官湖 深圳', '小红书线索 + OSM'),
    ('留家厨房', 'hk', '留家厨房 Kin’s Kitchen（湾仔）', '香港湾仔轩尼诗道314-324号W Square 5楼', '軒尼詩道 灣仔 香港', '联网核对(官网) + OSM'),
    ('527 cake', 'sz', '527 克拉芙缇（园岭新村）', '深圳市福田区园岭新村23栋105号', '园岭新村 深圳', '联网核对(OpenRice) + OSM'),
    ('sokosoko', 'sz', 'SOKO SOKO·日料道场（壹方天地）', '深圳市龙华区壹方天地D区L2-035号铺', '壹方天地 深圳', '联网核对(OpenRice) + OSM'),
    ('东湖公园第41届菊花展', 'sz', '东湖公园菊花展', '深圳市罗湖区东湖公园', '东湖公园 深圳', '小红书线索 + OSM'),
    ('鲲鹏径10段', 'sz', '鲲鹏径10段（5号绿道）', '深圳市罗湖区/盐田区梧桐绿道5号绿道', '梧桐山 深圳', '小红书线索 + OSM'),
    ('大围大美督骑行', 'hk', '大围—大美督单车径', '香港沙田大围至大埔大美督海滨单车径', '大美督 香港', '小红书线索 + OSM'),
    ('丰湖大厦', 'sz', '布吉路桥洞烤鸡翅（丰湖大厦旁）', '深圳市罗湖区布吉路丰湖大厦附近', '草埔 深圳', '小红书线索 + OSM'),
    ('去了一趟海怡半岛', 'hk', '海怡半岛海滨', '香港南区鸭脷洲海怡半岛', '海怡半島 香港', '小红书线索 + OSM'),
]


def main():
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    spots = json.loads(SPOTS_PATH.read_text())
    unlocated = json.loads(UNLOCATED_PATH.read_text())
    existing_ids = {s['id'] for s in spots}

    still_unlocated = []
    added = 0

    for note in unlocated:
        blob = note['title'] + ' ' + ' '.join(note.get('hints') or []) + ' ' + (note.get('snippet') or '')
        matched = False
        for key, city, disp_name, addr, query, src_note in WEB_VERIFIED:
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
            if hits:
                best = hits[0]
                lon, lat = float(best['lon']), float(best['lat'])
                if city == 'hk' and not (113.8 < lon < 114.45 and 22.15 < lat < 22.6):
                    continue
                if city == 'sz' and not (113.75 < lon < 114.68 and 22.40 < lat < 22.86):
                    continue
                sid = f"xhs-{note['id'].replace('xhs-note-','')}-w"
                if sid not in existing_ids:
                    existing_ids.add(sid)
                    spots.append({
                        'id': sid,
                        'city': city,
                        'name': disp_name,
                        'category': note['category'] if note['category'] != '待分类' else '吃喝探店',
                        'coordinates': [round(lon, 6), round(lat, 6)],
                        'address': addr,
                        'source': src_note,
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
    print(f'Web search pass added {added} spots -> total {len(spots)} spots ({sum(s["city"]=="hk" for s in spots)} HK, {sum(s["city"]=="sz" for s in spots)} SZ), {len(still_unlocated)} unlocated left.')


if __name__ == '__main__':
    main()
