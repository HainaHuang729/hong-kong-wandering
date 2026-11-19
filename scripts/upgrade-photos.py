"""Upgrade legacy photos and fetch recent, EXIF-verified Wikimedia Commons entrance/sign/landmark photos."""
import json
import math
import pathlib
import re
import subprocess
import time
import urllib.parse

R = pathlib.Path(__file__).resolve().parents[1]
RAW_PHOTOS = R / 'data/raw/photos'
RAW_PHOTOS.mkdir(parents=True, exist_ok=True)
SEL_PATH = R / 'data/editorial/place-photos.json'
PLACES_PATH = R / 'public/data/places.geojson'

def read(p):
    return json.loads(p.read_text())

def save(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

def haversine(lon1, lat1, lon2, lat2):
    rad = math.pi / 180
    return 6371000 * 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) * rad / 2) ** 2 +
        math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin((lon2 - lon1) * rad / 2) ** 2
    ))

def extract_year(s):
    m = re.search(r'(19\d{2}|20[0-2]\d)', s or '')
    return int(m.group(1)) if m else 0

places = {f['properties']['id']: f['properties'] for f in read(PLACES_PATH)['features']}
selected = read(SEL_PATH)

# 1. Direct upgrades already cached in data/raw/photos/ (only apply if not already updated)
for pid, info in [
    ('western', {'rawFile': 'western.json', 'pageId': 99255740, 'caption': '西港城及电车总站路口（2018 年照片）'}),
    ('sk-promenade', {'rawFile': 'sk-promenade.json', 'pageId': 167917922, 'caption': '西贡海滨公园地质公园入口标识（2025 年照片）'}),
    ('taikwun', {'rawFile': 'taikwun-reviewed.json', 'pageId': 101253554, 'caption': '大馆荷李活道入口建筑立面（2021 年照片）'}),
    ('theatre', {'rawFile': 'theatre.json', 'pageId': 130898698, 'caption': '油麻地戏院与新填地街路口（2023 年照片）'}),
]:
    selected.setdefault(pid, info)

