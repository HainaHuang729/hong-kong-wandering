# Phase 0 · 项目、来源与技术方案

审查日期：2026-11-02。

## 工作区

- `../hk-strollology-research/` 是已有资料研究，含授权梳理、书目、地点候选。路线表明确没有完整道路几何，不作为已核实路线导入。也不复制书页、影视截图或旅游网站照片。
- `../xhs/map/` 已使用 MapLibre，有地点筛选与地图工具，但不是 React 应用。本项目另建目录，避免改动已有应用和存储。
- 杭州慢游参考地图主导布局、浅深底图、缩放后的代表地标避让。采用相同原则独立实现。

## 来源与许可决策

| 来源 | 用途 | 条件 / 限制 |
| --- | --- | --- |
| [OpenFreeMap](https://openfreemap.org/) | OpenMapTiles 矢量底图 | 公开服务允许使用，无 API key；保留底图署名；无 SLA，不承诺离线 |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | 地点坐标与路网 | ODbL，署名并标许可证；本项目 OSM 衍生地理数据也以 ODbL 提供 |
| [Nominatim](https://operations.osmfoundation.org/policies/nominatim/) | 开发期间少量地点查询 | 串行、间隔 >1 秒、标 User-Agent、缓存；不做前端实时搜索，不做自动补全 |
| [FOSSGIS OSRM](https://routing.openstreetmap.de/about.html) | 少量编辑路线的 foot 几何与估时 | 最多每秒一次、不做批量抓取；缓存开发期间的少量路线请求，浏览者不再请求路由服务；署名和修正地图链接 |
| [香港旅发局](https://www.discoverhongkong.com/eng/neighbourhoods.html) | 片区、地点特色、交通线索 | 自行撰写简短事实摘要并链接原文，不复制照片、地图或整篇攻略 |
| [城巴](https://www.citybus.com.hk/) / [运输署渡轮资料](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/ferries/service_details/index_t.html) | 巴士与渡轮接驳 | 静态资料核对，不提供虚构班次、票价、实时到站或服务保证 |
| [地政总署 3D 行人道路网](https://portal.csdi.gov.hk/csdi-webpage/dataset/landsd_rcd_1637222018065_52265) | 后续提高楼梯、室内及立体路网质量 | 读取具体数据集许可后再导入；本版没有混入政府网络数据 |
| [Walkin’HK](https://usecases.csdi.geodata.gov.hk/walkinhk/?frame=tools&lang=sc) | 行人网络和步行可达分析参考 | 参考功能，不抓取产品地图或私有接口 |

参考产品只用于界面与内容组织研究，不将其内容当开放数据。Neihou 的徒步体验、Anitabi 的作品—地点关联可参考，但本版不复制它们的线路、数据库和图片。

## 架构

React + TypeScript + Vite；MapLibre GL JS；本地 CSS tokens。所有内容来自静态 JSON / GeoJSON。地点与几何各有来源；浏览器搜索本地数据。OSM 地点保留对象 URL、查询原始响应、核对日期和代表点性质。

路线由 foot profile 生成，保留完整折线及原始响应；道路距离和模型步行时间来自路由结果，游玩时长是编辑建议，不是交通承诺。网络可达不等于实地踏查：不宣称无台阶、无施工或全天开放。未知交通几何保留缺口，不画连接直线，也不让不完整路线进入推荐。

推荐是可解释的本地规则：时间上限、兴趣匹配、已审核属性、出发点直线接近程度。直线距离不冒充交通耗时。定位只在点击后请求，不保存定位。

记录采用版本化 localStorage key，收藏与完成日期持久化；读写失败提示用户。文化故事保留 verified / unverified 状态及来源字段。

## 视觉方案

海蓝 `#176879`、浅海 `#b9dce3`、山绿 `#61816b`、暖白 `#fffef8`、电车红 `#b64a3c`、墨色 `#223b3d`。正文系统中文无衬线，品牌用宋体作小幅点缀。地图全屏；左上搜索，右上主题与收藏，底部六类筛选；桌面窄侧板、手机底部详情。标记稳定排序、像素避让，选中点保持可见。

## 交付门槛

构建和数据完整性检查；桌面与手机实测地图资源、选点、路线、收藏、记录、刷新恢复。未实测与待核实内容必须在 README 和界面中如实列出。仅本地开发，禁止自动发布。


## 实施后确认

已使用运输署 Bus Route 的公开 FeatureServer 补齐浅水湾—赤柱，最终为 11 条路线。OSM 步行与政府巴士数据分来源保存及署名；政府 3D 行人道路网仍未导入。11 个片区有内容，另 13 个片区仅作为规划。来源、许可及补充核实细节见 SOURCES.md。
