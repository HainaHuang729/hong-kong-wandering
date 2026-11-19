"""Add five source-backed districts without replacing existing IDs, routes or local records."""
import json,pathlib,subprocess,time,math
R=pathlib.Path(__file__).resolve().parents[1];O=R/'public/data';D=R/'data/raw'
def read(p):return json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
e=read(R/'data/editorial/expansion-five.json');S=e['sources'];new=e['areas'];areas=read(O/'areas.json');routes=read(O/'routes.json');places=read(O/'places.geojson');ps={f['properties']['id']:f['properties'] for f in places['features']};guides=read(R/'data/editorial/place-guides.json');cats=read(R/'data/editorial/route-categories.json');services={}
static='静态资料，不含实时班次、临时改道或开放状态。候车、候船及往返交通时间另计。'
def areaof(id):return next(a for a in new if id in a['placeIds'])
def add(id,name,en,osm,file,src,mins,highlights,mode=None,service=None):
 a=areaof(id)
 if id=='sk-bus':
  f=next(f for f in read(D/'td-saikung-endpoints.geojson')['features'] if f['properties']['routeSeq']==1);coord=f['geometry']['coordinates'];cs='https://data.gov.hk/en-data/dataset/hk-td-tis_23-routes-fares-geojson'
 else:
  candidates=read(D/(file+'.json'));x=next(x for x in candidates if x['osm_id']==osm) if osm else candidates[0];coord=[float(x['lon']),float(x['lat'])];cs=f"https://www.openstreetmap.org/{x['osm_type']}/{x['osm_id']}"
 url=S[src] if src else cs
 arrival=[a['transport'],'按地图中的真实步行路线到此点；车站出口与现场围挡以指示为准。']
 g=dict(kind='transport' if mode else 'sightseeing',minutes=mins,durationNote='交通节点，站内步行和候车船另计。' if mode else '编辑建议，包含观看和休息；不含两站之间步行与往返交通。',highlights=highlights,arrivalSteps=arrival,transportSourceUrl=S[a['transportSource']],contentSourceUrl=url,checkedAt='2026-11-02',transportNote=static)
 p=dict(id=id,nameZh=name,nameEn=en,coordinates=coord,district=a['id'],categories=list(a['categories']),description=('；'.join(highlights)+'。'),sourceUrl=url,coordinateSource=cs,coordinateKind='运输署巴士总站坐标' if id=='sk-bus' else 'OSM 代表点，非保证无障碍入口；具体站口按现场指示。',verifiedAt='2026-11-02',priority=60+list(z['id'] for z in new).index(a['id']),visitDuration=round(sum(mins)/2),visitGuide=g,dataLicense='https://data.gov.hk/en/terms-and-conditions' if id=='sk-bus' else 'https://opendatacommons.org/licenses/odbl/1-0/',attribution='© 香港特区政府 运输署' if id=='sk-bus' else '© OpenStreetMap contributors')
 if ps.get(id,{}).get('photo'):p['photo']=ps[id]['photo']
 ps[id]=p;guides[id]=g
 if mode:services[id]=(mode,service,url)
