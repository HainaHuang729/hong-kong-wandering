import fs from 'node:fs';
import assert from 'node:assert/strict';
const read=n=>JSON.parse(fs.readFileSync(new URL('../public/data/'+n,import.meta.url),'utf8'));
const areas=read('areas.json'),places=read('places.geojson').features.map(f=>f.properties),routes=read('routes.json');
const ids=new Set(places.map(p=>p.id));assert.equal(ids.size,places.length);assert(areas.length>=10);
function distance(a,b){const r=Math.PI/180;return 6371000*2*Math.asin(Math.sqrt(Math.sin((b[1]-a[1])*r/2)**2+Math.cos(a[1]*r)*Math.cos(b[1]*r)*Math.sin((b[0]-a[0])*r/2)**2));}
const audit=[];
function inCityBounds(c,city){return city==='sz'?c[0]>113.75&&c[0]<114.68&&c[1]>22.40&&c[1]<22.86:c[0]>113.8&&c[0]<114.45&&c[1]>22.15&&c[1]<22.6;}
for(const p of places){assert(inCityBounds(p.coordinates,p.city),p.id);assert(p.coordinateSource.startsWith('https://www.openstreetmap.org/')||p.coordinateSource.startsWith('https://data.gov.hk/'));assert(p.description&&p.sourceUrl&&p.verifiedAt);}
for(const p of places){const g=p.visitGuide;assert(g&&g.highlights.length>=2&&g.arrivalSteps.length>=2,`${p.id}: missing visit guide`);assert(g.minutes.length===2&&g.minutes[0]>=0&&g.minutes[1]>=g.minutes[0]);assert(g.transportSourceUrl.startsWith('https://')&&g.contentSourceUrl.startsWith('https://'));if(g.kind==='transport')assert.deepEqual(g.minutes,[0,0]);else assert(g.minutes[0]>0);}
for(const a of areas){assert(a.placeIds.every(id=>ids.has(id)),a.id);assert(a.bounds.length===4);assert(a.transport&&a.weather&&a.timeOfDay);}
for(const r of routes){assert(r.categories.length>0&&r.categories.every(c=>r.categoryNotes[c]),r.id+': missing route categories');assert(r.placeIds.every(id=>ids.has(id)),r.id);assert(areas.some(a=>a.id===r.areaId));if(r.status==='pending'){assert.equal(r.distance,null);continue;}
assert(r.distance>100&&r.walkingMinutes>0&&r.requestUrl.includes('/routed-foot/'));assert(r.maxSnapMeters<=120);
assert(['flat','moderate','steep'].includes(r.climbLevel),`${r.id}: invalid climbLevel`);
assert(['easy','moderate','challenging'].includes(r.effortLevel),`${r.id}: invalid effortLevel`);
assert(typeof r.climbNote==='string'&&r.climbNote.length>5,`${r.id}: missing climbNote`);
assert(Array.isArray(r.stayMinutes)&&r.stayMinutes.length===2&&r.stayMinutes[0]>0&&r.stayMinutes[1]>=r.stayMinutes[0],`${r.id}: invalid stayMinutes`);
assert(Array.isArray(r.earlyExits)&&r.earlyExits.length>=1,`${r.id}: missing earlyExits`);
for(const ee of r.earlyExits){assert.equal(r.placeIds[ee.stopIndex],ee.atPlaceId,`${r.id}: earlyExit index mismatch`);assert(ee.nameZh&&ee.exitOrStop&&ee.service&&ee.instruction&&ee.sourceUrl.startsWith('https://'),`${r.id}: invalid earlyExit`);}
let length=0,maxGap=0,count=0;
for(const f of r.geometry.features){assert.equal(f.geometry.type,'LineString');if(f.properties.mode==='bus'){const original=JSON.parse(fs.readFileSync(new URL('../data/raw/td-260-geometry.geojson',import.meta.url),'utf8')).features.find(f=>f.properties.ROUTE_ID===1526&&f.properties.ROUTE_SEQ===1);assert.deepEqual(f.geometry.coordinates,original.geometry.coordinates[f.properties.sourceGeometryPart]);assert(f.properties.license&&f.properties.attribution);continue;}assert.equal(f.properties.mode,'walk');const coords=f.geometry.coordinates;count+=coords.length;assert(coords.length>5);for(let i=1;i<coords.length;i++){const d=distance(coords[i-1],coords[i]);length+=d;maxGap=Math.max(maxGap,d);}}
assert(Math.abs(length-r.distance)/r.distance<.06,`${r.id}: distance differs`);assert(maxGap<(r.city==='sz'?600:400),`${r.id}: suspicious gap ${maxGap}`);
const walks=r.geometry.features.filter(f=>f.properties.mode==='walk');
for(const f of walks){const props=f.properties;const raw=JSON.parse(fs.readFileSync(new URL('../data/raw/'+props.rawFile,import.meta.url),'utf8'));assert.equal(raw.code,'Ok');assert.deepEqual(raw.routes[0].geometry,f.geometry);assert.equal(raw.waypoints.length,props.placeIds.length);assert(Math.max(...raw.waypoints.map(w=>w.distance))<=120);assert(Math.abs(raw.routes[0].distance-props.distance)<1);}
assert.equal(r.transportNodes[0].role,'start');assert.equal(r.transportNodes.at(-1).role,'end');assert.equal(r.transportNodes[0].placeId,r.placeIds[0]);assert.equal(r.transportNodes.at(-1).placeId,r.placeIds.at(-1));
for(const n of r.transportNodes){assert.equal(r.placeIds[n.stopIndex],n.placeId);assert.equal(places.find(p=>p.id===n.placeId).visitGuide.kind,'transport');assert(n.service&&n.exitOrStop&&n.sourceUrl.startsWith('https://'),`${r.id}: missing exitOrStop on ${n.placeId}`);}
assert.equal(r.itineraryLegs.length,r.placeIds.length-1);
for(let i=0;i<r.placeIds.length-1;i++){const leg=r.itineraryLegs.find(l=>l.fromIndex===i);assert(leg&&leg.toIndex===i+1&&leg.distance>=0);assert(leg.mode==='bus'?leg.minutes===null:leg.minutes>=0);}
for(const [id,coord] of [[r.placeIds[0],walks[0].geometry.coordinates[0]],[r.placeIds.at(-1),walks.at(-1).geometry.coordinates.at(-1)]])assert(distance(places.find(p=>p.id===id).coordinates,coord)<=120,`${r.id}: endpoint not connected`);
const raw=JSON.parse(fs.readFileSync(new URL('../data/raw/'+walks[0].properties.rawFile,import.meta.url),'utf8'));
audit.push({id:r.id,vertices:count,meters:r.distance,minutes:r.walkingMinutes,climbLevel:r.climbLevel,effortLevel:r.effortLevel,maxSegmentMeters:Math.round(maxGap),snapMeters:r.maxSnapMeters,roads:[...new Set(raw.routes[0].legs.flatMap(l=>l.steps.map(s=>s.name)).filter(Boolean))]});}
assert(routes.filter(r=>r.status==='network-checked').length>=3);
fs.writeFileSync(new URL('../docs/route-audit.json',import.meta.url),JSON.stringify(audit,null,2));
console.log(`${areas.length} areas, ${places.length} places, ${audit.length} complete routes (including official bus geometry), ${routes.length-audit.length} pending. Coordinates, exits, climb levels, references, provenance, distances, continuity, snap offsets passed.`);

