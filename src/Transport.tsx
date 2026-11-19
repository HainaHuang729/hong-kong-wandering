import {Bus,TrainFront,Ship,LogOut} from 'lucide-react';
import type {Place,Route,TransportNode} from './types';
export const roleLabels={start:'起点',end:'终点',transfer:'换乘',access:'中途接入'};
export function TransportIcon({mode}:{mode:TransportNode['mode']}){const Icon=mode==='bus'?Bus:mode==='metro'?TrainFront:Ship;return <Icon size={15}/>;}
export function TransportDetails({route,places,onPlace}:{route:Route;places:Place[];onPlace:(p:Place)=>void}){
 const earlyExits=route.earlyExits??[];
 return <section className="transport-details" aria-label="路线交通节点">
  <div className="transport-list">
   {route.transportNodes.map(n=>{
    const p=places.find(p=>p.id===n.placeId);
    return p&&<article key={`${n.placeId}-${n.stopIndex}-${n.role}`}>
     <button onClick={()=>onPlace(p)}>
      <span className="transport-role"><TransportIcon mode={n.mode}/>第 {n.stopIndex+1} 站 · {roleLabels[n.role]}</span>
      <strong>{p.nameZh}</strong>
      {n.exitOrStop&&<span className="transport-exit">{n.exitOrStop}</span>}
      <span className="transport-service">{n.service}</span>
     </button>
     <p>{n.instruction}</p>
     <a href={n.sourceUrl} target="_blank" rel="noreferrer">查看交通资料 ↗</a>
    </article>;
   })}
  </div>
  {earlyExits.length>0&&<div className="early-exits">
   <h3><LogOut size={14}/>沿途可提前离开 / 换乘点</h3>
   <div className="transport-list">
    {earlyExits.map(e=>{
     const stopPlace=places.find(p=>p.id===e.atPlaceId);
     return <article key={`${e.atPlaceId}-${e.stopIndex}`}>
      <button onClick={()=>stopPlace&&onPlace(stopPlace)}>
       <span className="transport-role"><TransportIcon mode={e.mode}/>第 {e.stopIndex+1} 站旁可离开</span>
       <strong>{e.nameZh}</strong>
       {e.exitOrStop&&<span className="transport-exit">{e.exitOrStop}</span>}
       <span className="transport-service">{e.service}</span>
      </button>
      <p>{e.instruction}</p>
      <a href={e.sourceUrl} target="_blank" rel="noreferrer">查看接驳资料 ↗</a>
     </article>;
    })}
   </div>
  </div>}
  <p className="footnote">{route.transportNote}</p>
 </section>;
}