# 2. Target places: (place_id, raw_fname, keywords_any, fallback_search, caption_base, force_refresh)
TARGETS = [
    ('meiho', 'meiho-upgraded.json', ['mei ho', '美荷樓', '美荷楼'], 'YHA Mei Ho House Sham Shui Po', '美荷楼活化后外观与入口', False),
    ('kt-promenade', 'kt-promenade-upgraded.json', ['kwun tong promenade', '觀塘海濱'], 'Kwun Tong Promenade', '观塘海滨花园长廊及地标塔', False),
    ('manmo', 'manmo-upgraded-v2.json', ['man mo', '文武廟', 'lit shing'], 'Man Mo Temple Hollywood Road', '荷李活道文武庙正门与建筑群', False),
    ('murray', 'murray-upgraded.json', ['murray house', '美利樓'], 'Murray House Stanley', '赤柱美利楼立面与海旁入口', False),
    ('cc-paktai', 'cc-paktai-upgraded.json', ['yuk hui', 'pak tai', '玉虛宮', '北帝'], 'Yuk Hui Temple Cheung Chau', '长洲玉虚宫（北帝庙）入口广场', False),
    ('sheko-temple', 'sheko-temple-upgraded-v2.json', ['tin hau', '天后'], 'Shek O Tin Hau Temple', '石澳天后庙入口实景', False),
    ('cc-pier', 'cc-pier-photo.json', ['cheung chau ferry pier', 'cheung chau pier', '長洲碼頭', '長洲渡輪碼頭'], 'Cheung Chau Ferry Pier', '长洲渡轮码头入口与候船区', False),
    ('pc-pier', 'pc-pier-photo.json', ['peng chau ferry pier', 'peng chau pier', '坪洲碼頭', '坪洲渡輪碼頭'], 'Peng Chau Ferry Pier', '坪洲渡轮码头外观', False),
    ('mw-pier', 'mw-pier-photo.json', ['mui wo ferry pier', 'mui wo pier', '梅窩碼頭', '梅窩渡輪碼頭'], 'Mui Wo Ferry Pier', '梅窝渡轮码头入口', False),
    ('th-haw-par', 'th-haw-par-photo.json', ['haw par', 'tiger balm', '虎豹別墅'], 'Haw Par Mansion Hong Kong', '大坑道虎豹别墅入口建筑', False),
    ('th-lin-fa-kung', 'th-lin-fa-kung-photo.json', ['lin fa', '蓮花宮'], 'Lin Fa Temple Tai Hang', '大坑莲花宫入口阶梯与八角前殿', False),
    ('mlw-zoological', 'mlw-zoological-photo.json', ['zoological', 'botanical', '動植物公園'], 'Hong Kong Zoological and Botanical Gardens', '香港动植物公园喷水池平台', False),
    ('alc-wind-tower-park', 'alc-wind-tower-photo.json', ['wind tower', '風之塔'], 'Ap Lei Chau Wind Tower Park', '鸭脷洲风之塔公园地标塔', False),
    ('skm-jccac', 'skm-jccac-photo.json', ['jccac', 'creative arts centre', '創意藝術中心'], 'Jockey Club Creative Arts Centre', '石硖尾赛马会创意艺术中心入口', False),
    ('tkw-cattle-depot', 'tkw-cattle-depot-photo.json', ['cattle depot', '牛棚'], 'Cattle Depot Artist Village', '牛棚艺术村红砖建筑群', False),
    ('tko-velodrome-park', 'tko-velodrome-photo.json', ['velodrome', '單車館'], 'Hong Kong Velodrome Park', '香港单车馆公园与人工湖广场', False),
    ('tw-airport-core', 'tw-airport-core-photo.json', ['airport core', 'homi villa', '機場核心', '白樓'], 'Airport Core Programme Exhibition Centre', '白楼（机场核心计划展览中心）与汀九海景', False),
    ('qb-monster', 'qb-monster-photo.json', ['yick cheong', 'montane', 'monster', '益昌', '海山樓'], 'Yick Cheong Building Hong Kong', '益昌大厦与海山楼住宅外立面', False),
    ('wk-xiqu', 'wk-xiqu-photo.json', ['xiqu', '戲曲中心'], 'Xiqu Centre West Kowloon', '西九戏曲中心东面入口与银色立面', False),
    ('wk-mplus', 'wk-mplus-photo.json', ['m+', 'm plus'], 'M+ West Kowloon', 'M+ 视觉文化博物馆外观', False),
    ('wk-palace', 'wk-palace-photo.json', ['palace museum', '故宮'], 'Hong Kong Palace Museum', '香港故宫文化博物馆入口广场', False),
    ('kc-walled-city', 'kc-walled-city-photo.json', ['walled city park', 'yamen', '九龍寨城公園'], 'Kowloon Walled City Park', '九龙寨城公园南门及前衙门', False),
    ('tp-railway-museum', 'tp-railway-museum-photo.json', ['railway museum', 'tai po market station', '鐵路博物館'], 'Hong Kong Railway Museum', '香港铁路博物馆旧大埔墟火车站入口', False),
    # Additional route coverage & final 3 districts
    ('np-choi-sai-woo', 'np-choi-sai-woo-photo.json', ['choi sai woo', '賽西湖'], 'Choi Sai Woo Park Hong Kong', '宝马山赛西湖公园绿荫步道', False),
    ('np-provident', 'np-provident-photo.json', ['provident', '和富', 'island eastern corridor'], 'Provident Centre North Point', '和富中心及东区走廊桥下海滨', False),
    ('np-ferry-pier', 'np-ferry-pier-photo.json', ['north point ferry pier', '北角碼頭'], 'North Point Ferry Pier', '北角（西）渡轮码头外观', False),
    ('ncw-village', 'ncw-village-photo.json', ['ngau chi wan', '牛池灣'], 'Ngau Chi Wan Village', '牛池湾街市及牛池湾村入口', False),
    ('ncw-choi-hung-estate', 'ncw-choi-hung-photo.json', ['choi hung estate', '彩虹邨'], 'Choi Hung Estate Hong Kong', '彩虹邨公共空间与平台球场', False),
    ('spk-kai-tak-river', 'spk-kai-tak-river-photo.json', ['kai tak river', '啟德河'], 'Kai Tak River San Po Kong', '启德河新蒲岗段绿化河道', False),
    ('spk-fung-tak-park', 'spk-fung-tak-park-photo.json', ['fung tak park', '鳳德公園'], 'Fung Tak Park Hong Kong', '钻石山凤德公园景观', False),
    ('th-queens-college', 'th-queens-college-photo.json', ['queen\'s college', '皇仁書院'], "Queen's College Causeway Bay", '高士威道皇仁书院外街景', False),
    ('th-lai-tak', 'th-lai-tak-photo.json', ['lai tak tsuen', '勵德邨'], 'Lai Tak Tsuen Hong Kong', '大坑励德邨建筑外观', False),
    ('mlw-lung-fu-shan', 'mlw-lung-fu-shan-photo.json', ['lung fu shan', '龍虎山'], 'Lung Fu Shan Environmental Education Centre', '龙虎山环境教育中心历史建筑', False),
    ('abd-promenade', 'abd-promenade-photo.json', ['aberdeen promenade', '香港仔海濱'], 'Aberdeen Promenade Hong Kong', '香港仔海滨公园与避风塘海旁', False),
    ('skm-nam-shan-estate', 'skm-nam-shan-photo.json', ['nam shan estate', '南山邨'], 'Nam Shan Estate Hong Kong', '南山邨平台与周边长型屋邨', False),
    ('tkw-hoi-sham-park', 'tkw-hoi-sham-photo.json', ['hoi sham', '海心公園'], 'Hoi Sham Park To Kwa Wan', '土瓜湾海心公园鱼尾石与海亭', False),
    ('tkw-ko-shan-theatre', 'tkw-ko-shan-photo.json', ['ko shan', '高山劇場'], 'Ko Shan Theatre Hong Kong', '高山剧场及高山道公园入口', False),
    ('st-town-hall', 'st-town-hall-photo.json', ['sha tin town hall', '沙田大會堂'], 'Sha Tin Town Hall Hong Kong', '沙田大会堂公共广场与阶梯', False),
    ('st-lek-yuen', 'st-lek-yuen-photo.json', ['lek yuen', '瀝源邨'], 'Lek Yuen Estate Sha Tin', '沙田沥源邨中心喷泉池', False),
    ('tko-hkdi', 'tko-hkdi-photo.json', ['design institute', 'hkdi', '知專設計'], 'Hong Kong Design Institute', '调景岭香港知专设计学院平台', False),
    ('tko-waterfront-park', 'tko-waterfront-photo.json', ['tseung kwan o waterfront', '將軍澳海濱'], 'Tseung Kwan O Waterfront Park', '将军澳南海滨长廊与跨湾景观', False),
    ('tw-approach-beach', 'tw-approach-beach-photo.json', ['approach beach', '近水灣'], 'Approach Beach Hong Kong', '近水湾泳滩与青马大桥视野', False),
    ('tw-sham-tseng-garden', 'tw-sham-tseng-garden-photo.json', ['garden', '嘉頓', 'sham tseng'], 'Garden Bakery Sham Tseng', '深井嘉顿厂房地标建筑', False),
    ('qb-chun-yeung', 'qb-chun-yeung-photo.json', ['chun yeung', '春秧街'], 'Chun Yeung Street Market Hong Kong', '北角春秧街电车路露天市集', False),
    ('qb-woodside', 'qb-woodside-photo.json', ['woodside', '林邊'], 'Woodside House Quarry Bay', '鲗鱼涌林边红屋历史建筑', False),
    ('qb-park', 'qb-park-photo.json', ['quarry bay park', '鰂魚涌公園'], 'Quarry Bay Park Hong Kong', '鲗鱼涌公园海滨长廊', False),
    ('wk-freespace', 'wk-freespace-photo.json', ['freespace', 'art park', '西九', '藝術公園'], 'West Kowloon Art Park', '西九艺术公园与自由空间海滨', False),
    ('kc-garden', 'kc-garden-photo.json', ['sung wong toi', '宋王臺'], 'Sung Wong Toi Garden Hong Kong', '宋王台花园及宋王台石刻', False),
    ('tp-man-mo', 'tp-man-mo-photo.json', ['man mo temple', '文武二帝廟', 'fu shin'], 'Man Mo Temple Tai Po', '大埔富善街文武二帝庙', False),
    ('tp-waterfront-park', 'tp-waterfront-photo.json', ['tai po waterfront', '大埔海濱公園'], 'Tai Po Waterfront Park', '大埔海滨公园与回归纪念塔', False),
    ('tt-upper-dam', 'tt-upper-dam-photo.json', ['tai tam upper', 'tai tam reservoir', '大潭上水塘'], 'Tai Tam Upper Reservoir Dam', '大潭上水塘百年花岗岩水坝', False),
    ('tt-tuk-barbecue', 'tt-tuk-barbecue-photo.json', ['tai tam tuk', '大潭篤水塘'], 'Tai Tam Tuk Reservoir Masonry Bridge', '大潭笃水塘石拱桥群', False),
    ('tc-battery', 'tc-battery-photo.json', ['tung chung battery', '東涌小炮台'], 'Tung Chung Battery Hong Kong', '东涌小炮台清代石墙遗址', False),
    ('tc-fort', 'tc-fort-photo.json', ['tung chung fort', '東涌炮台'], 'Tung Chung Fort Hong Kong', '东涌炮台古城墙及正门', False),
    ('wts-temple', 'wts-temple-photo.json', ['wong tai sin temple', '黃大仙祠'], 'Wong Tai Sin Temple Hong Kong', '啬色园黄大仙祠广场与大殿', False),
    ('wts-nan-lian', 'wts-nan-lian-photo.json', ['nan lian', '南蓮園池'], 'Nan Lian Garden Hong Kong', '南莲园池唐代木构水景园林', False),
    ('wts-chi-lin', 'wts-chi-lin-photo.json', ['chi lin', '志蓮淨苑'], 'Chi Lin Nunnery Hong Kong', '志莲净苑仿唐佛寺庭院', False),
    # 15 new routes
    ('hv-racecourse', 'hv-racecourse-photo.json', ['happy valley', 'racing', '跑馬地'], 'Hong Kong Racing Museum Happy Valley', '跑马地马场及香港赛马博物馆外立面', False),
    ('hv-tram-terminus', 'hv-tram-terminus-photo.json', ['happy valley', 'tram', '跑馬地'], 'Happy Valley Tram Terminus Hong Kong', '黄泥涌道跑马地电车总站', False),
    ('skw-tam-kung', 'skw-tam-kung-photo.json', ['tam kung', '譚公廟'], 'Tam Kung Temple Shau Kei Wan', '筲箕湾谭公庙入口建筑', False),
    ('skw-coastal-defence', 'skw-coastal-defence-photo.json', ['coastal defence', 'war of resistance', '海防博物館'], 'Hong Kong Museum of Coastal Defence', '香港抗战及海防博物馆堡垒与天幕', False),
    ('skw-aldrich-bay', 'skw-aldrich-bay-photo.json', ['aldrich bay', '愛秩序灣'], 'Aldrich Bay Park Hong Kong', '爱秩序湾公园海滨亭阁', False),
    ('cwb-st-paul', 'cwb-st-paul-photo.json', ['st. paul', 'christ the king', '聖保祿', '基督君王'], 'Christ the King Chapel Causeway Bay', '铜锣湾圣保禄修院基督君王小堂', False),
    ('cwb-haven-street', 'cwb-haven-street-photo.json', ['haven street', '希雲街'], 'Haven Street Causeway Bay Hong Kong', '铜锣湾希云街社区街景', False),
    ('pk-lions-pavilion', 'pk-lions-pavilion-photo.json', ['lions pavilion', 'lion pavilion', '獅子亭', 'victoria gap'], 'Lions Pavilion Victoria Peak Hong Kong', '太平山狮子亭观景平台', False),
    ('pk-lugard-road', 'pk-lugard-road-photo.json', ['lugard road', '盧吉道'], 'Lugard Road Hong Kong', '太平山卢吉道百年高空栈道', False),
    ('lym-lighthouse', 'lym-lighthouse-photo.json', ['lighthouse', 'lei yue mun', '燈塔', '鯉魚門'], 'Lei Yue Mun Lighthouse', '鲤鱼门海角红白灯塔', False),
    ('lym-tin-hau', 'lym-tin-hau-photo.json', ['tin hau', 'lei yue mun', '鯉魚門', '天后'], 'Tin Hau Temple Lei Yue Mun', '鲤鱼门海峡旁天后古庙', False),
    ('hh-promenade', 'hh-promenade-photo.json', ['hung hom promenade', '紅磡海濱'], 'Hung Hom Promenade Hong Kong', '红磡海滨花园维港长廊', False),
    ('hh-whampoa-ship', 'hh-whampoa-ship-photo.json', ['whampoa', '黃埔號'], 'The Whampoa Hung Hom', '黄埔号船形建筑地标', False),
    ('lck-jao-tsung-i', 'lck-jao-tsung-i-photo.json', ['jao tsung', '饒宗頤'], 'Jao Tsung-I Academy Hong Kong', '饶宗颐文化馆红砖建筑群', False),
    ('lck-lingnan-garden', 'lck-lingnan-garden-photo.json', ['lingnan', 'lai chi kok park', '嶺南之風'], 'Lingnan Garden Lai Chi Kok Park', '荔枝角公园岭南之风园林', False),
    ('lck-d2-place', 'lck-d2-place-photo.json', ['d2 place', 'cheung yee', '長義街'], 'D2 Place Lai Chi Kok', '荔枝角 D2 Place 文创工厦', False),
    ('tkt-anchor-street', 'tkt-anchor-street-photo.json', ['anchor street', '晏架街', 'tai kok tsui', '大角咀'], 'Anchor Street Tai Kok Tsui', '大角咀晏架街街区景观', False),
    ('tkt-hoi-fai', 'tkt-hoi-fai-photo.json', ['hoi fai road', '海輝道', 'olympic'], 'Hoi Fai Road Promenade Hong Kong', '海辉道海滨花园与西九海湾', False),
    ('ps-tsui-sing-lau', 'ps-tsui-sing-lau-photo.json', ['tsui sing lau', '聚星樓'], 'Tsui Sing Lau Pagoda Hong Kong', '屏山聚星楼六百年青砖古塔', False),
    ('ps-tang-ancestral-hall', 'ps-tang-ancestral-hall-photo.json', ['tang ancestral hall', '鄧氏宗祠', 'yu kiu'], 'Tang Ancestral Hall Ping Shan', '屏山邓氏宗祠正门及三进瓦顶', False),
    ('ps-heritage-museum', 'ps-heritage-museum-photo.json', ['tang clan gallery', 'ping shan police station', '鄧族文物館', '屏山警署'], 'Ping Shan Tang Clan Gallery', '屏山邓族文物馆（旧屏山警署）', False),
    ('lyt-tang-chung-ling', 'lyt-tang-chung-ling-photo.json', ['tang chung ling', '松嶺鄧公祠'], 'Tang Chung Ling Ancestral Hall', '粉岭龙跃头松岭邓公祠', False),
    ('lyt-tin-hau', 'lyt-tin-hau-photo.json', ['tin hau', 'lung yeuk tau', '龍躍頭', '天后'], 'Tin Hau Temple Lung Yeuk Tau', '龙跃头天后宫古庙立面', False),
    ('lyt-ma-wat-wai', 'lyt-ma-wat-wai-photo.json', ['ma wat wai', '麻笏圍'], 'Ma Wat Wai Hong Kong', '龙跃头麻笏围门楼建筑', False),
    ('hku-main-building', 'hku-main-building-photo.json', ['main building', 'loke yew', 'university of hong kong', '本部大樓'], 'Main Building University of Hong Kong', '香港大学本部大楼爱德华红砖正门', False),
    ('hku-fung-ping-shan', 'hku-fung-ping-shan-photo.json', ['fung ping shan', 'museum and art gallery', '馮平山'], 'Fung Ping Shan Building HKU', '香港大学美术博物馆（冯平山楼）', False),
    ('hku-medical-museum', 'hku-medical-museum-photo.json', ['medical sciences', '醫學博物館'], 'Hong Kong Museum of Medical Sciences', '香港医学博物馆红砖阳廊建筑', False),
    ('tw-sam-tung-uk', 'tw-sam-tung-uk-photo.json', ['sam tung uk', '三棟屋'], 'Sam Tung Uk Museum Hong Kong', '荃湾三栋屋博物馆客家围屋', False),
    ('tw-the-mills', 'tw-the-mills-photo.json', ['the mills', 'nan fung', '南豐紗廠'], 'The Mills Tsuen Wan', '荃湾南丰纱厂活化建筑外观', False),
    ('tm-park', 'tm-park-photo.json', ['tuen mun park', '屯門公園'], 'Tuen Mun Park Hong Kong', '屯门公园河畔林荫水景', False),
    ('tm-kadoorie-pier', 'tm-kadoorie-pier-photo.json', ['kadoorie pier', 'cafeteria', '嘉道理碼頭', '青山灣'], 'Kadoorie Pier Tuen Mun', '屯门青山湾嘉道理码头海堤', False),
    ('si-tombolo', 'si-tombolo-photo.json', ['sharp island', 'tombolo', 'kiu tsui', '橋咀'], 'Sharp Island Tombolo Hong Kong', '西贡桥咀洲天然连岛沙洲与地质径', False),
    ('si-pier', 'si-pier-photo.json', ['sharp island', 'kiu tsui pier', '橋咀', '碼頭'], 'Sharp Island Pier Kiu Tsui', '西贡桥咀岛街渡码头', False),
    ('tm-tin-hau', 'tm-tin-hau-photo.json', ['tap mun', 'tin hau', '塔門', '天后'], 'Tin Hau Temple Tap Mun', '塔门天后古庙外貌', False),
    ('tm-balanced-rock', 'tm-balanced-rock-photo.json', ['tap mun', 'balanced rock', '疊石', '塔門'], 'Balanced Rock Tap Mun', '塔门海崖吕字叠石与大草坡', False),
    # Batch 2 (total 62 areas / 63 routes)
    ('adm-flagstaff', 'adm-flagstaff-photo.json', ['flagstaff house', 'tea ware', '茶具文物館'], 'Flagstaff House Museum of Tea Ware', '茶具文物馆（旗杆屋）白墙廊柱外观', False),
    ('adm-st-john', 'adm-st-john-photo.json', ['st. john', 'cathedral', '聖約翰座堂'], "St. John's Cathedral Hong Kong", '花园道圣约翰座堂石墙与钟楼', False),
    ('adm-cfa', 'adm-cfa-photo.json', ['court of final appeal', 'legislative council', '終審法院'], 'Court of Final Appeal Building Hong Kong', '中环终审法院大楼新古典花岗岩柱廊', False),
    ('pfl-bethanie', 'pfl-bethanie-photo.json', ['bethanie', 'béthanie', '伯大尼'], 'Bethanie Pok Fu Lam Hong Kong', '薄扶林伯大尼修院新哥德式外立面', False),
    ('pfl-pokfulam-farm', 'pfl-pokfulam-farm-photo.json', ['pokfulam farm', 'dairy farm', '薄鳧林牧場', '牛奶公司'], 'Old Dairy Farm Senior Staff Quarters', '薄鳧林牧场（旧牛奶公司职员宿舍）', False),
    ('pfl-waterfall-bay', 'pfl-waterfall-bay-photo.json', ['waterfall bay', '瀑布灣'], 'Waterfall Bay Park Hong Kong', '薄扶林瀑布湾海崖天然飞瀑', False),
    ('ar-lower-dam', 'ar-lower-dam-photo.json', ['aberdeen lower reservoir', 'aberdeen reservoir', '香港仔下水塘'], 'Aberdeen Lower Reservoir Hong Kong', '香港仔下水塘百年花岗岩石坝', False),
    ('ar-upper-dam', 'ar-upper-dam-photo.json', ['aberdeen upper reservoir', 'aberdeen reservoir', '香港仔上水塘'], 'Aberdeen Upper Reservoir Dam Hong Kong', '香港仔上水塘石拱桥与水坝', False),
    ('db-shek-o-peak', 'db-shek-o-peak-photo.json', ["dragon's back", 'shek o peak', '龍脊', '打爛埕頂'], "Dragon's Back Hong Kong", '石澳龙脊打烂埕顶山海湾脊线', False),
    ('db-big-wave-bay', 'db-big-wave-bay-photo.json', ['big wave bay', '大浪灣'], 'Big Wave Bay Beach Hong Kong', '大浪湾泳滩与环山海岸', False),
    ('fm-flower-market', 'fm-flower-market-photo.json', ['flower market', '花墟'], 'Flower Market Road Hong Kong', '旺角花墟道鲜花与园艺街市', False),
    ('fm-bird-garden', 'fm-bird-garden-photo.json', ['yuen po street bird garden', 'bird garden', '雀鳥花園'], 'Yuen Po Street Bird Garden', '太子园圃街雀鸟花园中式回廊', False),
    ('kh-kadoorie-avenue', 'kh-kadoorie-avenue-photo.json', ['kadoorie avenue', 'kadoorie hill', '嘉道理道'], 'Kadoorie Avenue Hong Kong', '加多利山嘉道理道林荫洋房街道', False),
    ('kh-maryknoll', 'kh-maryknoll-photo.json', ['maryknoll', '瑪利諾'], 'Maryknoll Convent School Hong Kong', '窝打老道玛利诺修院学校古迹外墙', False),
    ('lcu-han-tomb', 'lcu-han-tomb-photo.json', ['lei cheng uk han tomb', 'han tomb', '李鄭屋漢墓'], 'Lei Cheng Uk Han Tomb Museum', '李郑屋汉墓博物馆东汉砖室与汉花园', False),
    ('lcu-so-uk', 'lcu-so-uk-photo.json', ['so uk', '蘇屋邨'], 'So Uk Estate Hong Kong', '长沙湾苏屋邨与保留屋邨地标', False),
    ('ktk-sky-garden', 'ktk-sky-garden-photo.json', ['kai tak sky garden', 'sky garden', '啟德空中花園'], 'Kai Tak Sky Garden', '启德空中花园高架绿化步道', False),
    ('ktk-cruise-park', 'ktk-cruise-park-photo.json', ['cruise terminal', '啟德郵輪碼頭'], 'Kai Tak Cruise Terminal Park', '启德邮轮码头公园顶层海港草坪', False),
    ('sm-main-dam', 'sm-main-dam-photo.json', ['shing mun reservoir', '城門水塘'], 'Shing Mun Reservoir Main Dam', '城门水塘主水坝与青山倒影', False),
    ('sm-paperbark', 'sm-paperbark-photo.json', ['paperbark', 'melaleuca', 'shing mun', '白千層', '城門'], 'Shing Mun Reservoir paperbark trees', '城门水塘畔塘白千层林荫夹道', False),
    ('nsw-wedding-bridge', 'nsw-wedding-bridge-photo.json', ['nam sang wai', 'wooden bridge', 'wedding bridge', '南生圍'], 'Nam Sang Wai wooden bridge', '元朗南生围木板桥（婚纱桥）与湿地水面', False),
    ('nsw-eucalyptus', 'nsw-eucalyptus-photo.json', ['nam sang wai', '南生圍'], 'Nam Sang Wai Hong Kong', '元朗南生围赤桉树林荫大道与草地', False),
    ('lk-fung-hang', 'lk-fung-hang-photo.json', ['fung hang', 'luk keng', '鳳坑', '鹿頸'], 'Fung Hang Hong Kong', '鹿颈鸡谷树下与凤坑海堤步道', False),
    ('lk-kuk-po', 'lk-kuk-po-photo.json', ['kuk po', 'kai choi', '谷埔', '啟才'], 'Kuk Po Hong Kong', '谷埔海畔芦苇田与启才学校旧址', False),
    ('hsh-hau-ku-shek', 'hsh-hau-ku-shek-photo.json', ['hau ku shek', '居石侯公祠'], 'Hau Ku Shek Ancestral Hall', '上水河上乡明代居石侯公祠正门', False),
    ('hsh-long-valley', 'hsh-long-valley-photo.json', ['long valley', '塱原'], 'Long Valley Wetland Hong Kong', '塱原自然生态公园湿地农田栈道', False),
    ('ytt-chapel', 'ytt-chapel-photo.json', ['st. joseph', 'yim tin tsai', '聖若瑟小堂', '鹽田梓'], "St. Joseph's Chapel Yim Tin Tsai", '西贡盐田梓百年圣若瑟小堂', False),
    ('ytt-salt-pans', 'ytt-salt-pans-photo.json', ['salt pan', 'yim tin tsai', '鹽田', '鹽田梓'], 'Yim Tin Tsai Salt Pans', '西贡盐田梓复修传统海盐晒盐池', False),
    ('mw-tung-wan', 'mw-tung-wan-photo.json', ['tsing ma bridge', 'tung wan', 'ma wan', '東灣', '青馬大橋'], 'Ma Wan Tung Wan Beach Tsing Ma Bridge', '马湾东湾泳滩与青马大桥全景', False),
    ('mw-fong-yuen', 'mw-fong-yuen-photo.json', ['fong yuen', '芳園書室'], 'Fong Yuen Study Hall Ma Wan', '马湾百年古迹芳园书室山花外观', False),
    ('pt-rock-carving', 'pt-rock-carving-photo.json', ['rock carving', 'po toi', '蒲台', '石刻'], 'Rock Carving Po Toi Hong Kong', '蒲台岛青铜时期史前摩崖石刻', False),
    ('pt-lighthouse', 'pt-lighthouse-photo.json', ['nam kok tsui', 'po toi', '126', '蒲台', '燈塔'], 'Nam Kok Tsui Lighthouse Po Toi', '蒲台岛南角咀 126 号纯白灯塔', False),
    # Shenzhen 16 routes
    ('sz-sk-sea-world', 'sz-sk-sea-world-photo.json', ['sea world culture', 'design society', '海上世界文化艺术', '海上世界文化藝術', 'shekou'], 'Sea World Culture and Arts Center Shenzhen', '海上世界文化艺术中心临海白色展馆', False),
    ('sz-sk-old-street', 'sz-sk-old-street-photo.json', ['shekou', '蛇口'], 'Shekou Shenzhen', '蛇口老街区生活风貌', False),
    ('sz-oct-loft-north', 'sz-oct-loft-north-photo.json', ['oct loft', 'oct-loft', '華僑城創意', '华侨城创意'], 'OCT-LOFT Shenzhen', '华侨城创意园北区红砖旧厂房', False),
    ('sz-oct-eco-plaza', 'sz-oct-eco-plaza-photo.json', ['oct', 'overseas chinese town', '華僑城', '华侨城'], 'Overseas Chinese Town Shenzhen', '华侨城林荫园区与广场水景', False),
    ('sz-sb-mangrove', 'sz-sb-mangrove-photo.json', ['mangrove', 'shenzhen bay', '紅樹林', '红树林', '深圳灣'], 'Shenzhen Bay Park Mangrove', '深圳湾红树林海滨湿地滩涂', False),
    ('sz-sb-talent-park', 'sz-sb-talent-park-photo.json', ['talent park', 'houhai', '人才公園', '人才公园', '后海'], 'Shenzhen Talent Park', '深圳人才公园与后海高楼海湾', False),
    ('sz-nt-south-gate', 'sz-nt-south-gate-photo.json', ['nantou', "xin'an ancient", '南頭古城', '南头古城'], 'Nantou Ancient City Shenzhen', '南头古城青砖南城门与拱廊', False),
    ('sz-nt-zhongshan-park', 'sz-nt-zhongshan-park-photo.json', ['zhongshan park shenzhen', 'nanshan zhongshan', '南山中山公园', '南山中山公園', 'shenzhen'], 'Zhongshan Park Nanshan Shenzhen', '南山中山公园古荔荫道', False),
    ('sz-lh-top-plaza', 'sz-lh-top-plaza-photo.json', ['lianhuashan', 'lianhua hill', '蓮花山', '莲花山'], 'Lianhuashan Park Shenzhen', '莲花山公园山顶平台与福田中轴视野', False),
    ('sz-lh-upperhills', 'sz-lh-upperhills-photo.json', ['upperhills', 'upper hills', '深業上城', '深业上城'], 'UpperHills Shenzhen', '深业上城红黄墙开放平台', False),
    ('sz-lh-bijiashan', 'sz-lh-bijiashan-photo.json', ['bijiashan', 'bijia hill', '筆架山', '笔架山'], 'Bijia Hill Park Shenzhen', '笔架山公园山林绿道', False),
    ('sz-yl-lizhi-park', 'sz-yl-lizhi-park-photo.json', ['lychee park', 'lizhi park', '荔枝公園', '荔枝公园'], 'Lychee Park Shenzhen', '荔枝公园湖面与对岸罗湖福田大厦群', False),
    ('sz-dm-pedestrian', 'sz-dm-pedestrian-photo.json', ['dongmen', '東門', '东门'], 'Dongmen Pedestrian Street Shenzhen', '罗湖东门老街商业步行街景', False),
    ('sz-dm-peoples-park', 'sz-dm-peoples-park-photo.json', ['shenzhen', 'luohu', '深圳', '羅湖', '罗湖'], "People's Park Shenzhen", '罗湖人民公园林荫园林', False),
    ('sz-hqb-seg', 'sz-hqb-seg-photo.json', ['seg plaza', 'huaqiangbei', '賽格廣場', '赛格广场', '華強北', '华强北'], 'SEG Plaza Huaqiangbei Shenzhen', '华强北赛格广场与商业大道', False),
    ('sz-hqb-central-park', 'sz-hqb-central-park-photo.json', ['shenzhen central park', 'futian', 'shenzhen', '深圳', '福田'], 'Shenzhen Central Park', '福田中心公园河畔绿带与中轴大厦', False),
    ('sz-yt-dameisha-boardwalk', 'sz-yt-dameisha-boardwalk-photo.json', ['yantian', 'seaside promenade', 'boardwalk', '海濱棧道', '海滨栈道'], 'Yantian Seaside Promenade Shenzhen', '盐田区海滨栈道临海步道', False),
    ('sz-ml-dam', 'sz-ml-dam-photo.json', ['meilin', '梅林'], 'Meilin Reservoir Shenzhen', '梅林水库大坝湖水与山景', False),
    ('sz-qh-stone-park', 'sz-qh-stone-park-photo.json', ['qianhai', '前海'], 'Qianhai Stone Park Shenzhen', '前海石公园海湾岸堤与夕阳视野', False),
    ('sz-qh-happy-harbor', 'sz-qh-happy-harbor-photo.json', ['happy harbor', 'bay glory', '歡樂港灣', '欢乐港湾', 'qianhai'], 'Happy Harbor Baoan Shenzhen', '宝安欢乐港湾与湾区之光摩天轮', False),
    ('sz-tl-peak', 'sz-tl-peak-photo.json', ['tanglang', '塘朗山'], 'Tanglang Mountain Shenzhen', '塘朗山山脊观景点与市区视野', False),
    ('sz-dp-fortress', 'sz-dp-fortress-photo.json', ['dapeng', '大鵬', '大鹏'], 'Dapeng Fortress Shenzhen', '大鹏所城古城门与历史城墙', False),
    ('sz-dp-jiaochangwei', 'sz-dp-jiaochangwei-photo.json', ['jiaochangwei', '較場尾', '较场尾', 'dapeng'], 'Jiaochangwei Shenzhen', '大鹏较场尾海滩海岸民宿带', False),
    ('sz-ymk-coastal-road', 'sz-ymk-coastal-road-photo.json', ['yangmeikeng', 'luzui', '楊梅坑', '杨梅坑', '鹿嘴'], 'Yangmeikeng Shenzhen', '杨梅坑—鹿嘴海岸悬崖海景路', False),
    ('sz-gk-south-gate', 'sz-gk-south-gate-photo.json', ['gankeng', '甘坑'], 'Gankeng Hakka Town Shenzhen', '甘坑客家古镇青砖水岸建筑', False),
    ('sz-df-oil-street', 'sz-df-oil-street-photo.json', ['dafen', '大芬'], 'Dafen Oil Painting Village Shenzhen', '大芬油画村太阳广场街巷画坊', False),
    ('sz-df-art-museum', 'sz-df-art-museum-photo.json', ['dafen', '大芬'], 'Dafen Art Museum Shenzhen', '大芬美术馆现代外观', False),
    # Shenzhen Batch 2 (15 routes -> total 31 SZ routes)
    ('sz2-xm-park', 'sz2-xm-park-photo.json', ['xiangmi', '香蜜'], 'Xiangmi Park Shenzhen', '香蜜公园空中栈道与荔枝林海', False),
    ('sz2-dsh-park', 'sz2-dsh-park-photo.json', ['dasha', '大沙河', 'shenzhen'], 'Dasha River Park Shenzhen', '大沙河公园与生态碧道', False),
    ('sz2-xw-mangrove', 'sz2-xw-mangrove-photo.json', ['xiwan', '西灣', '西湾', 'shenzhen', 'baoan'], 'Xiwan Mangrove Park Shenzhen', '西湾红树林湿地公园海滨长廊', False),
    ('sz2-xa-old-street', 'sz2-xa-old-street-photo.json', ["xin'an park", 'xinan park', '新安公園', '新安公园', 'baoan', 'shenzhen'], "Xin'an Park Baoan Shenzhen", '宝安新安公园湖畔园林', False),
    ('sz2-sw-village', 'sz2-sw-village-photo.json', ['shuiwei', '水圍', '水围'], 'Shuiwei Village Shenzhen', '福田水围村牌坊与街区', False),
    ('sz2-sw-huanggang-park', 'sz2-sw-huanggang-park-photo.json', ['huanggang park', '皇崗公園', '皇岗公园', 'futian', 'shenzhen'], 'Huanggang Park Shenzhen', '皇岗公园林荫绿丘', False),
    ('sz2-hh-park', 'sz2-hh-park-photo.json', ['honghu', '洪湖'], 'Honghu Park Shenzhen', '罗湖洪湖公园荷塘与湖堤', False),
    ('sz2-dh-park', 'sz2-dh-park-photo.json', ['donghu', '東湖', '东湖', 'shenzhen'], 'Donghu Park Shenzhen', '罗湖东湖公园林荫大道', False),
    ('sz2-wt-xiantong', 'sz2-wt-xiantong-photo.json', ['xiantong', 'wutong', '仙桐', '梧桐山', 'shenzhen'], 'Xiantong Sports Park Wutong Mountain Shenzhen', '仙桐体育公园半山林道', False),
    ('sz2-xms-beizaijiao', 'sz2-xms-beizaijiao-photo.json', ['beizaijiao', 'xiaomeisha', '背仔角', '小梅沙'], 'Beizaijiao Lighthouse Shenzhen', '背仔角灯塔与海岸礁石栈道', False),
    ('sz-yt-dameisha-park', 'sz-yt-dameisha-park-photo.json', ['dameisha', '大梅沙'], 'Dameisha Beach Park Shenzhen', '大梅沙海滨公园沙滩与海景', False),
    ('sz-yt-seafood-street', 'sz-yt-seafood-street-photo.json', ['yantian', 'seafood', '鹽田', '盐田'], 'Yantian Seafood Street Shenzhen', '盐田海鲜街海滨栈道', False),
    ('sz2-gm-hongqiao', 'sz2-gm-hongqiao-photo.json', ['hongqiao', 'guangming', '虹橋公園', '虹桥公园', '光明'], 'Guangming Hongqiao Park Shenzhen', '光明虹桥公园空中红桥', False),
    ('sz2-lh2-music-park', 'sz2-lh2-music-park-photo.json', ['baishilong', '白石龍', '白石龙', 'longhua', 'shenzhen'], 'Baishilong Music Park Shenzhen', '龙华白石龙音乐公园草坡', False),
    ('sz2-gl-old-market', 'sz2-gl-old-market-photo.json', ['guanlan', '觀瀾', '观澜'], 'Guanlan Ancient Market Shenzhen', '观澜古墟清代商埠老街与碉楼', False),
    ('sz2-hh2-hehu', 'sz2-hh2-hehu-photo.json', ['hehu', 'crane lake', '鶴湖', '鹤湖'], 'Crane Lake Hakka Residence Longgang Shenzhen', '龙岗鹤湖新居客家围屋', False),
    ('sz2-ps-dawan', 'sz2-ps-dawan-photo.json', ['dawan', 'pingshan', '大萬世居', '大万世居', '坪山'], 'Dawan Residence Pingshan Shenzhen', '坪山大万世居清代方形围屋', False),
]