const photos=places.filter(p=>p.photo);let camVerified=0;
for(const p of photos){const f=p.photo;assert(f.url.startsWith('https://thumb.wikimedia.org/')||f.url.startsWith('https://upload.wikimedia.org/'));assert(f.sourceUrl.startsWith('https://commons.wikimedia.org/'));assert(f.author&&f.caption&&f.width>0&&f.height>0);assert(f.licenseUrl.startsWith('https://creativecommons.org/'));assert(f.checkedAt);if(f.locationKind==='camera-verified'){camVerified++;assert(Array.isArray(f.cameraCoordinates)&&f.cameraCoordinates.length===2);assert(inCityBounds(f.cameraCoordinates,p.city),`${p.id}: camera coords out of city bounds`);assert(distance(p.coordinates,f.cameraCoordinates)<=350,`${p.id}: camera too far`);}}
console.log(`${photos.length} sourced photos (${camVerified} camera-verified EXIF GPS) with attribution, licenses and locations.`);
const xhs=read('xhs-spots.json');assert(Array.isArray(xhs)&&xhs.length>0,'xhs-spots.json empty');
for(const s of xhs){assert(s.id&&s.name&&['hk','sz'].includes(s.city)&&inCityBounds(s.coordinates,s.city),`invalid xhs spot ${s.id}`);}
console.log(`${xhs.length} XHS curated spots (${xhs.filter(s=>s.city==='hk').length} HK, ${xhs.filter(s=>s.city==='sz').length} SZ) passed.`);
