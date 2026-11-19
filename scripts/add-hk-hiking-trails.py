#!/usr/bin/env python3
"""Add 8 classic Hong Kong hiking trails (MacLehose, Wilson, Lantau) with OSRM foot geometry."""
import json
import math
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "public" / "data"
RAW_DIR = ROOT / "data" / "raw"

SRC_AFCD = "https://www.hiking.gov.hk/trail"
SRC_TD = "https://www.td.gov.hk/tc/transport_in_hong_kong/public_transport/index.html"
SRC_KMB = "https://www.kmb.hk/"
SRC_NLB = "https://www.nlb.com.hk/"
SRC_CITYBUS = "https://www.citybus.com.hk/"
SRC_MTR = "https://www.mtr.com.hk/"
STATIC_NOTE = "静态资料，不含实时班次、临时改道或天气封山信息。行山请自备充足饮水、防晒与离线地图。"


def dist_m(a, b):
    r = math.pi / 180
    return 6371000 * 2 * math.asin(
        math.sqrt(
            math.sin((b[1] - a[1]) * r / 2) ** 2
            + math.cos(a[1] * r) * math.cos(b[1] * r) * math.sin((b[0] - a[0]) * r / 2) ** 2
        )
    )


def make_place(pid, name_zh, name_en, coord, osm_url, area_id, cats, highlights, mins, transport_info=None, priority=180, city="hk"):
    is_transport = transport_info is not None
    if is_transport:
        mode, service, exit_or_stop, t_url, arrival_steps = transport_info
        if len(arrival_steps) < 2:
            arrival_steps = list(arrival_steps) + ["下车或出站后留意官方郊游径标距柱与路牌指示，核对方向再起步。"]
    else:
        t_url = SRC_AFCD
        arrival_steps = [
            f"沿官方行山径／郊游径路标步行前往{name_zh}。",
            "山径部分路段无树荫或有碎石陡坡，请按体能与天气情况及时调整行程。",
        ]
    guide = {
        "kind": "transport" if is_transport else "sightseeing",
        "minutes": [0, 0] if is_transport else mins,
        "durationNote": "郊野交通接驳点，候车及班次间隔另计。" if is_transport else "行山途经停留与观景建议时间，不含全程步行耗时。",
        "highlights": highlights,
        "arrivalSteps": arrival_steps,
        "transportSourceUrl": t_url,
        "contentSourceUrl": SRC_AFCD,
        "checkedAt": "2026-11-17",
        "transportNote": STATIC_NOTE,
    }
    return {
        "id": pid,
        "city": city,
        "nameZh": name_zh,
        "nameEn": name_en,
        "coordinates": coord,
        "district": area_id,
        "categories": list(cats),
        "description": "；".join(highlights) + "。",
        "sourceUrl": SRC_AFCD,
        "coordinateSource": osm_url,
        "coordinateKind": "OSM 路网 / 山径节点坐标，非无障碍入口。",
        "verifiedAt": "2026-11-17",
        "priority": priority,
        "visitDuration": 0 if is_transport else round(sum(mins) / 2),
        "visitGuide": guide,
        "dataLicense": "https://opendatacommons.org/licenses/odbl/1-0/",
        "attribution": "© OpenStreetMap contributors",
    }


