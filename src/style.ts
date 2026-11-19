import type {StyleSpecification} from 'maplibre-gl';
export function mapStyle(dark:boolean):StyleSpecification {
const c=dark?{land:'#203538',wood:'#294b42',park:'#315749',water:'#183f50',building:'#365055',road:'#647575',edge:'#354e53',text:'#b8cace'}:{land:'#f3f2e9',wood:'#d1dfc9',park:'#bdd3b7',water:'#b9dce3',building:'#dfdfd4',road:'#fffef9',edge:'#d5d6c8',text:'#607b7d'};
const source='basemap';
return {version:8,name:'港深生活指南',glyphs:'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',sources:{[source]:{type:'vector',url:'https://tiles.openfreemap.org/planet',attribution:'<a href="https://openfreemap.org">OpenFreeMap</a> · <a href="https://openmaptiles.org">OpenMapTiles</a> · © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}},layers:[
{id:'land',type:'background',paint:{'background-color':c.land}},
{id:'green',type:'fill',source,'source-layer':'landcover',filter:['match',['get','class'],['wood','grass','scrub'],true,false],paint:{'fill-color':c.wood}},
{id:'park',type:'fill',source,'source-layer':'park',paint:{'fill-color':c.park,'fill-opacity':.65}},
{id:'water',type:'fill',source,'source-layer':'water',paint:{'fill-color':c.water}},
{id:'waterways',type:'line',source,'source-layer':'waterway',paint:{'line-color':c.water,'line-width':2}},
{id:'buildings',type:'fill',source,'source-layer':'building',minzoom:13,paint:{'fill-color':c.building,'fill-opacity':.8}},
{id:'road-edge',type:'line',source,'source-layer':'transportation',filter:['match',['get','class'],['rail','ferry'],false,true],paint:{'line-color':c.edge,'line-width':['interpolate',['linear'],['zoom'],10,.6,15,3,19,14]}},
{id:'roads',type:'line',source,'source-layer':'transportation',filter:['match',['get','class'],['rail','ferry'],false,true],paint:{'line-color':c.road,'line-width':['interpolate',['linear'],['zoom'],10,.3,15,2,19,10]}},
{id:'paths',type:'line',source,'source-layer':'transportation',filter:['==',['get','class'],'path'],minzoom:14,paint:{'line-color':c.text,'line-opacity':.4,'line-width':1,'line-dasharray':[2,2]}},
{id:'road-labels',type:'symbol',source,'source-layer':'transportation_name',minzoom:14,filter:['match',['get','class'],['motorway','trunk','primary','secondary','tertiary','minor','service','path'],true,false],layout:{'symbol-placement':'line','symbol-spacing':350,'text-field':['coalesce',['get','name:zh'],['get','name']],'text-font':['Noto Sans Regular'],'text-size':11},paint:{'text-color':c.text,'text-halo-color':c.land,'text-halo-width':2}},
{id:'region-labels',type:'symbol',source,'source-layer':'place',maxzoom:13,filter:['match',['get','class'],['suburb','town','village','city'],true,false],layout:{'text-field':['coalesce',['get','name:zh'],['get','name']],'text-font':['Noto Sans Regular'],'text-size':12,'text-padding':45},paint:{'text-color':c.text,'text-halo-color':c.land,'text-halo-width':2}}
]};}
