import assert from 'node:assert/strict';
import fs from 'node:fs';
import {recommend,distanceKm} from '../src/recommend.ts';
const read=n=>JSON.parse(fs.readFileSync(new URL('../public/data/'+n,import.meta.url),'utf8'));
const routes=read('routes.json'),areas=read('areas.json');
for(const time of [120,300,600]) for(const interests of [[],['看海'],['看建筑'],['坐船']]){
 const results=recommend(routes,areas,time,interests,[]);
 assert(results.every(x=>x.route.status==='network-checked'&&x.route.visitMinutes<=time));
 assert(results.every(x=>interests.length===0||interests.some(i=>x.route.interests.includes(i))));
 assert(results.every(x=>x.reason.includes('步行约')));
}
assert.equal(recommend(routes,areas,600,[],['雨天可玩']).length,0);
const flatResults=recommend(routes,areas,600,[],['少爬坡']);
assert(flatResults.length>0&&flatResults.every(x=>x.route.climbLevel==='flat'));
const easyResults=recommend(routes,areas,600,[],['不太累']);
assert(easyResults.length>0&&easyResults.every(x=>x.route.effortLevel==='easy'));
assert(distanceKm([114.1,22.3],[114.1,22.3])===0);
const origin=areas.find(a=>a.id==='cheungchau').coordinates;
assert(recommend(routes,areas,600,['坐船'],[],origin)[0].route.areaId==='cheungchau');
const wkOrigin=areas.find(a=>a.id==='westkowloon').coordinates;
assert(recommend(routes,areas,600,[],[],wkOrigin,'wk-mplus')[0].route.id==='route-westkowloon');
console.log('Recommendation eligibility, time limits, interest matching, climb/effort preference filtering, distance and origin ranking passed.');

const pending={...routes[0],id:'pending-test',status:'pending',visitMinutes:1};assert(!recommend([pending],areas,600,[],[]).length);