TRAILS = [
    {
        "area_id": "maclehose-1",
        "route_id": "route-maclehose-1",
        "nameZh": "麦理浩径第一段·东坝破边洲",
        "nameEn": "MacLehose Sec. 1 · East Dam & Po Pin Chau",
        "title": "麦理浩径第一段精华：万宜水库东坝、六角岩柱与破边洲",
        "area_desc": "世界地质公园级的火山六角岩柱群与海蚀断崖，从东坝步行接驳破边洲观景台再探浪茄湾。",
        "route_desc": "由万宜水库东坝出发，先沿检猪湾山脊望向破边洲海蚀柱，再沿麦理浩径第一段步入白沙细软的浪茄湾。",
        "duration": "半天",
        "visitMinutes": 240,
        "stayMinutes": [50, 90],
        "climbLevel": "moderate",
        "effortLevel": "moderate",
        "climbNote": "东坝至破边洲及浪茄湾山脊有连续石阶与碎石坡，需穿防滑行山鞋并注意悬崖边缘。",
        "transport": "周末及公众假期可于北潭涌或西贡市中心乘新界专线小巴 9A 直达万宜水库东坝；平日需乘的士入东坝。",
        "transportSource": SRC_TD,
        "weather": "东坝及浪茄湾全段无遮荫，强风或雷暴天气请勿靠近破边洲崖边。",
        "notes": "东坝与浪茄湾沿途无补给商店，出发前请备足至少 1.5L 饮水；注意 9A 小巴仅于周六日及公众假期营运。",
        "interests": ["自然风光", "山海脊线", "地质奇观"],
        "preferences": ["慢慢走", "看海看风景"],
        "categoryNotes": {
            "山海之间": "万宜水库东坝六角火山岩柱、破边洲海蚀柱与浪茄湾海湾串联。",
        },
        "places": [
            ("mh1-east-dam", "万宜水库东坝（9A 小巴站）", "High Island Reservoir East Dam", [114.3715347, 22.3619760], "https://www.openstreetmap.org/node/8219682498",
             ["世界地质公园六角凝灰岩柱群", "9A 专线小巴及的士落客起点"], [0, 0],
             ("bus", "新界专线小巴 9A（北潭涌⇄万宜水库东坝）", "东坝纪念碑旁小巴站", SRC_TD, ["北潭涌乘 9A 专线小巴（假日）或西贡乘的士直达万宜水库东坝。"])),
            ("mh1-po-pin-chau", "破边洲观景台", "Po Pin Chau Viewpoint", [114.3784988, 22.3583810], "https://www.openstreetmap.org/way/191174810",
             ["近距离俯瞰百米高海蚀柱与六角岩壁", "检猪湾海蚀拱门全景机位"], [25, 45], None),
            ("mh1-long-ke", "浪茄湾营地（麦径一段）", "Long Ke Wan", [114.3763933, 22.3742660], "https://www.openstreetmap.org/way/85964199",
             ["香港最美细白沙滩之一与翡翠海湾", "麦理浩径第一段终点接第二段起点"], [0, 0],
             ("bus", "原路折返东坝乘 9A / 的士，或续接麦径二段往西湾亭", "浪茄湾凉亭", SRC_AFCD, ["浪茄湾无车路直达，可原路折返万宜水库东坝乘车，或继续行经西湾山往西湾亭离开。"])),
        ],
        "early_exits": [
            (1, "mh1-po-pin-chau", "破边洲观景台", "bus", "原路折返东坝（约 25 分钟）", "9A 小巴 / 的士", "看完破边洲后若体力有限，可直接折返东坝乘车，无需翻山入浪茄湾。", SRC_TD),
        ],
    },
    {
        "area_id": "maclehose-2",
        "route_id": "route-maclehose-2",
        "nameZh": "麦理浩径第二段·大浪西湾",
        "nameEn": "MacLehose Sec. 2 · Sai Wan & Ham Tin",
        "title": "麦理浩径第二段精华：西湾亭、大浪西湾、咸田湾到北潭凹",
        "area_desc": "被誉为香港最美海岸行山径，一次走遍西湾、咸田湾双白沙滩与独木桥，翻越大浪坳至北潭凹。",
        "route_desc": "自西湾亭轻装切入吹筒坳，下山即见大浪西湾与咸田湾独木桥士多，最后翻越大浪坳抵达北潭凹乘车。",
        "duration": "一整天",
        "visitMinutes": 360,
        "stayMinutes": [60, 100],
        "climbLevel": "moderate",
        "effortLevel": "challenging",
        "climbNote": "咸田湾翻越大浪坳至赤径、北潭凹路段起伏较大，全程约 12 公里以上。",
        "transport": "西贡亲民街麦当劳旁乘村巴 NR29 至西湾亭起步；终点北潭凹可乘九巴 94 / 96R 返回西贡或钻石山。",
        "transportSource": SRC_KMB,
        "weather": "西湾至大浪坳暴晒路段长，夏季务必防晒补水；暴雨后独木桥及石涧慎行。",
        "notes": "西湾村及咸田湾均有士多可补给冻饮与简餐；北潭凹 94 路巴士班次约 30 分钟一班。",
        "interests": ["山海脊线", "离岛海湾", "自然风光"],
        "preferences": ["慢慢走", "看海看风景"],
        "categoryNotes": {
            "山海之间": "西湾亭经大浪西湾、咸田湾独木桥翻越大浪坳至北潭凹，集齐麦径二段精华。",
        },
        "places": [
            ("mh2-sai-wan-pavilion", "西湾亭（NR29 村巴站）", "Sai Wan Pavilion", [114.3601171, 22.3947462], "https://www.openstreetmap.org/way/276177720",
             ["村巴 NR29 落客起点", "俯瞰万宜水库东端与西湾山入口"], [0, 0],
             ("bus", "居民巴士 NR29（西贡亲民街⇄西湾亭）", "西湾亭回旋处", SRC_TD, ["于西贡市中心亲民街乘 NR29 村巴（或乘的士）直达西湾亭起步。"])),
            ("mh2-sai-wan-beach", "大浪西湾沙滩", "Sai Wan Beach", [114.370985, 22.397835], "https://www.openstreetmap.org/node/1200111392",
             ["水清沙幼的西贡东大浪湾首滩", "西湾村士多补给及海景木台"], [25, 45], None),
            ("mh2-ham-tin", "咸田湾独木桥", "Ham Tin Wan", [114.3753998, 22.4092191], "https://www.openstreetmap.org/way/245413792",
             ["标志性咸田湾独木桥与海湾冲浪滩", "安记／海风士多休息补给点"], [25, 45], None),
            ("mh2-pak-tam-au", "北潭凹（94 / 96R 巴士站）", "Pak Tam Au", [114.3327823, 22.4200024], "https://www.openstreetmap.org/node/1184038995",
             ["麦理浩径第二段终点与第三段起点", "九巴 94 往西贡／96R 往钻石山接驳站"], [0, 0],
             ("bus", "九巴 94（往西贡）／ 96R（假日往钻石山）", "北潭凹巴士站", SRC_KMB, ["于北潭路北潭凹巴士站乘九巴 94 回西贡，或假日乘 96R 直出钻石山港铁站。"])),
        ],
        "early_exits": [
            (1, "mh2-sai-wan-beach", "大浪西湾沙滩", "bus", "折返西湾亭乘 NR29", "村巴 NR29 / 快艇（旺季）", "若不想翻越大浪坳，可于西湾折返西湾亭（约 40 分钟）乘村巴回西贡。", SRC_TD),
        ],
    },
    {
        "area_id": "maclehose-4",
        "route_id": "route-maclehose-4",
        "nameZh": "麦理浩径第四段·昂平高原",
        "nameEn": "MacLehose Sec. 4 · Ngong Ping Plateau",
        "title": "麦理浩径第四段精华：水浪窝、马鞍山昂平高原到大水坑",
        "area_desc": "香港罕见的高山大草原「昂平高原」，居高临下俯瞰西贡海、白沙湾与大金钟金字塔峰。",
        "route_desc": "从西沙路水浪窝起步沿麦径四段登高至开阔的昂平高原草地，远眺大金钟与西贡内海，再经梅子林下山直抵港铁大水坑站。",
        "duration": "半天",
        "visitMinutes": 270,
        "stayMinutes": [40, 70],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "水浪窝上攀昂平高原需连续登升约 400 米石阶，下山往梅子林路段坡度较陡。",
        "transport": "马鞍山／沙田乘九巴 99 或 299X 至水浪窝站起步；终点步行接入港铁屯马线大水坑站。",
        "transportSource": SRC_KMB,
        "weather": "昂平高原风大无树荫，秋季芒草季周末游人较多，注意保暖防风。",
        "notes": "昂平高原无小卖部，建议于马鞍山或西贡先买好补给；下山经梅子林村路后即接入大水坑住宅区。",
        "interests": ["山海脊线", "草原视野", "自然风光"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "昂平高山草原俯瞰西贡海与大金钟山峰，串联麦理浩径四段与屯马线。",
        },
        "places": [
            ("mh4-shui-long-wo", "水浪窝（99 / 299X 巴士站）", "Shui Long Wo", [114.2783992, 22.4042410], "https://www.openstreetmap.org/node/2528904731",
             ["麦理浩径第四段起点及观星台旁登山口", "九巴 99 / 299X 巴士接驳站"], [0, 0],
             ("bus", "九巴 99（恒安⇄西贡）／ 299X（沙田⇄西贡）", "水浪窝巴士站", SRC_KMB, ["于沙田市中心或马鞍山乘九巴 299X／99 至水浪窝站下车起步。"])),
            ("mh4-ngong-ping", "昂平高原营地（大金钟观景）", "Ngong Ping Campsite", [114.2512319, 22.3922522], "https://www.openstreetmap.org/way/1044693898",
             ["海拔 400 米高山草坡与滑翔伞起飞场", "270 度俯瞰西贡海、滘西洲与大金钟峰"], [35, 60], None),
            ("mh4-tai-shui-hang", "港铁大水坑站（终点）", "MTR Tai Shui Hang Station", [114.2227469, 22.4084775], "https://www.openstreetmap.org/way/41856916",
             ["港铁屯马线接驳离开", "梅子林下山道尽头"], [0, 0],
             ("metro", "港铁屯马线", "大水坑站 A/B 出口", SRC_MTR, ["由昂平经梅子林下山，经行人隧道接驳港铁大水坑站乘屯马线离开。"])),
        ],
        "early_exits": [
            (1, "mh4-ngong-ping", "昂平高原营地（大金钟观景）", "bus", "改走马鞍山村道下耀安邨", "新界绿巴 84R / 步行至马鞍山站", "若不想经梅子林长坡下大水坑，可由昂平往北下马鞍山郊野公园凉亭，步行或乘车往马鞍山站。", SRC_TD),
        ],
    },
    {
        "area_id": "maclehose-5",
        "route_id": "route-maclehose-5",
        "nameZh": "麦理浩径第五段·狮子山",
        "nameEn": "MacLehose Sec. 5 · Lion Rock",
        "title": "麦理浩径第五段：沙田坳、狮子山脊线、毕架山到大埔道",
        "area_desc": "香港最经典城市脊线，沿着狮子山狮头与毕架山一路向西，脚下即是九龙半岛与维多利亚港全景。",
        "route_desc": "由沙田坳狮子亭踏入麦理浩径第五段，先经回归亭登顶狮子山俯瞰九龙与维港，再沿着山脊翻越毕架山与鹰巢山接大埔道。",
        "duration": "半天",
        "visitMinutes": 270,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "沙田坳至狮子山顶及毕架山沿途石阶陡峭，狮头崖边风大且无护栏，拍照请勿跨越警示线。",
        "transport": "黄大仙站乘小巴 18M 至慈云山法藏寺步行上沙田坳；终点大埔道眺望处乘九巴 72 / 81 返回市区。",
        "transportSource": SRC_KMB,
        "weather": "脊线全程曝露于强风与日照下，黄昏看维港夜景需自备头灯并注意安全。",
        "notes": "沙田坳狮子亭周末有恒益商店可补给豆腐花与饮水；毕架山段有野生猕猴出没，切勿手提胶袋或喂食。",
        "interests": ["山海脊线", "城市全景", "经典地标"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "狮子山与毕架山脊线横跨九龙群山，将维港与新界沙田景色尽收眼底。",
        },
        "places": [
            ("mh5-shatin-pass", "沙田坳狮子亭", "Sha Tin Pass", [114.1993019, 22.3561546], "https://www.openstreetmap.org/node/9217451834",
             ["麦理浩径第五段核心补给驿站", "慈云山与大老山交汇路口"], [0, 0],
             ("bus", "九龙专线小巴 18M（黄大仙⇄慈云山法藏寺）+ 步行上坡约 20 分钟", "法藏寺小巴总站", SRC_TD, ["于黄大仙港铁站乘 18M 小巴至法藏寺，沿沙田坳道步行约 20 分钟至狮子亭。"])),
            ("mh5-lion-rock", "狮子山顶观景台", "Lion Rock Summit", [114.1871656, 22.3530064], "https://www.openstreetmap.org/node/1167628556",
             ["海拔 495 米香港精神地标", "360 度俯瞰九龙半岛、维多利亚港与沙田谷"], [25, 45], None),
            ("mh5-beacon-hill", "毕架山观景台", "Beacon Hill", [114.1703900, 22.3497540], "https://www.openstreetmap.org/node/5437296836",
             ["海拔 457 米雷达站旁脊线平台", "西九龙与青衣海港落日绝佳机位"], [15, 25], None),
            ("mh5-taipo-road", "大埔道眺望处（72 / 81 巴士站）", "Tai Po Road Lookout", [114.1605744, 22.3586533], "https://www.openstreetmap.org/node/2666815553",
             ["麦理浩径第五段终点", "九巴 72 / 81 往深水埗、太子或沙田"], [0, 0],
             ("bus", "九巴 72（太和⇄长沙湾）／ 81（禾輋⇄佐敦）", "石梨贝水塘 / 大埔道巴士站", SRC_KMB, ["下抵大埔公路石梨贝水塘／大埔道巴士站乘 72 或 81 返回市区或沙田。"])),
        ],
        "early_exits": [
            (1, "mh5-lion-rock", "狮子山顶观景台", "bus", "由回归亭下狮子山公园往黄大仙", "步行至天马苑 / 黄大仙站（约 35 分钟）", "登顶狮子山后若不继续走毕架山，可经回归亭下坡往狮子山公园直接离开。", SRC_MTR),
        ],
    },
    {
        "area_id": "maclehose-8",
        "route_id": "route-maclehose-8",
        "nameZh": "麦理浩径第八段·大帽山",
        "nameEn": "MacLehose Sec. 8 · Tai Mo Shan",
        "title": "麦理浩径第八段：荃锦坳、香港之巅大帽山道到铅矿坳与城门",
        "area_desc": "攀登香港最高峰大帽山（957 米），沿大帽山道盘旋看云海日落与芒草山坡，再经四方山、铅矿坳下走城门水塘。",
        "route_desc": "自荃锦坳郊野公园站起步，沿全港最高车行山道缓坡攀上大帽山雷达站旁观景弯，再跨过四方山草坡与铅矿坳直抵城门水塘菠萝坝。",
        "duration": "一整天",
        "visitMinutes": 330,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "全段从海拔 490 米攀升至 930 米以上后再连续下坡至城门水塘，全程约 13 公里。",
        "transport": "荃湾如心广场／港铁荃湾站乘九巴 51 至荃锦坳（郊野公园站）起步；终点菠萝坝乘小巴 82 直返荃湾兆和街。",
        "transportSource": SRC_KMB,
        "weather": "大帽山山顶气温常比市区低 6–8°C 且多雾强风，请携带防风外套。",
        "notes": "大帽山顶雷达站为禁区不可入内，沿闸前麦理浩径主路旁四方山凉亭绕行；荃锦坳有大帽山茶水亭可补给。",
        "interests": ["高山云海", "自然风光", "山海脊线"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "香港之巅大帽山与四方山草坡连走城门水塘，是麦理浩径最高海拔路段。",
        },
        "places": [
            ("mh8-tsuen-kam-au", "荃锦坳（51 巴士站）", "Tsuen Kam Au", [114.1049149, 22.4088354], "https://www.openstreetmap.org/node/9250902183",
             ["麦理浩径第八段西端入口", "九巴 51 郊野公园站与茶水亭补给"], [0, 0],
             ("bus", "九巴 51（荃湾西站⇄上村）", "大帽山郊野公园站", SRC_KMB, ["于港铁荃湾站或荃湾西站乘九巴 51 至大帽山郊野公园（荃锦坳）下车起步。"])),
            ("mh8-tai-mo-shan", "大帽山观景山道", "Tai Mo Shan", [114.1245950, 22.4101175], "https://www.openstreetmap.org/node/1852935107",
             ["海拔 957 米香港最高峰山脊公路", "秋冬季云海、日落与大片芒草坡"], [30, 50], None),
            ("mh8-lead-mine-pass", "铅矿坳营地", "Lead Mine Pass", [114.1581428, 22.4123139], "https://www.openstreetmap.org/node/7059808056",
             ["麦理浩径第七段与第八段分界点", "卫奕信径交汇林荫休息亭"], [15, 25], None),
            ("mh8-pineapple-dam", "菠萝坝（82 小巴总站）", "Pineapple Dam", [114.1440780, 22.3845509], "https://www.openstreetmap.org/way/23368182",
             ["城门水塘主入口与自然教育中心", "专线小巴 82 直达荃湾兆和街"], [0, 0],
             ("bus", "新界专线小巴 82（菠萝坝⇄荃湾兆和街）", "城门水塘菠萝坝小巴总站", SRC_TD, ["从铅矿坳沿麦径七段方向下城门水塘至菠萝坝，乘 82 号小巴返回荃湾。"])),
        ],
        "early_exits": [
            (2, "mh8-lead-mine-pass", "铅矿坳营地", "bus", "往北下大埔元墩下", "新界小巴 23K（元墩下⇄大埔墟站）", "抵达铅矿坳后若想改往大埔，可向北沿着卫奕信径下山至元墩下村乘 23K 小巴往大埔墟站。", SRC_TD),
        ],
    },
    {
        "area_id": "maclehose-10",
        "route_id": "route-maclehose-10",
        "nameZh": "麦理浩径十段·千岛湖",
        "nameEn": "MacLehose Sec. 10 · Thousand Island Lake",
        "title": "大榄涌水塘「香港千岛湖」：扫管笏、千岛湖清景台到大棠红叶谷",
        "area_desc": "俯瞰大榄涌水塘十余座翠绿湖中小岛，路线平缓易行，串联麦理浩径第十段与大棠枫香林。",
        "route_desc": "由扫管笏沿麦理浩径第十段缓步上山，登上千岛湖清景台俯瞰星罗棋布的水塘岛屿，续经黄泥墩水塘走至大棠山道乘 K66 离开。",
        "duration": "半天",
        "visitMinutes": 210,
        "stayMinutes": [35, 60],
        "climbLevel": "moderate",
        "effortLevel": "easy",
        "climbNote": "全段多为泥沙宽径与林荫斜坡，仅千岛湖清景台前有一小段梯级，整体轻松好走。",
        "transport": "屯门站乘港铁巴士 K53（或小巴 43）至扫管笏起步；终点大棠山道可乘 K66 巴士返回朗屏站。",
        "transportSource": SRC_MTR,
        "weather": "秋冬 12 月至 1 月大棠枫香转红时节人流较旺，K66 假日会加开特别班次。",
        "notes": "沿途树荫较多但无固定商店，建议自备饮水；清景台木栈道风大，注意防晒。",
        "interests": ["湖光山色", "自然风光", "轻松行山"],
        "preferences": ["慢慢走", "不太累", "看海看风景"],
        "categoryNotes": {
            "山海之间": "大榄涌水塘群岛景观搭配麦理浩径第十段林道，适合新手与半日轻松行山。",
        },
        "places": [
            ("mh10-so-kwun-wat", "扫管笏（K53 / 43 小巴站）", "So Kwun Wat", [114.0017553, 22.3751909], "https://www.openstreetmap.org/node/7030857415",
             ["扫管笏村登山入口", "麦理浩径第十段旁支接入点"], [0, 0],
             ("bus", "港铁巴士 K53（屯门站循环）／ 小巴 43", "扫管笏村总站", SRC_MTR, ["于港铁屯门站乘 K53 巴士或新界小巴 43 至扫管笏总站下车起步。"])),
            ("mh10-viewpoint", "千岛湖清景台", "Tai Lam Chung Reservoir Viewpoint", [114.0241566, 22.3909362], "https://www.openstreetmap.org/node/6515848087",
             ["香港版千岛湖全景木平台", "俯瞰大榄涌水塘十余座湖心小岛"], [25, 40], None),
            ("mh10-tai-tong", "大棠山道（K66 巴士站）", "Tai Tong Shan Road", [114.0358918, 22.4060212], "https://www.openstreetmap.org/way/95649480",
             ["大棠枫香林与郊野公园出口", "港铁巴士 K66 往朗屏／元朗"], [0, 0],
             ("bus", "港铁巴士 K66（大棠山道⇄朗屏站）", "大棠山道巴士站", SRC_MTR, ["沿大棠山道步行下山至巴士站，乘港铁巴士 K66 直达朗屏港铁站。"])),
        ],
        "early_exits": [
            (1, "mh10-viewpoint", "千岛湖清景台", "bus", "原路折返扫管笏（约 45 分钟）", "K53 巴士 / 小巴 43", "看完千岛湖全景后可原路下撤至扫管笏乘车回屯门。", SRC_MTR),
        ],
    },
    {
        "area_id": "lantau-sunset-peak",
        "route_id": "route-lantau-sunset-peak",
        "nameZh": "凤凰径二段·大东山",
        "nameEn": "Lantau Trail Sec. 2 · Sunset Peak",
        "title": "凤凰径第二段：伯公坳、大东山烂头营芒草脊线到南山",
        "area_desc": "香港第三高峰大东山（869 米），每逢深秋整片山头化为金色芒草海，山脊散布百年传教士石屋烂头营。",
        "route_desc": "自东涌道高点伯公坳直上天梯石阶，穿过漫山芒草与古老石屋群登临大东山观景台，再顺二东山脊线稳步下走南山营地。",
        "duration": "半天",
        "visitMinutes": 270,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "伯公坳起步即连续攀升 500 米陡峭石梯，下山往南山石阶亦较长，对膝盖有一定考验。",
        "transport": "东涌站乘新大屿山巴士 3M / 11 / 23 至伯公坳站下车起步；终点南山营地乘 3M 返回东涌或梅窝。",
        "transportSource": SRC_NLB,
        "weather": "山脊海拔高且无遮挡，日落后气温骤降；拍日落需带足头灯及保暖衣物。",
        "notes": "烂头营石屋为私人度假屋，请勿攀爬屋顶或破坏石墙；南山营地有洗手间与自动饮水机。",
        "interests": ["山海脊线", "秋季芒草", "日落云海"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "凤凰径最经典的金色芒草高山脊线，俯瞰贝澳海湾与南大屿海岸。",
        },
        "places": [
            ("lt2-pak-kung-au", "伯公坳（3M / 11 / 23 巴士站）", "Pak Kung Au", [113.9432200, 22.2481465], "https://www.openstreetmap.org/node/1917264532",
             ["凤凰径第二段与第三段交汇高点", "大屿山巴士 3M / 11 / 23 落客即见登山牌坊"], [0, 0],
             ("bus", "新大屿山巴士 3M / 11 / 23（东涌市中心起步）", "伯公坳巴士站", SRC_NLB, ["于东涌港铁站外巴士总站乘 3M、11 或 23 号巴士至伯公坳站下车起步。"])),
            ("lt2-sunset-peak", "大东山二号观景台（烂头营）", "Sunset Peak Viewpoint", [113.9570311, 22.2562033], "https://www.openstreetmap.org/node/14383739130",
             ["海拔 869 米山脊与百年石屋群", "深秋金色芒草与贝澳湾海景"], [35, 60], None),
            ("lt2-nam-shan", "南山营地（3M 巴士站）", "Nam Shan Campsite", [113.9893198, 22.2496814], "https://www.openstreetmap.org/node/9870969673",
             ["凤凰径第二段终点与林荫烧烤营地", "屿巴 3M 往梅窝码头或东涌站"], [0, 0],
             ("bus", "新大屿山巴士 3M（梅窝⇄东涌）", "南山巴士站", SRC_NLB, ["下抵屿南道南山巴士站，乘 3M 巴士前往梅窝码头转渡轮或返回东涌站。"])),
        ],
        "early_exits": [
            (1, "lt2-sunset-peak", "大东山二号观景台（烂头营）", "bus", "原路下伯公坳（约 60 分钟）", "屿巴 3M / 11 / 23", "若不走长坡往南山，可在大东山看完芒草后原路返回伯公坳乘巴士下山。", SRC_NLB),
        ],
    },
    {
        "area_id": "wilson-1",
        "route_id": "route-wilson-1",
        "nameZh": "卫奕信径第一段·孖岗山",
        "nameEn": "Wilson Trail Sec. 1 · Violet Hill & The Twins",
        "title": "卫奕信径第一段：黄泥涌峡、紫罗兰山翻越孖岗山至赤柱峡",
        "area_desc": "港岛经典魔鬼石阶挑战线，连续翻越紫罗兰山与孪生双峰孖岗山，俯瞰浅水湾与赤柱半岛双海湾。",
        "route_desc": "自黄泥涌峡沿紫罗兰山径缓步而上，接浅水湾坳后一口气挑战孖岗山南北双峰千级石阶，居高望尽赤柱与大潭海湾。",
        "duration": "半天",
        "visitMinutes": 240,
        "stayMinutes": [35, 60],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "孖岗山有超过千级极陡石阶，俗称「港岛天梯」，务必量力而行并备足饮水。",
        "transport": "中环／铜锣湾乘城巴 6 / 66 / 76 至黄泥涌水塘公园（黄泥涌峡）起步；终点赤柱峡道乘 6 / 6X / 260 离开。",
        "transportSource": SRC_CITYBUS,
        "weather": "孖岗山脊无遮荫且石阶曝晒，夏季建议清晨或傍晚前完成。",
        "notes": "黄泥涌峡有加油站与自动售卖机可最后补给；下抵赤柱峡道后向南步行数分钟即达赤柱广场与海滨。",
        "interests": ["山海脊线", "海湾全景", "体力挑战"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "紫罗兰山与孖岗山双峰连走，俯瞰浅水湾、深水湾与赤柱半岛海湾。",
        },
        "places": [
            ("ws1-wong-nai-chung", "黄泥涌峡（6 / 66 / 76 巴士站）", "Wong Nai Chung Gap", [114.1928608, 22.2581043], "https://www.openstreetmap.org/node/8781211670",
             ["港岛中部重要山隘与卫奕信径紫罗兰山入口", "城巴 6 / 66 / 76 直达"], [0, 0],
             ("bus", "城巴 6 / 66 / 76（中环／铜锣湾出发）", "黄泥涌水塘公园巴士站", SRC_CITYBUS, ["于中环交易广场乘城巴 6 或 66 至黄泥涌水塘公园站下车起步。"])),
            ("ws1-violet-hill", "紫罗兰山脊", "Violet Hill", [114.1987678, 22.2478454], "https://www.openstreetmap.org/way/1061013226",
             ["海拔 436 米俯瞰大潭水塘群与浅水湾", "接连浅水湾坳的平缓山腰小径"], [20, 30], None),
            ("ws1-the-twins", "孖岗山双峰", "The Twins", [114.2065520, 22.2294475], "https://www.openstreetmap.org/way/956281697",
             ["港岛南部标志性孪生双峰与千级天梯", "赤柱半岛、春坎角与南中国海绝佳视野"], [20, 35], None),
            ("ws1-stanley-gap", "赤柱峡道（卫径一段起点）", "Stanley Gap", [114.2099899, 22.2247457], "https://www.openstreetmap.org/way/956281695",
             ["卫奕信径第一段起点牌坊", "步行接赤柱峡道／赤柱广场乘 6 / 6X / 260 离开"], [0, 0],
             ("bus", "城巴 6 / 6X / 260（赤柱⇄中环）", "赤柱峡道 / 赤柱广场巴士站", SRC_CITYBUS, ["下抵赤柱峡道后沿行人路走往赤柱广场或马坑邨乘城巴 6、6X 或 260 返回市区。"])),
        ],
        "early_exits": [
            (1, "ws1-violet-hill", "紫罗兰山脊", "bus", "于浅水湾坳下走浅水湾道", "城巴 6 / 6X / 260（浅水湾海滩站）", "走过紫罗兰山抵达浅水湾坳后，若不想攀登孖岗山天梯，可直接循引水道旁小径下走浅水湾道乘巴士离开。", SRC_CITYBUS),
        ],
    },
    {
        "area_id": "maclehose-3",
        "route_id": "route-maclehose-3",
        "nameZh": "麦理浩径第三段·嶂上",
        "nameEn": "MacLehose Sec. 3 · Cheung Sheung",
        "title": "麦理浩径第三段：北潭凹、牛耳石山、嶂上高原到水浪窝",
        "area_desc": "翻越牛耳石山与鸡公山群峰，中途藏着高山草原「嶂上」与百年许林士多，全程山海野趣十足。",
        "route_desc": "从北潭凹沿麦径三段直上牛耳石山，抵达隐世高山草地嶂上小休，再经画眉山与鸡公山脊线稳步下走西沙路水浪窝。",
        "duration": "一整天",
        "visitMinutes": 330,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "牛耳石山与鸡公山连续上落约 400 米，碎石斜坡较多，雨后慎防湿滑。",
        "transport": "西贡乘九巴 94（假日可从钻石山乘 96R）至北潭凹起步；终点水浪窝乘九巴 99 / 299X 返回马鞍山或沙田。",
        "transportSource": SRC_KMB,
        "weather": "脊线曝晒且风大，请带够 1.5L 以上饮水及防晒装备。",
        "notes": "嶂上许林士多仅周末及公众假期营业，平日需自备干粮；水浪窝观星台旁有洗手间。",
        "interests": ["山海脊线", "高山草原", "自然风光"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "麦理浩径第三段翻越牛耳石山、嶂上高山草坡与鸡公山脊线，风景壮阔。",
        },
        "places": [
            ("mh3-pak-tam-au", "北潭凹（94 / 96R 巴士站）", "Pak Tam Au", [114.3327823, 22.4200024], "https://www.openstreetmap.org/node/1184038995",
             ["麦理浩径第三段起点", "九巴 94 / 96R 郊野接驳站"], [0, 0],
             ("bus", "九巴 94（西贡⇄黄石码头）／ 96R（假日钻石山）", "北潭凹巴士站", SRC_KMB, ["于西贡市中心乘九巴 94 或假日钻石山乘 96R 至北潭凹下车起步。"])),
            ("mh3-cheung-sheung", "嶂上高原营地", "Cheung Sheung", [114.3097725, 22.4296441], "https://www.openstreetmap.org/node/1184027867",
             ["海拔 300 米四面环山的高山草坪", "周末可于许林士多喝山水豆腐花小休"], [25, 45], None),
            ("mh3-shui-long-wo", "水浪窝（99 / 299X 巴士站）", "Shui Long Wo", [114.2783992, 22.4042410], "https://www.openstreetmap.org/node/2528904731",
             ["麦理浩径第三段终点", "九巴 99 / 299X 往沙田或马鞍山"], [0, 0],
             ("bus", "九巴 99 / 299X（西贡⇄沙田 / 恒安）", "水浪窝巴士站", SRC_KMB, ["下抵西沙路水浪窝巴士站乘九巴 99 或 299X 返回市区。"])),
        ],
        "early_exits": [
            (1, "mh3-cheung-sheung", "嶂上高原营地", "bus", "向北经海下路下走榕树澳／深涌", "步行往深涌码头（约 50 分钟）或折返北潭凹", "若在嶂上后体力不足，可沿石阶往北下走榕树澳接西沙路，或折返北潭凹乘 94 离开。", SRC_AFCD),
        ],
    },
    {
        "area_id": "maclehose-6",
        "route_id": "route-maclehose-6",
        "nameZh": "麦理浩径第六段·金山水塘",
        "nameEn": "MacLehose Sec. 6 · Kam Shan",
        "title": "麦理浩径第六段：大埔道石梨贝水塘、九龙水塘主坝到城门",
        "area_desc": "麦理浩径最短最轻松的一段，沿着百年石砌九龙水塘大坝与林荫马路漫步至城门水塘。",
        "route_desc": "从大埔道石梨贝水塘起步，走过花岗岩砌成的九龙水塘主坝与金山林道，经城门林区稳步接驳城门水塘。",
        "duration": "2 小时",
        "visitMinutes": 110,
        "stayMinutes": [20, 35],
        "climbLevel": "flat",
        "effortLevel": "easy",
        "climbNote": "全段以柏油林道与平缓土径为主，坡度温和，适合郊游入门或亲子同行。",
        "transport": "深水埗／沙田乘九巴 72 / 81 至石梨贝水塘站起步；终点城门水塘菠萝坝乘小巴 82 返荃湾。",
        "transportSource": SRC_KMB,
        "weather": "沿途树荫浓密，夏季相对清凉；雨天注意大坝湿滑。",
        "notes": "金山郊野公园野生猕猴众多，切勿手提胶袋、当众进食或投喂猴子。",
        "interests": ["百年水塘", "森林绿道", "轻松行山"],
        "preferences": ["慢慢走", "不太累", "少爬坡"],
        "categoryNotes": {
            "山海之间": "串联石梨贝、九龙与城门水塘群，是麦理浩径最平缓亲民的森林水塘段。",
        },
        "places": [
            ("mh6-shek-lei-pui", "石梨贝水塘（72 / 81 巴士站）", "Shek Lei Pui Reservoir", [114.1484724, 22.3557541], "https://www.openstreetmap.org/way/23618225",
             ["麦理浩径第六段西端大埔道入口", "九巴 72 / 81 直达"], [0, 0],
             ("bus", "九巴 72（长沙湾⇄太和）／ 81（佐敦⇄禾輋）", "石梨贝水塘巴士站", SRC_KMB, ["于太子、深水埗或沙田乘九巴 72／81 至石梨贝水塘站下车起步。"])),
            ("mh6-kowloon-dam", "九龙水塘法定古迹主坝", "Kowloon Reservoir", [114.1543757, 22.3541252], "https://www.openstreetmap.org/way/23618305",
             ["建于 1910 年的弧形花岗岩历史水坝", "水塘倒影与森林环抱景致"], [15, 25], None),
            ("mh6-pineapple-dam", "城门水塘菠萝坝（82 小巴站）", "Pineapple Dam", [114.1440780, 22.3845509], "https://www.openstreetmap.org/way/23368182",
             ["麦理浩径第六段终点与第七段起点", "专线小巴 82 往荃湾兆和街"], [0, 0],
             ("bus", "新界专线小巴 82（菠萝坝⇄荃湾兆和街）", "菠萝坝小巴总站", SRC_TD, ["抵达城门水塘菠萝坝后乘 82 号专线小巴返回荃湾市区。"])),
        ],
        "early_exits": [
            (1, "mh6-kowloon-dam", "九龙水塘法定古迹主坝", "bus", "步行返回大埔道巴士站（约 15 分钟）", "九巴 72 / 81", "若走至九龙水塘主坝即想结束，可沿金山路步行约 15 分钟返回大埔道乘巴士。", SRC_KMB),
        ],
    },
    {
        "area_id": "maclehose-7",
        "route_id": "route-maclehose-7",
        "nameZh": "麦理浩径第七段·针山草山",
        "nameEn": "MacLehose Sec. 7 · Needle Hill & Grassy Hill",
        "title": "麦理浩径第七段：城门水塘主坝、针山天梯翻越草山至铅矿坳",
        "area_desc": "以「针山千级天梯」闻名的一段，登顶尖耸的针山俯瞰城门水塘全景，再经草山林道走入铅矿坳。",
        "route_desc": "自城门水塘菠萝坝经主坝踏上麦径七段，一口气攀上 532 米针山，再循山脊接草山开阔车路直达铅矿坳（可下走大埔元墩下或返城门）。",
        "duration": "半天",
        "visitMinutes": 250,
        "stayMinutes": [35, 60],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "针山南坡石阶连续陡升 350 米，下山往沙田坳亦陡峭，草山段则相对平缓。",
        "transport": "荃湾兆和街乘小巴 82 至城门水塘菠萝坝起步；铅矿坳可折返城门或北下大埔元墩下乘 23K 小巴。",
        "transportSource": SRC_TD,
        "weather": "针山山顶风大无遮荫，夏日请清晨起步避开正午暴晒。",
        "notes": "城门主坝及菠萝坝有自动售卖机及洗手间，中途针山至铅矿坳无商店。",
        "interests": ["山海脊线", "体力挑战", "水塘全景"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "针山尖峰俯瞰整个城门水塘与沙田谷，是麦理浩径标志性双峰挑战段。",
        },
        "places": [
            ("mh7-pineapple-dam", "城门水塘菠萝坝（82 小巴站）", "Pineapple Dam", [114.1440780, 22.3845509], "https://www.openstreetmap.org/way/23368182",
             ["麦理浩径第七段起点", "专线小巴 82 总站"], [0, 0],
             ("bus", "新界专线小巴 82（荃湾兆和街⇄城门水塘）", "菠萝坝小巴总站", SRC_TD, ["于荃湾兆和街乘 82 号小巴至菠萝坝总站，沿水塘畔步行过主坝上针山。"])),
            ("mh7-needle-hill", "针山顶（532 米）", "Needle Hill", [114.1606284, 22.3868950], "https://www.openstreetmap.org/node/1143809719",
             ["金字塔形尖峰 360 度环顾城门水塘与沙田", "麦径七段最著名拍照地标"], [20, 35], None),
            ("mh7-grassy-hill", "草山脊线", "Grassy Hill", [114.1658946, 22.4116959], "https://www.openstreetmap.org/node/1102121339",
             ["海拔 647 米开阔大草坡与盘山路", "远眺大帽山、马鞍山与吐露港"], [15, 25], None),
            ("mh7-lead-mine-pass", "铅矿坳（麦径七段终点）", "Lead Mine Pass", [114.1581428, 22.4123139], "https://www.openstreetmap.org/node/7059808056",
             ["麦理浩径第七段与第八段交界营地", "可下大埔元墩下（23K 小巴）或返城门菠萝坝"], [0, 0],
             ("bus", "卫奕信径北下元墩下乘 23K 小巴往大埔墟站（或下返菠萝坝）", "铅矿坳凉亭", SRC_TD, ["抵达铅矿坳后可沿着卫奕信径下走大埔元墩下乘 23K 小巴，或沿水塘畔折返菠萝坝乘 82。"])),
        ],
        "early_exits": [
            (1, "mh7-needle-hill", "针山顶（532 米）", "bus", "由针山北侧林道下道风山往沙田站", "步行往沙田排头村 / 港铁沙田站（约 45 分钟）", "翻越针山后若不想继续走草山，可在鞍部岔路下走道风山直出沙田港铁站。", SRC_MTR),
        ],
    },
    {
        "area_id": "lantau-3",
        "route_id": "route-lantau-3",
        "nameZh": "凤凰径第三段·凤凰山",
        "nameEn": "Lantau Trail Sec. 3 · Lantau Peak",
        "title": "凤凰径第三段：伯公坳登全港第二高峰凤凰山、天门栈道至昂坪",
        "area_desc": "攀登海拔 934 米的香港第二高峰凤凰山，穿过壮观的天门石栈道俯瞰石壁水塘与南大屿海岸，直下昂坪市集。",
        "route_desc": "从伯公坳西侧起步沿着凤凰径三段石梯陡升登顶凤凰山，再顺北侧「天门栈道」百级天梯下至心经简林与昂坪市集。",
        "duration": "半天",
        "visitMinutes": 260,
        "stayMinutes": [40, 65],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "全港最陡峭的大众山径之一，伯公坳上山与下昂坪天门栈道均极耗膝盖，建议带登山杖。",
        "transport": "东涌站乘屿巴 3M / 11 / 23 至伯公坳起步；终点昂坪市集可乘屿巴 23 或昂坪 360 缆车返东涌。",
        "transportSource": SRC_NLB,
        "weather": "山顶常有大雾与强风，清晨看日出务必携带头灯及防风保暖外套。",
        "notes": "昂坪市集有餐厅、便利店及洗手间；若赶乘昂坪 360 缆车需留意末班收车时间。",
        "interests": ["高山云海", "日出观景", "山海脊线"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "登顶香港第二高峰凤凰山，串联南天门栈道与昂坪大佛视野。",
        },
        "places": [
            ("lt3-pak-kung-au", "伯公坳（3M / 11 / 23 巴士站）", "Pak Kung Au", [113.9432200, 22.2481465], "https://www.openstreetmap.org/node/1917264532",
             ["凤凰径第三段东端起点", "大屿山巴士 3M / 11 / 23 直达"], [0, 0],
             ("bus", "新大屿山巴士 3M / 11 / 23（东涌起步）", "伯公坳巴士站", SRC_NLB, ["于东涌港铁站外乘屿巴 3M、11 或 23 至伯公坳站下车起步。"])),
            ("lt3-lantau-peak", "凤凰山顶（934 米）", "Lantau Peak", [113.9199385, 22.2492970], "https://www.openstreetmap.org/node/1852935099",
             ["香港第二高峰与日出圣地", "俯瞰石壁水塘、大澳海湾与机场岛"], [30, 50], None),
            ("lt3-ngong-ping", "昂坪市集（23 巴士 / 缆车站）", "Ngong Ping Village", [113.9030577, 22.2563156], "https://www.openstreetmap.org/way/45605614",
             ["凤凰径第三段终点与天坛大佛山下市集", "屿巴 23 往东涌／2 往梅窝／昂坪 360 缆车"], [0, 0],
             ("bus", "新大屿山巴士 23（昂坪⇄东涌）／ 昂坪 360 缆车", "昂坪巴士总站", SRC_NLB, ["下抵昂坪市集后可乘屿巴 23 返回东涌站，或乘昂坪 360 缆车下山。"])),
        ],
        "early_exits": [
            (1, "lt3-lantau-peak", "凤凰山顶（934 米）", "bus", "原路折返伯公坳（约 70 分钟）", "屿巴 3M / 11 / 23", "若登顶后遇浓雾或时间紧张，可评估原路返回伯公坳或快速下走至昂坪广场乘车。", SRC_NLB),
        ],
    },
    {
        "area_id": "hk-trail-1-2",
        "route_id": "route-hk-trail-1-2",
        "nameZh": "港岛径一二段·薄扶林",
        "nameEn": "Hong Kong Trail Sec. 1-2 · Pok Fu Lam",
        "title": "港岛径第一、二段：山顶广场、西高山栈道下走薄扶林水塘到置富",
        "area_desc": "沿着太平山腰绿荫小径穿过西高山观景台与香港首座水塘薄扶林水塘，轻松连走港岛最精华森林段。",
        "route_desc": "从山顶广场循夏力道接港岛径一段，绕过西高山山腰眺望西博寮海峡与南丫岛，再下入百年薄扶林水塘林道出置富花园。",
        "duration": "半天",
        "visitMinutes": 180,
        "stayMinutes": [30, 50],
        "climbLevel": "moderate",
        "effortLevel": "easy",
        "climbNote": "由山顶高处一路缓步下坡为主，几乎不用大幅爬坡，非常轻松舒适。",
        "transport": "中环乘新巴 15 或山顶缆车至山顶广场起步；终点置富花园乘城巴 4 / 7 / 37A / 970 离开。",
        "transportSource": SRC_CITYBUS,
        "weather": "沿途树荫多且路况极佳，适合全年大部分晴朗或微阴天气。",
        "notes": "薄扶林水塘石桥与百年水务建筑值得驻足；若体力充沛还可顺登西高山顶看维港落日。",
        "interests": ["百年水塘", "森林绿道", "轻松行山"],
        "preferences": ["慢慢走", "不太累", "少爬坡", "看海看风景"],
        "categoryNotes": {
            "山海之间": "自山顶向下缓行至薄扶林水塘，俯瞰南丫岛海面与百年水务古迹。",
        },
        "places": [
            ("hkt-peak-galleria", "山顶广场（15 巴士 / 缆车站）", "The Peak Galleria", [114.1498719, 22.2703561], "https://www.openstreetmap.org/way/156335591",
             ["港岛径第一段起点", "城巴 15 巴士总站及山顶缆车凌霄阁旁"], [0, 0],
             ("bus", "城巴 15（中环码头⇄山顶）／ 山顶缆车", "山顶广场巴士总站", SRC_CITYBUS, ["于中环乘城巴 15 或山顶缆车抵达山顶广场，沿卢吉道／夏力道往西步行起步。"])),
            ("hkt-high-west", "西高山（港岛径一段观景）", "High West", [114.1362939, 22.2721699], "https://www.openstreetmap.org/node/288737750",
             ["俯瞰维多利亚港西口、青马大桥与南丫岛", "港岛径一段与二段分界路口旁"], [15, 25], None),
            ("hkt-pokfulam-res", "薄扶林水塘百年石桥", "Pok Fu Lam Reservoir", [114.1372437, 22.2652061], "https://www.openstreetmap.org/way/4339370",
             ["1863 年落成的香港首座水塘", "法定古迹量水站与林荫环塘小径"], [15, 25], None),
            ("hkt-chi-fu", "置富花园（4 / 7 / 37A 巴士站）", "Chi Fu Fa Yuen", [114.1389348, 22.2576142], "https://www.openstreetmap.org/relation/11816983",
             ["港岛径第二段终点附近市区接驳点", "多条城巴线路往中环、铜锣湾或旺角"], [0, 0],
             ("bus", "城巴 4 / 7 / 37A / 970（往中环、金钟、九龙）", "置富花园巴士总站", SRC_CITYBUS, ["从薄扶林水塘下走置富道至置富花园巴士总站乘车返回市区。"])),
        ],
        "early_exits": [
            (2, "hkt-pokfulam-res", "薄扶林水塘百年石桥", "bus", "沿薄扶林水塘道直出薄扶林道", "城巴 4 / 7 / 30X / 91（薄扶林水塘道站）", "走过薄扶林水塘后亦可直接沿水塘道步行 10 分钟出薄扶林道乘车。", SRC_CITYBUS),
        ],
    },
    {
        "area_id": "wilson-2",
        "route_id": "route-wilson-2",
        "nameZh": "卫奕信径二段·渣甸毕拿",
        "nameEn": "Wilson Trail Sec. 2 · Jardine's & Butler",
        "title": "卫奕信径第二段：黄泥涌峡、渣甸山、毕拿山石矿场到鲗鱼涌",
        "area_desc": "串联渣甸山与毕拿山双峰，俯瞰大潭水塘碧水与跑马地—维港东翼天际线，最后循柏架山道下走鲗鱼涌。",
        "route_desc": "自黄泥涌峡沿引水道旁石梯登上渣甸山观景台，穿过毕拿山与废弃石矿场旧址俯瞰港岛东区，再顺柏架山道林荫斜路直抵鲗鱼涌港铁站。",
        "duration": "半天",
        "visitMinutes": 210,
        "stayMinutes": [35, 55],
        "climbLevel": "steep",
        "effortLevel": "moderate",
        "climbNote": "渣甸山及毕拿山连续石阶攀升约 300 米，过毕拿山后下往柏架山道为全柏油缓坡。",
        "transport": "中环／铜锣湾乘城巴 6 / 66 / 76 至黄泥涌水塘公园起步；终点步出英皇道港铁鲗鱼涌站离开。",
        "transportSource": SRC_CITYBUS,
        "weather": "渣甸山及毕拿山脊曝晒，下入柏架山道后树荫极密。",
        "notes": "柏架山道沿途有战时灶头及林边生物多样性自然教育中心（红屋）可顺路参观。",
        "interests": ["山海脊线", "城市全景", "历史遗迹"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "渣甸山与毕拿山脊线俯瞰维港东翼与大潭水塘群，直通鲗鱼涌地铁站。",
        },
        "places": [
            ("ws2-wong-nai-chung", "黄泥涌峡（6 / 66 / 76 巴士站）", "Wong Nai Chung Gap", [114.1928608, 22.2581043], "https://www.openstreetmap.org/node/8781211670",
             ["卫奕信径第二段南端起步点", "城巴 6 / 66 / 76 直达"], [0, 0],
             ("bus", "城巴 6 / 66 / 76（中环／铜锣湾出发）", "黄泥涌水塘公园巴士站", SRC_CITYBUS, ["于中环或铜锣湾乘城巴 6、66 或 76 至黄泥涌水塘公园站下车，过马路上渣甸山。"])),
            ("ws2-jardines", "渣甸山顶（433 米）", "Jardine's Lookout", [114.1983331, 22.2663560], "https://www.openstreetmap.org/node/1096337353",
             ["正面俯瞰跑马地、铜锣湾与维港两岸", "卫奕信径二段标志性山顶标高柱"], [20, 30], None),
            ("ws2-butler", "毕拿山顶（436 米）", "Mount Butler", [114.2111196, 22.2676649], "https://www.openstreetmap.org/node/1169564903",
             ["俯瞰昔日石矿场悬崖与大潭水塘群", "连接小马山与大风坳的脊线节点"], [15, 25], None),
            ("ws2-quarry-bay", "港铁鲗鱼涌站（终点）", "MTR Quarry Bay Station", [114.2089920, 22.2881654], "https://www.openstreetmap.org/node/6610705648",
             ["港铁港岛线／将军澳线换乘站", "柏架山道下山终点直出英皇道"], [0, 0],
             ("metro", "港铁港岛线 / 将军澳线", "鲗鱼涌站 A 出口", SRC_MTR, ["由大风坳沿柏架山道柏油斜路步行下山至英皇道，即达港铁鲗鱼涌站。"])),
        ],
        "early_exits": [
            (2, "ws2-butler", "毕拿山顶（436 米）", "bus", "于大风坳往北下走鲗鱼涌，或南下大潭水塘", "港铁鲗鱼涌站 / 城巴 14（大潭郊野公园站）", "抵达大风坳后如不想走长段柏架山道，亦可往南经大潭笃水塘下出大潭道乘 14 路离开。", SRC_CITYBUS),
        ],
    },
    {
        "area_id": "sharp-peak",
        "route_id": "route-sharp-peak",
        "nameZh": "西贡蚺蛇尖·三尖之首",
        "nameEn": "Sharp Peak · Sai Kung",
        "title": "香港三尖之首：北潭凹、赤径、大浪坳登蚺蛇尖再落咸田湾",
        "area_desc": "被誉为「香港第一险峰」与「香港三尖之首」的蚺蛇尖（468 米），山体尖削孤耸，俯瞰整个大浪四湾翡翠海景。",
        "route_desc": "从北潭凹经赤径与大浪坳切入蚺蛇坳，攀登风化碎石陡坡登顶蚺蛇尖 360 度望尽西贡东四湾，再沿南脊下走咸田湾或折返赤径。",
        "duration": "一整天",
        "visitMinutes": 390,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "蚺蛇尖上下山均为松散风化碎石陡坡（手脚并用路段），极易滑倒，仅适合有经验行山者于干燥晴天前往。",
        "transport": "西贡乘九巴 94 / 假日钻石山乘 96R 至北潭凹起步；若经咸田湾离开需再走西湾亭乘 NR29 或翻大浪坳回北潭凹。",
        "transportSource": SRC_KMB,
        "weather": "切忌雨天、大雾或强风前往蚺蛇尖；全程无遮荫，每人需备 2L 以上饮水。",
        "notes": "务必穿抓地力强的登山鞋与手套；赤径与咸田湾均可作为补给与下撤中转点。",
        "interests": ["极限挑战", "山海脊线", "离岛海湾"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "香港三尖之首蚺蛇尖，俯瞰大浪西湾、咸田湾、大湾与东湾四连海湾。",
        },
        "places": [
            ("sp-pak-tam-au", "北潭凹（94 / 96R 巴士站）", "Pak Tam Au", [114.3327823, 22.4200024], "https://www.openstreetmap.org/node/1184038995",
             ["前往赤径与大浪坳的主要起步点", "九巴 94 / 96R 接驳站"], [0, 0],
             ("bus", "九巴 94（西贡⇄黄石）／ 96R（假日钻石山）", "北潭凹巴士站", SRC_KMB, ["乘九巴 94 或 96R 至北潭凹下车，沿着麦径二段反方向步往赤径。"])),
            ("sp-chek-keng", "赤径村与渡轮码头", "Chek Keng", [114.3501962, 22.4213385], "https://www.openstreetmap.org/node/1200155475",
             ["静谧海湾村落与红树林湿地", "翻越大浪坳前最后平地补给点"], [15, 25], None),
            ("sp-sharp-peak", "蚺蛇尖山路观景（大浪四湾全景）", "Sharp Peak Trail", [114.375378, 22.426906], "https://www.openstreetmap.org/node/13313665216",
             ["香港三尖之首标志性尖峰标高柱", "同时俯瞰大浪四湾、米粉咀与吐露港"], [25, 45], None),
            ("sp-ham-tin", "咸田湾独木桥（或折返赤径）", "Ham Tin Wan", [114.3753998, 22.4092191], "https://www.openstreetmap.org/way/245413792",
             ["下抵大浪湾白沙滩士多补给", "可再翻大浪坳回北潭凹或往西湾亭乘 NR29"], [0, 0],
             ("bus", "经西湾亭乘 NR29 或翻大浪坳回北潭凹乘 94", "咸田湾海风士多", SRC_TD, ["于咸田湾休整补给后，可沿麦径二段走西湾亭乘 NR29 或翻越大浪坳返回北潭凹乘 94。"])),
        ],
        "early_exits": [
            (1, "sp-chek-keng", "赤径村与渡轮码头", "ferry", "赤径码头（假日街渡往黄石码头）", "翠华船务假日街渡（黄石⇄赤径⇄塔门）", "若天气转坏不宜攻顶蚺蛇尖，可在赤径折返北潭凹，或假日于赤径码头乘街渡往黄石码头转 94 离开。", SRC_TD),
        ],
    },
    {
        "area_id": "sz-wutong-summit",
        "route_id": "route-sz-wutong-summit",
        "city": "sz",
        "nameZh": "深圳梧桐山·鹏城第一峰",
        "nameEn": "Wutong Mountain Summit",
        "title": "深圳最高峰登顶：莲塘地铁站、登云道、好汉坡到大梧桐顶（943.7m）",
        "area_desc": "挑战深圳第一高峰「大梧桐」（海拔 943.7 米），从莲塘地铁站直登云海石阶与好汉坡，俯瞰深圳水库、香港群山与大鹏湾。",
        "route_desc": "自莲塘地铁站起步切入登云道千级石阶，经蝴蝶谷与好汉坡攀上大梧桐「鹏城第一峰」巨石碑，再按原线或好汉坡下撤返梧桐山南／莲塘。",
        "duration": "一整天",
        "visitMinutes": 340,
        "stayMinutes": [45, 75],
        "climbLevel": "steep",
        "effortLevel": "challenging",
        "climbNote": "全段累计爬升超 900 米，登云道石梯与好汉坡极为陡峭，需备足水与电解质补给。",
        "transport": "深圳地铁 2/8 号线莲塘站 C 口出站步行即可切入登云道入口；下山可由梧桐山南站或莲塘站乘地铁离开。",
        "transportSource": "https://www.szmc.net/",
        "weather": "大梧桐山顶风大雾浓，气温比市区低 5–7°C，登顶建议带防风外套。",
        "notes": "好汉坡停车场及盘山路沿途有自动售水机与应急补给站；景区免门票。",
        "interests": ["城市最高峰", "云海日出", "体力挑战"],
        "preferences": ["看海看风景"],
        "categoryNotes": {
            "山海之间": "深圳最高峰大梧桐登顶线，地铁直达山脚，山海城景与深港边界群山尽收眼底。",
        },
        "places": [
            ("szwt-liantang", "莲塘地铁站（登云道入口方向）", "Liantang Metro Station", [114.1698721, 22.5670087], "https://www.openstreetmap.org/node/9203761253",
             ["深圳地铁 2 / 8 号线直达山脚", "步行接登云道登山石阶牌坊"], [0, 0],
             ("metro", "深圳地铁 2号线 / 8号线", "莲塘站 C 出口", "https://www.szmc.net/", ["乘地铁 2/8 号线至莲塘站下车，向北沿仙湖路步行至登云道登山口。"])),
            ("szwt-haohanpo", "好汉坡广场", "Haohanpo", [114.2133869, 22.5791902], "https://www.openstreetmap.org/way/275120870",
             ["大梧桐与小梧桐交汇的经典补给休息平台", "冲刺鹏城第一峰前最后休整点"], [15, 25], None),
            ("szwt-summit", "大梧桐顶峰·鹏城第一峰（943.7m）", "Wutong Mountain Summit", [114.2146672, 22.5822680], "https://www.openstreetmap.org/node/9131873008",
             ["深圳最高峰巨石地标", "晴日远眺盐田港、大鹏湾与香港八仙岭"], [0, 0],
             ("metro", "沿好汉坡 / 盘山公路下撤至梧桐山南站或莲塘站", "大梧桐顶峰观景台", "https://www.szmc.net/", ["登顶后可沿原路或经盘山公路／凌云道下山至梧桐山南站或莲塘站乘地铁离开。"])),
        ],
        "early_exits": [
            (1, "szwt-haohanpo", "好汉坡广场", "bus", "沿梧桐山北路盘山道下至梧桐山北大门", "公交 M445 / 211（梧桐山总站）", "抵达好汉坡若体力不支，可直接沿着缓坡盘山公路步行下山至梧桐山北大门乘公交离开。", "https://www.szmc.net/"),
        ],
    },
]


