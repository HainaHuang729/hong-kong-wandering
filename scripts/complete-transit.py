"""Assemble the researched 260 transfer using unchanged official road segments.
Inputs are the cached TD stop snapshot and CSDI route geometry. No POI chord is generated.
"""
import json,pathlib,time,urllib.request,math
R=pathlib.Path(__file__).resolve().parents[1];out=R/'public/data';raw=R/'data/raw'
places=json.loads((out/'places.geojson').read_text());areas=json.loads((out/'areas.json').read_text());routes=json.loads((out/'routes.json').read_text());p={f['properties']['id']:f['properties'] for f in places['features']}
source='https://data.gov.hk/en-data/dataset/hk-td-tis_23-routes-fares-geojson'
shapeSource='https://portal.csdi.gov.hk/csdi-webpage/dataset/td_rcd_1638844988873_41214'
license='https://data.gov.hk/en/terms-and-conditions'
stops=[f for f in json.loads((raw/'td-260.json').read_text()) if f['properties']['routeId']==1526 and f['properties']['routeSeq']==1]
for id,seq,name in [('repulse-bus',11,'浅水湾泳滩站（往赤柱）'),('stanley-bus',22,'赤柱村站（赤柱村道）')]:
 f=next(f for f in stops if f['properties']['stopSeq']==seq);props=f['properties'];coords=f['geometry']['coordinates']
 obj={'id':id,'nameZh':name,'nameEn':props['stopNameE'],'coordinates':coords,'district':'repulse','categories':['山海之间'],'description':('在浅水湾道此站乘城巴 260 往赤柱；请核对车头目的地。' if seq==11 else '在赤柱村道此站下车，再步行往赤柱市场与美利楼。'),'sourceUrl':source,'coordinateSource':source,'coordinateKind':'运输署巴士站点坐标；静态资料，请现场核对站牌','verifiedAt':'2026-11-02','priority':5,'visitDuration':0,'sourceStopId':props['stopId'],'sourceRouteId':1526,'sourceRouteSeq':1,'sourceStopSeq':seq,'dataLicense':license,'attribution':'© 香港特别行政区政府 运输署 / DATA.GOV.HK'}
 p[id]=obj
features=[];distance=0;duration=0;snap=0
for label,ids in [('repulse-access',['repulse-beach','repulse-bus']),('stanley-access',['stanley-bus','stanley-market','murray'])]:
 coords=';'.join(','.join(map(str,p[id]['coordinates'])) for id in ids)
 url=f'https://routing.openstreetmap.de/routed-foot/route/v1/foot/{coords}?overview=full&geometries=geojson&steps=true';path=raw/('route-'+label+'.json')
 if path.exists():res=json.loads(path.read_text())
 else:
  time.sleep(1.2);req=urllib.request.Request(url,headers={'User-Agent':'HongKongWandering-MVP-Research/0.1'});res=json.load(urllib.request.urlopen(req,timeout=30));path.write_text(json.dumps(res,ensure_ascii=False,indent=2))
 r=res['routes'][0];distance+=r['distance'];duration+=r['duration'];snap=max(snap,*[w['distance'] for w in res['waypoints']]);assert snap<80
 features.append({'type':'Feature','geometry':r['geometry'],'properties':{'mode':'walk','routeId':'route-repulse','source':'OSM / FOSSGIS OSRM foot','requestUrl':url,'rawFile':path.name,'distance':r['distance'],'duration':r['duration'],'license':'https://opendatacommons.org/licenses/odbl/1-0/'}})
 print(label,r['distance'],r['duration'],res['waypoints'],flush=True)
shape=next(f for f in json.loads((raw/'td-260-geometry.geojson').read_text())['features'] if f['properties']['ROUTE_ID']==1526 and f['properties']['ROUTE_SEQ']==1)
# The reviewed source line members 11..21 cover stops 11 to 22.
lines=shape['geometry']['coordinates'][11:22]
def dist(a,b):
 rad=math.pi/180;return 6371000*2*math.asin(math.sqrt(math.sin((b[1]-a[1])*rad/2)**2+math.cos(a[1]*rad)*math.cos(b[1]*rad)*math.sin((b[0]-a[0])*rad/2)**2))
for a,b in zip(lines,lines[1:]):assert dist(a[-1],b[0])<1
assert dist(lines[0][0],p['repulse-bus']['coordinates'])<15
assert dist(lines[-1][-1],p['stanley-bus']['coordinates'])<15
bus=[]
for i,line in enumerate(lines,11):bus.append({'type':'Feature','geometry':{'type':'LineString','coordinates':line},'properties':{'mode':'bus','routeId':'route-repulse','service':'城巴 260 往赤柱','source':shapeSource,'sourceRouteId':1526,'sourceRouteSeq':1,'sourceGeometryPart':i,'license':license,'attribution':'© 香港特别行政区政府 运输署 / DATA.GOV.HK','verifiedAt':'2026-11-02'}})
r=next(r for r in routes if r['areaId']=='repulse');r.update({'status':'network-checked','placeIds':['repulse-beach','repulse-bus','stanley-bus','stanley-market','murray'],'distance':round(distance),'walkingMinutes':math.ceil(duration/60),'maxSnapMeters':round(snap,1),'geometry':{'type':'FeatureCollection','features':[features[0],*bus,features[1]]},'busDistance':round(sum(dist(l[i-1],l[i]) for l in lines for i in range(1,len(l)))),'verificationNote':'步行段来自 OSM foot 路网；巴士段直接采用运输署公开线路 1526 / 方向 1 的道路几何成员 11–21，已核对第 11 站至第 22 站的方向和站点。浅水湾沙滩代表点距步行起点约 53 米，路线从岸边路网开始。非实地踏查；道路中心线与站点有约 10 米偏移，不代表精确上下车位置。','transport':'浅水湾泳滩散步后，步行至浅水湾道「浅水湾泳滩」站，乘城巴 260 往赤柱，在「赤柱村，赤柱村道」站下车，继续步行到市场及美利楼。不是全程步行；班次与改道请查城巴。','transportSource':'https://mobile.citybus.com.hk/nwp3/?f=1&ds=260&dsmode=1&l=1','notes':'巴士时间、候车时间与票价未纳入估算。浅水湾上车点请确认往赤柱方向，按现场指示过街。海滨与寺庙开放情况请另查当天公告。','requestUrl':features[0]['properties']['requestUrl'],'preferences':['公共交通方便','不太累'],'dataSources':[source,shapeSource,'https://routing.openstreetmap.de/about.html']})
a=next(a for a in areas if a['id']=='repulse');a['transport']=r['transport'];a['placeIds']=r['placeIds']
(out/'places.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'Point','coordinates':v['coordinates']},'properties':v} for v in p.values()]},ensure_ascii=False,indent=2))
(out/'areas.json').write_text(json.dumps(areas,ensure_ascii=False,indent=2));(out/'routes.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
(out/'routes.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[f for r in routes for f in r['geometry']['features']]},ensure_ascii=False,indent=2));(out/'transit.geojson').write_text(json.dumps({'type':'FeatureCollection','features':bus},ensure_ascii=False,indent=2))
print('COMPLETE',r['distance'],r['walkingMinutes'],r['busDistance'],flush=True)
