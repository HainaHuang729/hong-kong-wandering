import json, pathlib, urllib.request, urllib.parse, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw'; out=ROOT/'public/data'
D='https://www.discoverhongkong.com/eng/'
rows=[
('repulse','浅水湾—赤柱','Repulse Bay & Stanley','山海之间,黄昏出逃','在沙滩停一停，再搭巴士去赤柱看海。','半天','巴士接驳；城巴 260 途经浅水湾与赤柱。','place-to-go/travel.guide-repulse-bay.html', [('repulse-beach','浅水湾泳滩','Repulse Bay Beach'),('stanley-market','赤柱市场','Stanley Market'),('murray','美利楼','Murray House')]),
('sheko','石澳','Shek O','山海之间,城市漫步','沿村落的小街，走向石澳的海风。','半天','先抵达筲箕湾，再查询前往石澳的公共交通。','place-to-go/travel.guide-shek-o-beach.html',[('sheko-beach','石澳泳滩','Shek O Beach'),('sheko-temple','石澳天后庙','Tin Hau Temple Shek O')]),
('kennedy','坚尼地城','Kennedy Town','城市漫步,黄昏出逃','沿着港岛西岸，慢慢读一段旧城。','半天','港铁坚尼地城站进入，西营盘站离开。','neighbourhoods/central-and-western-district/how-to-spend-your-day-in-kennedy-town.html',[('kennedy-station','坚尼地城站','Kennedy Town station'),('belcher','卑路乍湾公园','Belcher Bay Park'),('saiyingpun','西营盘站','Sai Ying Pun station')]),
('sheungwan','上环—西营盘','Sheung Wan & Sai Ying Pun','城市漫步,人文寻踪','从西港城出发，看电车街与旧街区的日常。','2 小时','港铁上环站进入，西营盘站离开。','neighbourhoods/central-and-western-district.html',[('western','西港城','Western Market'),('hollywood-park','荷李活道公园','Hollywood Road Park'),('saiyingpun','西营盘站','Sai Ying Pun station')]),
('central','中环—半山','Central & Mid-Levels','城市漫步,人文寻踪','文武庙、创意空间与旧建筑，藏在坡道之间。','半天','港铁上环或中环站进入；坡道及楼梯较多。','neighbourhoods/central-and-western-district.html',[('manmo','文武庙','Man Mo Temple Sheung Wan'),('pmq','元创方','PMQ'),('taikwun','大馆','Tai Kwun'),('central-market','中环街市','Central Market')]),
('wanchai','湾仔','Wan Chai','城市漫步,人文寻踪','在蓝屋和旧街之间，发现建筑里的生活。','2 小时','港铁湾仔站进入及离开。','place-to-go/travel.guide-the-blue-house.html',[('wanchai-station','湾仔站','Wan Chai station'),('bluehouse','蓝屋','Blue House'),('pakta-wan','湾仔北帝庙','Pak Tai Temple Wan Chai')]),
('shamshuipo','深水埗','Sham Shui Po','城市漫步,人文寻踪','街市、布料与老社区，边走边发现市井香港。','2 小时','港铁深水埗站进入；沿街公共空间为主。','neighbourhoods/sham-shui-po.html',[('ssp-station','深水埗站','Sham Shui Po station'),('apliu','鸭寮街','Apliu Street'),('meiho','美荷楼','Mei Ho House')]),
('yaumatei','油麻地—佐敦','Yau Ma Tei & Jordan','城市漫步,人文寻踪,黄昏出逃','由老戏院走到海港，把街道与天际线串起来。','半天','港铁油麻地站进入，尖沙咀站离开。','place-to-go/travel.guide-yau-ma-tei-theatre.html',[('theatre','油麻地戏院','Yau Ma Tei Theatre'),('temple-street','庙街','Temple Street Jordan'),('clocktower','尖沙咀钟楼','Clock Tower Tsim Sha Tsui')]),
('cheungchau','长洲','Cheung Chau','离岛出走,山海之间,城市漫步','下船后不赶路，去庙前广场和东湾吹吹风。','半天','中环 5 号码头乘新渡轮往返长洲；班次以运营方为准。','neighbourhoods/outlying-islands/cheung-chau-island-hopping.html',[('cc-pier','长洲渡轮码头','Cheung Chau Ferry Pier'),('cc-paktai','长洲北帝庙','Pak Tai Temple Cheung Chau'),('tungwan','长洲东湾泳滩','Tung Wan Beach Cheung Chau')]),
('lamma','南丫岛','Lamma Island','离岛出走,山林漫游,山海之间','从榕树湾走到索罟湾，让海风陪你翻过小山。','一整天','中环乘港九小轮至榕树湾，索罟湾乘船返回；出发前查尾班船。','outdoors/city-to-wild-in-minutes-hong-kongs-easy-escapes.html',[('yungshue','榕树湾码头','Yung Shue Wan Ferry Pier'),('hungshing','洪圣爷湾泳滩','Hung Shing Yeh Beach'),('sokkwu','索罟湾码头','Sok Kwu Wan Ferry Pier')]),
('taio','大澳','Tai O','离岛出走,人文寻踪,山海之间','沿水道与棚屋外的小路，慢慢走进渔村。','一整天','由东涌查询前往大澳的巴士；不提供未经核实的班次与车程。','place-to-go/travel.guide-tai-o.html',[('taio-bridge','大涌桥','Tai Chung Bridge Tai O'),('taio-temple','大澳关帝庙','Kwan Tai Temple Tai O'),('taio-hotel','大澳文物酒店','Tai O Heritage Hotel')]),
]
def get(url,path):
 if path.exists():
  try:return json.loads(path.read_text())
  except:pass
 time.sleep(1.15)
 req=urllib.request.Request(url,headers={'User-Agent':'HongKongWandering-MVP-Research/0.1 (local educational city guide)'})
 with urllib.request.urlopen(req,timeout=25) as r: data=json.load(r)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
 return data