def main():
    areas = json.loads((DATA_DIR / "areas.json").read_text(encoding="utf-8"))
    places_fc = json.loads((DATA_DIR / "places.geojson").read_text(encoding="utf-8"))
    routes = json.loads((DATA_DIR / "routes.json").read_text(encoding="utf-8"))

    areas_by_id = {a["id"]: a for a in areas}
    places_by_id = {f["properties"]["id"]: f for f in places_fc["features"]}
    routes_by_id = {r["id"]: r for r in routes}

    for idx, t in enumerate(TRAILS):
        area_id = t["area_id"]
        route_id = t["route_id"]
        place_ids = [p[0] for p in t["places"]]

        city = t.get("city", "hk")
        # Create/update places
        coords_list = []
        for p_idx, p_tuple in enumerate(t["places"]):
            pid, name_zh, name_en, coord, osm_url, highlights, mins, t_info = p_tuple
            place_obj = make_place(
                pid, name_zh, name_en, coord, osm_url, area_id,
                ["山海之间"], highlights, mins, t_info, priority=185 + idx, city=city
            )
            places_by_id[pid] = {
                "type": "Feature",
                "properties": place_obj,
                "geometry": {"type": "Point", "coordinates": coord},
            }
            coords_list.append(coord)

        # Fetch OSRM foot route
        raw_name = f"osrm-{route_id}.json"
        raw_path = RAW_DIR / raw_name
        req_url = (
            "https://routing.openstreetmap.de/routed-foot/route/v1/foot/"
            + ";".join(f"{c[0]},{c[1]}" for c in coords_list)
            + "?overview=full&geometries=geojson&steps=true"
        )
        if not raw_path.exists():
            print(f"Fetching OSRM for {route_id}...")
            res = subprocess.run(
                ["curl", "-fLsS", "--retry", "4", "--retry-all-errors", "--max-time", "40",
                 "-A", "HongKongWandering/1.0", req_url],
                capture_output=True, check=True,
            )
            raw_path.write_bytes(res.stdout)
            time.sleep(0.8)
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        assert raw.get("code") == "Ok", (route_id, raw)

        rr = raw["routes"][0]
        max_snap = round(max(w["distance"] for w in raw["waypoints"]), 1)
        geom_coords = rr["geometry"]["coordinates"]
        max_gap = max(dist_m(geom_coords[i - 1], geom_coords[i]) for i in range(1, len(geom_coords)))
        print(f"  {route_id}: dist={round(rr['distance'])}m, walkMin={round(rr['duration']/60)}m, maxSnap={max_snap}m, maxGap={round(max_gap)}m")
        assert max_snap <= 120, f"{route_id} snap too large: {max_snap}"
        assert max_gap < 400, f"{route_id} gap too large: {max_gap}"

        lons = [c[0] for c in coords_list]
        lats = [c[1] for c in coords_list]
        bounds = [round(min(lons) - 0.01, 4), round(min(lats) - 0.01, 4), round(max(lons) + 0.01, 4), round(max(lats) + 0.01, 4)]
        center = [round(sum(lons) / len(lons), 5), round(sum(lats) / len(lats), 5)]

        areas_by_id[area_id] = {
            "id": area_id,
            "city": city,
            "nameZh": t["nameZh"],
            "nameEn": t["nameEn"],
            "categories": ["山海之间"],
            "description": t["area_desc"],
            "duration": t["duration"],
            "transport": t["transport"],
            "sourceUrl": SRC_AFCD,
            "verifiedAt": "2026-11-17",
            "placeIds": place_ids,
            "coordinates": center,
            "bounds": bounds,
            "boundsNote": "范围包络涵盖该段行山径起终点及沿线主要观景途经点。",
            "weather": t["weather"],
            "timeOfDay": "清晨 / 白天（避开正午酷热及天黑后下山）",
            "priority": 185 + idx,
            "status": "active",
        }

        legs = rr["legs"]
        itinerary_legs = [
            {"fromIndex": i, "toIndex": i + 1, "mode": "walk", "distance": round(legs[i]["distance"]), "minutes": max(1, round(legs[i]["duration"] / 60))}
            for i in range(len(legs))
        ]

        start_p = t["places"][0]
        end_p = t["places"][-1]
        transport_nodes = [
            {
                "placeId": start_p[0], "stopIndex": 0, "role": "start",
                "mode": start_p[7][0], "service": start_p[7][1], "exitOrStop": start_p[7][2],
                "instruction": start_p[7][4][0], "sourceUrl": start_p[7][3],
            },
            {
                "placeId": end_p[0], "stopIndex": len(place_ids) - 1, "role": "end",
                "mode": end_p[7][0], "service": end_p[7][1], "exitOrStop": end_p[7][2],
                "instruction": end_p[7][4][0], "sourceUrl": end_p[7][3],
            },
        ]

        early_exits = [
            {
                "atPlaceId": pid, "stopIndex": s_idx, "nameZh": n_zh, "mode": mode,
                "exitOrStop": exit_stop, "service": svc, "instruction": instr, "sourceUrl": s_url,
            }
            for (s_idx, pid, n_zh, mode, exit_stop, svc, instr, s_url) in t["early_exits"]
        ]

        routes_by_id[route_id] = {
            "id": route_id,
            "city": city,
            "areaId": area_id,
            "title": t["title"],
            "description": t["route_desc"],
            "placeIds": place_ids,
            "status": "network-checked",
            "verificationNote": "OSM 真实行山径 / OSRM 步行路网核对。",
            "distance": round(rr["distance"]),
            "walkingMinutes": max(1, round(rr["duration"] / 60)),
            "visitMinutes": t["visitMinutes"],
            "stayMinutes": t["stayMinutes"],
            "climbLevel": t["climbLevel"],
            "effortLevel": t["effortLevel"],
            "climbNote": t["climbNote"],
            "transport": t["transport"],
            "transportSource": t["transportSource"],
            "sourceUrl": SRC_AFCD,
            "verifiedAt": "2026-11-17",
            "timeOfDay": "清晨 / 白天",
            "notes": t["notes"],
            "interests": t["interests"],
            "preferences": t["preferences"],
            "categories": ["山海之间"],
            "categoryNotes": t["categoryNotes"],
            "requestUrl": req_url,
            "maxSnapMeters": max_snap,
            "itineraryLegs": itinerary_legs,
            "transportNodes": transport_nodes,
            "earlyExits": early_exits,
            "transportNote": STATIC_NOTE,
            "geometry": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "mode": "walk",
                            "rawFile": raw_name,
                            "placeIds": place_ids,
                            "distance": rr["distance"],
                        },
                        "geometry": rr["geometry"],
                    }
                ],
            },
        }

    (DATA_DIR / "areas.json").write_text(json.dumps(list(areas_by_id.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    places_fc["features"] = list(places_by_id.values())
    (DATA_DIR / "places.geojson").write_text(json.dumps(places_fc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA_DIR / "routes.json").write_text(json.dumps(list(routes_by_id.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(areas_by_id)} areas, {len(places_fc['features'])} places, {len(routes_by_id)} routes.")


if __name__ == "__main__":
    main()
