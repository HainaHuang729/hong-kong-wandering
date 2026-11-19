import {useState} from 'react';
import {Camera,MapPin} from 'lucide-react';
import type {Coord,Place,PlacePhoto as Photo} from './types';
export function PhotoImage({photo,className}:{photo:Photo;className?:string}){
 const [failed,setFailed]=useState(false);
 const [loaded,setLoaded]=useState(false);
 return failed?<span className={`photo-fallback ${className??''}`}><Camera size={18}/>照片暂时无法加载</span>:<img className={`${className??''} photo-img ${loaded?'is-loaded':'is-loading'}`} src={photo.url} alt={photo.caption} loading="lazy" decoding="async" width={photo.width} height={photo.height} onLoad={()=>setLoaded(true)} onError={()=>setFailed(true)}/>;
}
export default function PlacePhoto({place,onLocate,routePosition}:{place:Place;onLocate:(coord?:Coord)=>void;routePosition?:string}){
 const photo=place.photo;
 if(!photo)return null;
 const isCameraVerified=photo.locationKind==='camera-verified'&&Array.isArray(photo.cameraCoordinates);
 const targetCoord=isCameraVerified?photo.cameraCoordinates:place.coordinates;
 return <figure className="place-photo">
  <button className="photo-locate-image" onClick={()=>onLocate(targetCoord)} aria-label={isCameraVerified?`在地图上定位${place.nameZh}的拍摄机位`:`定位照片中的${place.nameZh}`}>
   <PhotoImage key={photo.url} photo={photo}/>
   <span>{isCameraVerified?<><Camera size={14}/>在地图上看拍摄机位</>:<><MapPin size={14}/>在地图上看位置</>}</span>
  </button>
  <figcaption>
   <button className="photo-location" onClick={()=>onLocate(targetCoord)}>
    {isCameraVerified?<Camera size={15}/>:<MapPin size={15}/>}
    <strong>{place.nameZh}</strong>
    <small>{routePosition??(isCameraVerified?'已核实机位':'地图定位')}</small>
   </button>
   <p className="photo-caption">{photo.caption}</p>
   <details>
    <summary>照片来源与授权</summary>
    <p>摄影：{photo.author}</p>
    {photo.capturedAt&&<p>源站拍摄日期：{photo.capturedAt}</p>}
    {isCameraVerified&&photo.cameraCoordinates
     ?<p>已核实拍摄机位（EXIF GPS）：{photo.cameraCoordinates[1].toFixed(5)}° N · {photo.cameraCoordinates[0].toFixed(5)}° E（距代表点约 {photo.cameraDistanceMeters??0} 米）</p>
     :<p>代表点坐标：{place.coordinates[1].toFixed(5)}° N · {place.coordinates[0].toFixed(5)}° E（非拍摄机位）</p>
    }
    <a href={photo.sourceUrl} target="_blank" rel="noreferrer">Wikimedia Commons 原图 ↗</a> · <a href={photo.licenseUrl} target="_blank" rel="noreferrer">{photo.license}</a>
    <p>缩略展示，未修改原图；照片不代表实时现场。</p>
   </details>
  </figcaption>
 </figure>;
}
