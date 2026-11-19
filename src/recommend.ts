import type {Area,Coord,Route} from './types';
export const interests=['看海','逛小店','看天际线','散步','看建筑','逛老街','坐船','轻徒步','看日落','文化探索'];
export const preferences=['少爬坡','公共交通方便','不太累','适合独自出行','雨天可玩'];
export const climbLabels={flat:'平缓少坡',moderate:'局部坡阶',steep:'爬坡较多'} as const;
export const effortLabels={easy:'轻松慢走',moderate:'适中步量',challenging:'体力消耗较大'} as const;
export function distanceKm(a:Coord,b:Coord){const r=Math.PI/180,dlat=(b[1]-a[1])*r,dlon=(b[0]-a[0])*r;return 6371*2*Math.asin(Math.sqrt(Math.sin(dlat/2)**2+Math.cos(a[1]*r)*Math.cos(b[1]*r)*Math.sin(dlon/2)**2));}
export function recommend(routes:Route[],areas:Area[],minutes:number,wants:string[],prefs:string[],origin?:Coord,originId?:string){
 const preferEasy=prefs.includes('少爬坡')||prefs.includes('不太累');
 return routes
  .filter(r=>r.status==='network-checked'&&r.visitMinutes<=minutes&&prefs.every(p=>r.preferences.includes(p)))
  .map(r=>{
   const a=areas.find(a=>a.id===r.areaId)!;
   const matches=wants.filter(w=>r.interests.includes(w));
   const proximity=origin?distanceKm(origin,a.coordinates):null;
   const directHit=!!originId&&(r.areaId===originId||r.placeIds.includes(originId));
   const timeComfort=r.visitMinutes<minutes?2:0.5;
   const climbBonus=preferEasy?(r.climbLevel==='flat'?5:0)+(r.effortLevel==='easy'?4:0):(r.climbLevel==='flat'?1.5:r.climbLevel==='steep'?-1:0);
   const score=matches.length*10+(proximity===null?0:Math.max(0,10-proximity/3))+(directHit?15:0)+timeComfort+climbBonus;
   const distLabel=((r.distance??0)/1000).toFixed(1);
   const walkMin=r.walkingMinutes??0;
   const originText=directHit?'可从所选位置起步 · ':proximity!==null?`起点距约 ${proximity.toFixed(1)} 公里 · `:'';
   return {
    route:r,
    score,
    reason:`${originText}${matches.length?'适合'+matches.join('、')+' · ':''}步行约 ${distLabel} 公里（约 ${walkMin} 分钟）`
   };
  })
  .filter(x=>!wants.length||wants.some(w=>x.route.interests.includes(w)))
  .sort((a,b)=>b.score-a.score)
  .slice(0,6);
}