def query_commons(params_dict):
    params = urllib.parse.urlencode(params_dict)
    url = f'https://commons.wikimedia.org/w/api.php?{params}'
    res = subprocess.run(
        ['curl', '-fLsS', '--retry', '4', '--retry-all-errors', '--max-time', '25', '-A', 'HongKongWandering-MVP-Research/0.1 (local educational city guide)', url],
        capture_output=True, text=True
    )
    if res.returncode != 0 or not res.stdout.strip():
        return None
    try:
        return json.loads(res.stdout)
    except Exception:
        return None

def pick_best(pid, raw_data, keywords_any):
    coord = places[pid]['coordinates']
    pages = (raw_data or {}).get('query', {}).get('pages', {})
    candidates = []
    for pg_id, pg in pages.items():
        title = pg.get('title', '')
        tl = title.lower()
        if not tl.endswith(('.jpg', '.jpeg', '.png')):
            continue
        ii_list = pg.get('imageinfo') or []
        if not ii_list:
            continue
        ii = ii_list[0]
        ext = ii.get('extmetadata') or {}
        desc = ext.get('ImageDescription', {}).get('value', '').lower()
        cats = ext.get('Categories', {}).get('value', '').lower()
        text_blob = f"{tl} {desc} {cats}"
        if keywords_any and not any(kw.lower() in text_blob for kw in keywords_any):
            continue
        # Avoid indoor-only plaques or historical pre-2010 if newer exists
        lic_short = ext.get('LicenseShortName', {}).get('value', '')
        lic_url = ext.get('LicenseUrl', {}).get('value', '').replace('http://creativecommons.org/', 'https://creativecommons.org/')
        artist = ext.get('Artist', {}).get('value', '')
        if not lic_short.startswith(('CC BY', 'CC0')) or not lic_url.startswith('https://creativecommons.org/') or not artist:
            continue
        if not (ii.get('thumburl', '').startswith(('https://thumb.wikimedia.org/', 'https://upload.wikimedia.org/'))):
            continue
        if not ii.get('descriptionurl', '').startswith('https://commons.wikimedia.org/'):
            continue
        dt_str = ext.get('DateTimeOriginal', {}).get('value', '') or title
        yr = extract_year(dt_str)
        gps_lat = ext.get('GPSLatitude', {}).get('value')
        gps_lon = ext.get('GPSLongitude', {}).get('value')
        has_valid_gps = False
        dist_m = 999999
        if gps_lat and gps_lon:
            try:
                dist_m = haversine(coord[0], coord[1], float(gps_lon), float(gps_lat))
                if dist_m <= 350:
                    has_valid_gps = True
            except Exception:
                pass
        if gps_lat and gps_lon and dist_m > 800:
            continue
        # Score strongly prefers recent photos (>= 2015) AND GPS <= 350m
        recent_bonus = 2000 if yr >= 2016 else (1200 if yr >= 2012 else 0)
        gps_bonus = 800 if has_valid_gps else 0
        plaque_penalty = -300 if 'plaque' in tl or 'inscription' in tl else 0
        score = recent_bonus + gps_bonus + yr + plaque_penalty
        candidates.append((score, yr, has_valid_gps, round(dist_m) if has_valid_gps else None, pg_id, title))
    candidates.sort(reverse=True)
    return candidates[0] if candidates else None

