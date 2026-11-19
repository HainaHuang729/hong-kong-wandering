"""Connect curated walks to sourced transport nodes; cache real foot routing responses."""
import json,pathlib,urllib.request,time,math,subprocess
R=pathlib.Path(__file__).resolve().parents[1]; O=R/'public/data'; D=R/'data/raw'
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
places=read(O/'places.geojson'); ps={f['properties']['id']:f['properties'] for f in places['features']}; areas=read(O/'areas.json'); routes=read(O/'routes.json'); guides=read(R/'data/editorial/place-guides.json')
MTR='https://www.mtr.com.hk/en/customer/services/system_map.html'; TD='https://data.gov.hk/en-data/dataset/hk-td-tis_23-routes-fares-geojson'
services={}
def add(id,name,aid,coord,coordSource,url,service,mode):
 guide={'kind':'transport','minutes':[0,0],'durationNote':'交通节点，候车、候船与站内步行时间另计。','highlights':[service,'按现场指示确认行车方向与上车位置'],'arrivalSteps':[service,'车站标记为代表位置；港铁具体出口、无障碍通道请查站内图。' if mode=='metro' else '核对站牌、目的地与当天班次后上车。'],'transportSourceUrl':url,'contentSourceUrl':url,'checkedAt':'2026-11-02','transportNote':'静态站点资料，无实时到站时间；请查看运营方当日公告。'}
 p={'id':id,'nameZh':name,'coordinates':coord,'district':aid,'categories':next(a['categories'] for a in areas if a['id']==aid),'description':service+'，可作为漫游接入或离开点。','visitDuration':0,'sourceUrl':url,'coordinateSource':coordSource,'coordinateKind':'港铁车站代表点，非具体出口' if mode=='metro' else '运输署巴士站坐标','verifiedAt':'2026-11-02','priority':50,'visitGuide':guide}
 ps[id]=p;guides[id]=guide;services[id]=(mode,service,url)
for id,file,name,aid,service in [('sheungwan-mtr','sheungwan-mtr','上环站','sheungwan','港铁港岛线'),('central-mtr','central-rail','中环站','central','港铁港岛线 / 荃湾线'),('yaumatei-mtr','yaumatei-mtr','油麻地站','yaumatei','港铁荃湾线 / 观塘线'),('jordan-mtr','jordan-mtr','佐敦站','yaumatei','港铁荃湾线'),('tst-mtr','tst-mtr','尖沙咀站','yaumatei','港铁荃湾线')]:
 x=next(x for x in read(D/(file+'.json')) if x['type']=='station' and x['class']=='railway')
 add(id,name,aid,[float(x['lon']),float(x['lat'])],f"https://www.openstreetmap.org/{x['osm_type']}/{x['osm_id']}",MTR,service,'metro')
# Government transport source cached locally during research. Only selected original records are retained.
full=read(D/'td-route-endpoints.geojson') if (D/'td-route-endpoints.geojson').exists() else json.load(open('/tmp/hk-official-bus.json',encoding='utf-8-sig')); excerpt=[]
for id,name,aid,rid,seq,stop,service in [('sheko-bus','石澳巴士总站','sheko',1637,2,1,'城巴 9 · 筲箕湾 ↔ 石澳'),('taio-bus','大澳巴士总站','taio',1724,2,1,'新大屿山巴士 11 · 东涌站 ↔ 大澳'),('stanley-return','赤柱村巴士总站（回程）','repulse',1526,2,1,'城巴 260 · 赤柱村 → 中环交易广场')]:
 f=next(f for f in full['features'] if (f['properties']['routeId'],f['properties']['routeSeq'],f['properties']['stopSeq'])==(rid,seq,stop));excerpt.append(f)
 add(id,name,aid,f['geometry']['coordinates'],TD,f['properties']['hyperlinkE'],service,'bus')
save(D/'td-route-endpoints.geojson',{'type':'FeatureCollection','sourceUrl':'https://static.data.gov.hk/td/routes-fares-geojson/JSON_BUS.json','retrievedAt':'2026-11-02','features':excerpt})
for id in ['kennedy-station','saiyingpun','wanchai-station','ssp-station']:
 services[id]=('metro','港铁荃湾线' if id=='ssp-station' else '港铁港岛线',MTR)
for id in ['cc-pier','yungshue','sokkwu']:
 services[id]=('ferry',{'cc-pier':'渡轮 · 长洲 ↔ 中环五号码头','yungshue':'渡轮 · 榕树湾 ↔ 中环','sokkwu':'渡轮 · 索罟湾 ↔ 中环'}[id],ps[id]['visitGuide']['transportSourceUrl'])
for id in ['repulse-bus','stanley-bus']:services[id]=('bus','城巴 260 · 往赤柱方向',ps[id]['visitGuide']['transportSourceUrl'])
plans={
'repulse':['repulse-bus','repulse-beach','repulse-bus','stanley-bus','stanley-market','murray','stanley-return'],
'sheko':['sheko-bus','sheko-beach','sheko-temple','sheko-bus'],
'kennedy':['kennedy-station','belcher','saiyingpun'],
'sheungwan':['sheungwan-mtr','western','hollywood-park','saiyingpun'],
'central':['sheungwan-mtr','manmo','pmq','taikwun','central-market','central-mtr'],
'wanchai':['wanchai-station','bluehouse','pakta-wan','wanchai-station'],
'shamshuipo':['ssp-station','apliu','meiho','ssp-station'],
'yaumatei':['yaumatei-mtr','theatre','temple-street','jordan-mtr','clocktower','tst-mtr'],
'cheungchau':['cc-pier','cc-paktai','tungwan','cc-pier'],
'lamma':['yungshue','hungshing','sokkwu'],
 'taio':['taio-bus','taio-bridge','taio-temple','taio-hotel','taio-bus']}