places={}; areas=[]
for rank,row in enumerate(rows):
 aid,zh,en,cats,desc,duration,trans,source,stops=row
 ids=[]
 for pid,pzh,query in stops:
  ids.append(pid)
  if pid in places:continue
  try:
   params=urllib.parse.urlencode({'q':query+' Hong Kong','format':'json','limit':3,'viewbox':'113.8,22.6,114.45,22.15','bounded':1})
   results=get('https://nominatim.openstreetmap.org/search?'+params,raw/(pid+'.json'))
   if not results: print('MISSING',pid,flush=True);continue
   p=results[0]; coord=[float(p['lon']),float(p['lat'])]
   places[pid]={'id':pid,'nameZh':pzh,'nameEn':query,'coordinates':coord,'district':aid,'categories':cats.split(','),'description':pzh+'是这段漫游的停留点。可在此观察周边街景，按自己的节奏停留。','sourceUrl':D+source,'coordinateSource':f"https://www.openstreetmap.org/{p['osm_type']}/{p['osm_id']}",'coordinateKind':'OSM 代表点，非保证无障碍入口','verifiedAt':'2026-11-02','priority':rank*5+len(ids),'visitDuration':15}
   print(pid,coord,p['display_name'],flush=True)
  except Exception as e:print('FAIL',pid,e,flush=True)
 areas.append({'id':aid,'nameZh':zh,'nameEn':en,'categories':cats.split(','),'description':desc,'duration':duration,'transport':trans,'sourceUrl':D+source,'verifiedAt':'2026-11-02','placeIds':ids,'weather':'晴天或多云；雷雨时避开海岸和山径。','timeOfDay':'白天；海滨可选择傍晚，注意回程交通。','priority':rank,'status':'researched'})
(out/'places.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':p['coordinates']},'properties':p} for p in places.values()]},ensure_ascii=False,indent=2))
for a in areas:
 ps=[places[i]['coordinates'] for i in a['placeIds'] if i in places]
 a['coordinates']=ps[0] if ps else None
 a['bounds']=[min(p[0] for p in ps)-.003,min(p[1] for p in ps)-.003,max(p[0] for p in ps)+.003,max(p[1] for p in ps)+.003] if ps else None
 a['boundsNote']='内容浏览范围：据所选地点外扩约 300 米，不是行政边界。'
(out/'areas.json').write_text(json.dumps(areas,ensure_ascii=False,indent=2))
