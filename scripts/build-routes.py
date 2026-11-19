import json,pathlib,urllib.request,time,math
R=pathlib.Path(__file__).resolve().parents[1]; raw=R/'data/raw'; out=R/'public/data'
d=json.loads((out/'places.geojson').read_text()); areas=json.loads((out/'areas.json').read_text());p={f['properties']['id']:f['properties'] for f in d['features']}
for pid,name,en,aid,file,index in [('stanley-market','赤柱市场','Stanley Market','repulse','stanley-market.json',1),('taio-bridge','大澳涌行人桥','Tai O Creek Pedestrian Bridge','taio','taio-bridge-refined.json',0),('yungshue','榕树湾码头','Yung Shue Wan Pier','lamma','yungshue-refined.json',0),('sokkwu','索罟湾二号码头','Sok Kwu Wan Pier No. 2','lamma','sokkwu-refined.json',0)]:
 x=json.loads((raw/file).read_text())[index];a=next(a for a in areas if a['id']==aid)
 p[pid]={**p.get(pid,{}),'id':pid,'nameZh':name,'nameEn':en,'coordinates':[float(x['lon']),float(x['lat'])],'district':aid,'categories':a['categories'],'sourceUrl':a['sourceUrl'],'coordinateSource':f"https://www.openstreetmap.org/{x['osm_type']}/{x['osm_id']}",'coordinateKind':'OSM 代表点，非保证无障碍入口','verifiedAt':'2026-11-02','priority':a['priority']*5,'visitDuration':15}
descriptions={
'repulse-beach':'山坡围着海湾，沙滩与滨海空间适合放慢脚步。可以只看海，不把游泳当成行程前提。',
'stanley-market':'在赤柱市场一带逛小街，再走向海旁。购物与用餐随兴安排，不预设店铺营业。',
'murray':'海边的美利楼是赤柱建筑景观之一；这条路线以外观欣赏为主。',
'sheko-beach':'石澳村旁的沙滩，是这段短漫游的海景停留点。留意海况与现场旗号。',
'sheko-temple':'村内的天后庙是街巷中的文化节点。参观时尊重祭祀活动，未开放时只在外部停留。',
'kennedy-station':'港岛线车站，为坚尼地城漫游提供公共交通入口。地图标示车站代表位置，实际出口请看现场指示。',
'belcher':'坚尼地城的公共公园，可在街道探索途中停下来休息。',
'saiyingpun':'港岛线西营盘站。周边坡道多，车站代表点不代表具体出口或无障碍通道。',
'western':'上环的历史建筑地标。沿外墙观察建筑细部，再转入附近街道。',
'hollywood-park':'荷李活道沿线的公共公园，为旧街漫步留出一段绿意。',
'manmo':'荷李活道上的文武庙，把信仰空间与旧城街景连在一起。尊重现场参拜者。',
'pmq':'旧建筑活化而成的创意空间。可看建筑外观，展览与店铺以现场开放安排为准。',
 'taikwun':'中环的历史建筑群与文化空间。行程不预设展览、预约或室内通道一定开放。',
'central-market':'中环街市是旧城建筑漫游的一个节点，可从附近街道观察其街区关系。',
'wanchai-station':'港岛线湾仔站，适合作为蓝屋与湾仔旧街探索的交通起点。',
'bluehouse':'石水渠街一带的蓝屋建筑群保留唐楼街景。这里也是生活空间，拍摄时请尊重住户。',
'pakta-wan':'隆安街的北帝庙，是湾仔旧街中的庙宇地标。入内参观以现场开放安排为准。',
'ssp-station':'深水埗站连接九龙街区与港铁网络，出站后进入街市与商业街环境。',
'apliu':'鸭寮街一带适合观察街铺与摊档。地图为街道代表点，不是某家店铺。',
'meiho':'石硖尾的美荷楼，是认识香港社区与住宅建筑的地点。室内参观另查开放资讯。',
'theatre':'油麻地戏院是区内历史建筑与粤剧表演场所。行程以外观为主，不包含演出票。',
'temple-street':'穿行庙街一带，感受油麻地与佐敦的街道尺度；摊档经营时间各异。',
'clocktower':'尖沙咀海旁的钟楼，把这段街区漫游带到维港边。',
'cc-pier':'长洲与中环之间的渡轮抵达点。回程请提前查询新渡轮班次。',
'cc-paktai':'长洲北帝庙及附近广场，是岛上步行探索的文化停留点。',
'tungwan':'从长洲街巷转向东湾，沙滩是休息看海的停留点。',
'yungshue':'从榕树湾码头进入南丫岛。向村内街道走，再接往洪圣爷湾。',
'hungshing':'南丫岛洪圣爷湾泳滩是跨岛步行的海景停留点；后续路线有坡度。',
'sokkwu':'索罟湾二号码头为回中环的交通节点。抵达前请核对港九小轮当天班次。',
 'taio-bridge':'大澳涌行人桥连接水道两侧，适合观察棚屋与村落的空间关系。',
 'taio-temple':'吉庆街附近的关帝古庙，是大澳渔村中的历史文化节点。',
 'taio-hotel':'由旧警署活化而来的文物酒店，位于石仔埗一带。路线以外围欣赏为主。'}