def walk(route,ids,suffix):
 file=route['id']+'-transport'+suffix+'.json'; path=D/file
 url='https://routing.openstreetmap.de/routed-foot/route/v1/foot/'+';'.join(','.join(map(str,ps[id]['coordinates'])) for id in ids)+'?overview=full&geometries=geojson&steps=true'
 if not path.exists():
  result=subprocess.run(['curl','-fL','--retry','2','--max-time','35','-sS','-A','HongKongWandering-MVP-Research/0.1',url],capture_output=True,check=True)
  payload=json.loads(result.stdout);assert payload.get('code')=='Ok';path.write_bytes(result.stdout)
  time.sleep(1.2)
 x=read(path); assert x['code']=='Ok'; result=x['routes'][0];snap=max(w['distance'] for w in x['waypoints']);assert snap<=120,(route['id'],snap)
 return {'type':'Feature','properties':{'mode':'walk','routeId':route['id'],'source':'OSM / FOSSGIS OSRM foot','requestUrl':url,'rawFile':file,'placeIds':ids,'distance':result['distance'],'duration':result['duration'],'maxSnapMeters':snap,'license':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© OpenStreetMap contributors / FOSSGIS OSRM'},'geometry':result['geometry']}
for r in routes:
 if r['areaId'] not in plans:continue
 ids=plans[r['areaId']];r['placeIds']=ids
 if r['areaId']=='repulse':
  fs=[walk(r,ids[:3],'-arrival')]+[f for f in r['geometry']['features'] if f['properties']['mode']=='bus']+[walk(r,ids[3:],'-departure')]
 else:fs=[walk(r,ids,'')]
 r['geometry']={'type':'FeatureCollection','features':fs};ws=[f['properties'] for f in fs if f['properties']['mode']=='walk']
 r['distance']=round(sum(w['distance'] for w in ws));r['walkingMinutes']=math.ceil(sum(w['duration'] for w in ws)/60);r['maxSnapMeters']=max(w['maxSnapMeters'] for w in ws);r['requestUrl']=ws[0]['requestUrl'];r['transportNodes']=[]
 for i,id in enumerate(ids):
  if id not in services:continue
  mode,service,url=services[id]; role='start' if i==0 else 'end' if i==len(ids)-1 else 'transfer' if id in ['repulse-bus','stanley-bus'] else 'access'
  instruction={'start':'从这里抵达并开始漫游。','end':'在这里结束漫游，按目的地方向乘车或乘船离开。','transfer':'这里是步行与巴士的衔接点，请核对上、下车方向。','access':'可在这里中途加入，或乘港铁提前结束行程。'}[role]
  r['transportNodes'].append(dict(placeId=id,stopIndex=i,role=role,mode=mode,service=service,instruction=instruction,sourceUrl=url))
 r['itineraryLegs']=[]
 offset=0
 for f in fs:
  prop=f['properties']
  if prop['mode']!='walk':continue
  raw=read(D/prop['rawFile'])
  if r['areaId']=='repulse' and prop['rawFile'].endswith('-departure.json'):offset=3
  for j,leg in enumerate(raw['routes'][0]['legs']):r['itineraryLegs'].append(dict(fromIndex=offset+j,toIndex=offset+j+1,mode='walk',distance=round(leg['distance']),minutes=math.ceil(leg['duration']/60)))
 if r.get('busDistance'):r['itineraryLegs'].append(dict(fromIndex=2,toIndex=3,mode='bus',distance=r['busDistance'],minutes=None))
 for n in r['transportNodes']:
  if n['role']=='start':
   arrivals={'repulse-bus':'从中环交易广场乘城巴 260 往赤柱，在浅水湾泳滩站下车后开始漫游。','sheko-bus':'乘港铁到筲箕湾，再转城巴 9 到石澳总站开始漫游。','taio-bus':'乘港铁到东涌，再转新大屿山巴士 11 到大澳总站开始漫游。','cc-pier':'从中环五号码头乘渡轮抵达长洲，再开始岛上步行。','yungshue':'从中环乘榕树湾渡轮抵达；跨岛步行后在索罟湾乘船离开。'}
   n['instruction']=arrivals.get(n['placeId'],n['instruction'])
  if n['role']=='transfer':n['instruction']='游览浅水湾后回此站，乘城巴 260 往赤柱。' if n['placeId']=='repulse-bus' else '在赤柱村站下车，转步行逛市场与海旁。'
 r['transportNote']='站点和线路为静态资料，班次与末班时间请查运营方；港铁标记为车站代表位置，站内通道不计入步行导航。'
 if r['areaId']=='lamma':r['transportNote']+=' 跨岛步行中段未列可乘巴士或港铁的接出点，请预留走到码头及候船时间。'
 a=next(a for a in areas if a['id']==r['areaId']);a['placeIds']=list(dict.fromkeys(a['placeIds']+ids));coords=[c for f in fs for c in f['geometry']['coordinates']];a['bounds']=[min(c[0] for c in coords)-.002,min(c[1] for c in coords)-.002,max(c[0] for c in coords)+.002,max(c[1] for c in coords)+.002]
 print(r['id'],r['distance'],r['walkingMinutes'],r['maxSnapMeters'],flush=True)
places['features']=[{'type':'Feature','properties':p,'geometry':{'type':'Point','coordinates':p['coordinates']}} for p in ps.values()]
save(O/'places.geojson',places);save(O/'routes.json',routes);save(O/'areas.json',areas);save(R/'data/editorial/place-guides.json',guides)
save(O/'routes.geojson',{'type':'FeatureCollection','features':[f for r in routes for f in r['geometry']['features']]})