for pid, raw_fname, kws, search_q, caption_base, force in TARGETS:
    if pid in selected and not force:
        continue
    out_path = RAW_PHOTOS / raw_fname
    best = None
    best_data = None
    if out_path.exists() and not force:
        best_data = read(out_path)
        best = pick_best(pid, best_data, kws)
    if not best:
        coord = places[pid]['coordinates']
        # Try geosearch around POI first (returns verified GPS files!)
        geo_data = query_commons({
            'action': 'query',
            'format': 'json',
            'generator': 'geosearch',
            'ggscoord': f'{coord[1]}|{coord[0]}',
            'ggsradius': 250,
            'ggsnamespace': 6,
            'ggslimit': 25,
            'prop': 'imageinfo',
            'iiprop': 'url|size|extmetadata',
            'iiurlwidth': 960,
        })
        time.sleep(1.3)
        cand = pick_best(pid, geo_data, kws)
        if cand:
            best = cand
            best_data = geo_data
        else:
            # Fallback to keyword search
            s_data = query_commons({
                'action': 'query',
                'format': 'json',
                'generator': 'search',
                'gsrsearch': search_q,
                'gsrnamespace': 6,
                'gsrlimit': 12,
                'prop': 'imageinfo',
                'iiprop': 'url|size|extmetadata',
                'iiurlwidth': 960,
            })
            time.sleep(1.3)
            cand = pick_best(pid, s_data, kws)
            if cand:
                best = cand
                best_data = s_data
        if best_data and best:
            save(out_path, best_data)
    if best:
        _, yr, has_gps, dist_m, pg_id, title = best
        yr_note = f'（{yr} 年照片）' if yr >= 2010 else ''
        selected[pid] = {
            'rawFile': raw_fname,
            'pageId': int(pg_id),
            'caption': f'{caption_base}{yr_note}'
        }
        print(f"OK   {pid:20s} | pageId={pg_id:10s} | yr={yr} | gps={has_gps} ({dist_m}m) | {title[:45]}", flush=True)
    else:
        print(f"SKIP {pid:20s} | kept existing", flush=True)

save(SEL_PATH, selected)
print(f"Updated place-photos.json with {len(selected)} entries.")