for args in e['sights']:add(*args)
for id,name,en,osm,file,mode,service,src in e['transport']:add(id,name,en,osm,file,src,[0,0],[service,'核对目的地方向与现场登车、登船位置'],mode,service)
add('sk-bus','西贡巴士总站','Sai Kung Bus Terminus',None,None,'bus',[0,0],['九巴 92 · 西贡 ↔ 钻石山站','抵达与离开均在总站范围，具体站位看站牌。'],'bus','九巴 92 · 西贡 ↔ 钻石山站')
for idx,a in enumerate(new):
 ids=a['placeIds'];rid='route-'+a['id'];file=rid+'-expansion.json';path=D/file
 url='https://routing.openstreetmap.de/routed-foot/route/v1/foot/'+';'.join(','.join(map(str,ps[id]['coordinates'])) for id in ids)+'?overview=full&geometries=geojson&steps=true'
 if not path.exists():
  res=subprocess.run(['curl','-fLsS','--retry','1','--max-time','40','-A','HongKongWandering-MVP-Research/0.1',url],capture_output=True,check=True);x=json.loads(res.stdout);assert x.get('code')=='Ok';path.write_bytes(res.stdout);time.sleep(1.2)
 raw=read(path);rr=raw['routes'][0];snap=max(w['distance'] for w in raw['waypoints']);print(rid,round(rr['distance']),math.ceil(rr['duration']/60),round(snap,1),[(ids[i],round(w['distance'],1)) for i,w in enumerate(raw['waypoints'])],flush=True);assert snap<=120,(rid,snap)
 prop=dict(mode='walk',routeId=rid,source='OSM / FOSSGIS OSRM foot',requestUrl=url,rawFile=file,placeIds=ids,distance=rr['distance'],duration=rr['duration'],maxSnapMeters=snap,license='https://opendatacommons.org/licenses/odbl/1-0/',attribution='© OpenStreetMap contributors / FOSSGIS OSRM')
 coords=rr['geometry']['coordinates'];area=dict(id=a['id'],nameZh=a['nameZh'],nameEn=a['nameEn'],categories=list(a['categories']),description=a['description'],duration=a['duration'],transport=a['transport'],sourceUrl=S[a['source']],verifiedAt='2026-11-02',placeIds=list(dict.fromkeys(ids)),coordinates=ps[ids[0]]['coordinates'],bounds=[min(c[0] for c in coords)-.002,min(c[1] for c in coords)-.002,max(c[0] for c in coords)+.002,max(c[1] for c in coords)+.002],boundsNote='精选步行路线及地点的浏览范围，不是行政边界。',weather='建议干燥、凉爽天气；雷雨避免海岸、河边和山径。',timeOfDay='白天出发；海滨可选傍晚，山径应在天黑前完成。',priority=11+idx,status='researched')
 r=dict(id=rid,areaId=a['id'],title=a['title'],description=a['description'],placeIds=ids,categories=list(a['categories']),categoryNotes=a['categories'],status='network-checked',verificationNote='官方景点与交通资料、OSM 坐标和 foot 路网已核对；未实地踏查，不代表当天开放或无障碍保证。',distance=round(rr['distance']),walkingMinutes=math.ceil(rr['duration']/60),maxSnapMeters=snap,visitMinutes=a['visitMinutes'],transport=a['transport'],transportSource=S[a['transportSource']],sourceUrl=S[a['source']],verifiedAt='2026-11-02',timeOfDay=area['timeOfDay'],notes=a['notes'],interests=a['interests'],preferences=a['preferences'],requestUrl=url,geometry=dict(type='FeatureCollection',features=[dict(type='Feature',properties=prop,geometry=rr['geometry'])]),transportNote=static+'只绘制镇内 / 岛上真实步行，不绘制未经核实的巴士或海上接驳轨迹。',transportNodes=[],itineraryLegs=[dict(fromIndex=i,toIndex=i+1,mode='walk',distance=round(l['distance']),minutes=math.ceil(l['duration']/60)) for i,l in enumerate(rr['legs'])])
 for i,id in enumerate(ids):
  if id not in services:continue
  mode,service,src=services[id];role='start' if i==0 else 'end' if i==len(ids)-1 else 'access'
  instruction=a['transport'] if role=='start' else '在此结束步行，核对目的地方向与当天班次后离开。' if role=='end' else '可在这里提前结束步行，改乘往北角方向渡轮；出发前核对服务和班次。'
  r['transportNodes'].append(dict(placeId=id,stopIndex=i,role=role,mode=mode,service=service,instruction=instruction,sourceUrl=src))
 areas=[x for x in areas if x['id']!=a['id']]+[area];routes=[x for x in routes if x['id']!=rid]+[r];cats[rid]=a['categories']
save(O/'areas.json',areas);save(O/'routes.json',routes);save(O/'places.geojson',dict(type='FeatureCollection',features=[dict(type='Feature',geometry=dict(type='Point',coordinates=p['coordinates']),properties=p) for p in ps.values()]));save(O/'routes.geojson',dict(type='FeatureCollection',features=[f for r in routes for f in r['geometry']['features']]))
save(R/'data/editorial/place-guides.json',guides);save(R/'data/editorial/route-categories.json',cats)
planned=read(O/'planned-areas.json');save(O/'planned-areas.json',[p for p in planned if p['nameZh'] not in {a['nameZh'] for a in new}])
print('Added five districts and routes; previous content IDs preserved.')