for id,v in p.items():v['description']=descriptions[id]
for a in areas:
 ps=[p[id]['coordinates'] for id in a['placeIds']];a['coordinates']=ps[0];a['bounds']=[min(x[0] for x in ps)-.003,min(x[1] for x in ps)-.003,max(x[0] for x in ps)+.003,max(x[1] for x in ps)+.003]
 if a['id']=='lamma':a['weather']='适合凉爽、干燥的白天；沿途有上落坡，带水与防晒，雷雨不推荐。'
 if a['id']=='central':a['weather']='建议干燥天气；坡道、楼梯雨后易滑，不承诺无障碍。'
(out/'areas.json').write_text(json.dumps(areas,ensure_ascii=False,indent=2))
(out/'places.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':v['coordinates']},'properties':v} for v in p.values()]},ensure_ascii=False,indent=2))
titles=['浅水湾到赤柱，慢一点看海','石澳村与海滨短漫游','坚尼地城走到西营盘','上环到西营盘，旧街日常','上环—中环，建筑之间','湾仔，蓝屋旁的旧街','深水埗，逛进市井生活','油麻地—佐敦—尖沙咀','长洲，庙前与东湾','榕树湾走到索罟湾','大澳，沿水道慢慢走']
routes=[]
for a,title in zip(areas,titles):
 ids=a['placeIds'][:]
 if a['id']=='cheungchau':ids+=['cc-pier']
 actual=ids if a['id']!='repulse' else ids[1:]
 coords=';'.join(','.join(str(v) for v in p[id]['coordinates']) for id in actual)
 url=f'https://routing.openstreetmap.de/routed-foot/route/v1/foot/{coords}?overview=full&geometries=geojson&steps=true'
 path=raw/('route-'+a['id']+'.json')
 try:
  if path.exists():res=json.loads(path.read_text())
  else:
   time.sleep(1.2);req=urllib.request.Request(url,headers={'User-Agent':'HongKongWandering-MVP-Research/0.1'});res=json.load(urllib.request.urlopen(req,timeout=30));path.write_text(json.dumps(res,ensure_ascii=False,indent=2))
  r=res['routes'][0];snap=max(x['distance'] for x in res['waypoints']);geometry=r['geometry']
  print(a['id'],round(r['distance']),round(r['duration']/60),'snap',round(snap), 'roads',list(dict.fromkeys(s['name'] for l in r['legs'] for s in l['steps'] if s['name'])),flush=True)
  status='pending' if a['id']=='repulse' or snap>120 else 'network-checked'
 except Exception as e:print('FAIL',a['id'],e,flush=True);status='pending';r=None;geometry=None
 cats=a['categories'];ints=['散步'];ints+=['看海'] if '山海之间' in cats else [];ints+=['坐船'] if a['id'] in ['cheungchau','lamma'] else [];ints+=['看建筑','逛老街','文化探索'] if '人文寻踪' in cats else [];ints+=['看日落'] if '黄昏出逃' in cats else [];ints+=['轻徒步'] if a['id']=='lamma' else []
 transportSource='https://www.mtr.com.hk/en/customer/services/system_map.html'
 if a['id']=='repulse':transportSource='https://www.citybus.com.hk/en/uploadedPressRelease/21535_20250530_ENG.pdf'
 elif a['id']=='cheungchau':transportSource='https://www.sunferry.com.hk/en/route-and-fare/timetable?route=central-to-cheung-chau'
 elif a['id']=='lamma':transportSource='https://hkkf.com.hk/en/lamma-island/lamma-island-hiking-trails-places-of-interest/'
 elif a['id']=='taio':transportSource='https://www.nlb.com.hk/en/route/13'
 elif a['id']=='sheko':transportSource='https://mobile.citybus.com.hk/nwp3/?f=1&ds=9&dsmode=1&l=1'
 routes.append({'id':'route-'+a['id'],'areaId':a['id'],'title':title,'description':a['description'],'placeIds':ids,'status':status,'verificationNote':('巴士接驳有静态资料依据，但尚无核实的巴士几何及浅水湾完整步行段。仅展示赤柱局部步行段，整线待核实。' if a['id']=='repulse' else '已核对 OSM foot 路网响应、地点匹配与吸附距离；未实地踏查，不能保证当天通行。'),'distance':round(r['distance']) if r and status!='pending' else None,'walkingMinutes':math.ceil(r['duration']/60) if r and status!='pending' else None,'visitMinutes':120 if a['duration']=='2 小时' else 300 if a['duration']=='半天' else 600,'transport':a['transport'],'transportSource':transportSource,'sourceUrl':a['sourceUrl'],'verifiedAt':'2026-11-02','timeOfDay':a['timeOfDay'],'notes':'请使用合法过街设施；楼梯、坡度与临时封闭以现场为准。寺庙、建筑内部不保证开放，可在外部欣赏。'+('岛上需留足回程候船时间。' if a['id'] in ['cheungchau','lamma'] else ''),'interests':ints,'preferences':['公共交通方便']+(['不太累'] if r and r['distance']<1600 and a['id']!='central' else []),'geometry':{'type':'FeatureCollection','features':[{'type':'Feature','geometry':geometry,'properties':{'mode':'walk','source':'OSM / FOSSGIS OSRM foot','routeId':'route-'+a['id'],'distance':r['distance'],'duration':r['duration'],'partial':status=='pending'}}] if geometry else []},'requestUrl':url,'maxSnapMeters':round(snap,1) if r else None})
(out/'routes.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
(out/'routes.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[f for r in routes for f in r['geometry']['features']]},ensure_ascii=False,indent=2))
