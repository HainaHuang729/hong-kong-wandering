# 五片区扩展 · 2026-11-02

新增西贡、沙田—城门河、观塘海滨、坪洲、梅窝；当前共 16 片区、59 地点（34 游览点 / 25 交通节点）、16 路线。余下 8 片区仍为规划。原有地点、路线 ID 与记录键保留。

| 路线 | 实际路网米数 | 模型步行分钟 | 最大吸附偏移米 |
| --- | --- | --- | --- |
| 西贡旧墟与海滨 | 1088 | 15 | 12.5 |
| 沙田公园到城门河两岸 | 1601 | 22 | 13.1 |
| 观塘海滨 | 2471 | 33 | 16.1 |
| 坪洲庙前小街与手指山 | 2044 | 28 | 8.3 |
| 梅窝银矿湾与瀑布花园 | 4068 | 55 | 19.1 |

步行时间不含停留、候车船、站内通道、过街等待，坡度与个人体力也会影响实际用时。游玩时间是编辑建议：沙田约 2 小时，其余半天，不含往返交通。

## 来源与边界

- Nominatim 原始查询保留于 data/raw，按名称、对象类型与地理位置核对，排除同名地区和巴士站。港铁为 railway/station 代表点；坪洲、梅窝为渡轮客运点，不保证具体站口。
- 西贡巴士总站使用运输署 ROUTE_ID 1399（九巴 92），方向 1 首站与方向 2 末站同址；原始节选为 `td-saikung-endpoints.geojson`。
- `route-*-expansion.json` 保留 FOSSGIS OSRM foot 的完整几何、逐段 legs、模型时间与吸附距离。未以直线连点；ODbL 与政府数据许可分别保留。
- 沙田通过沥源桥连接城门河两岸。观塘包含励业街、海滨道、开源道等接入道路，不是全程海滨；观塘码头为可选提前离开点。
- 坪洲手指山、梅窝瀑布段有坡道，不加入「少爬坡」「雨天可玩」标签；不进入矿洞。海上航迹、巴士接驳轨迹、实时船班均不虚构。
- 新增 9 张照片均核对实际画面，保留作者、授权与年代，定位为景点代表点，不冒充拍摄机位。照片不代表当前现场。
- 可下载官方网页缓存于 `data/raw/expansion-sources/`；旅发局两个页面经网页检索读取，直接下载失败。原始 URL 见同目录 sources.json。

## 验收

数据检查、推荐规则检查与生产构建通过。浏览器逐条验证五片区的搜索 → 片区 → 路线，均显示四个行程节点；观塘地图显示港铁起终点与渡轮中途接入点。新照片逐张目视检查。未实地踏查，不保证当天开放或无障碍通行。

截图：`output/playwright/expansion-muiwo.png`。构建仅有既有 MapLibre 包体积提示。

## 内容与交通来源

- [mtr](https://www.mtr.com.hk/en/customer/services/system_map.html)
- [sk](https://www.discoverhongkong.com/eng/neighbourhoods/sai-kung/a-scenic-and-satiating-day-in-sai-kung.html)
- [skt](https://www.discoverhongkong.com/eng/place-to-go/travel.guide-tin-hau-temple-at-sai-kung-town.html)
- [bus](https://search.kmb.hk/KMBWebSite/?action=routesearch&route=92&lang=en)
- [st](https://www.lcsd.gov.hk/en/parks/stp/index.html)
- [staccess](https://www.lcsd.gov.hk/en/fitnesswalking/)
- [kt](https://www.lcsd.gov.hk/en/parks/ktp/index.html)
- [ktaccess](https://www.kwuntong.org.hk/en/c3_1.html)
- [pc](https://www.islands.gov.hk/en/routes-peng-chau.php)
- [pct](https://www.islands.gov.hk/en/explores-peng-chau-tin-hau-temple.php)
- [pch](https://www.islands.gov.hk/en/explores-peng-chau-finger-hill.php)
- [mw](https://www.islands.gov.hk/en/explores-mui-wo.php)
- [falls](https://www.gohk.gov.hk/en/spots/spot_detail.php?spot=Silvermine+Cave+and+Silvermine+Waterfalls)
- [ferry](https://www.td.gov.hk/en/transport_in_hong_kong/public_transport/ferries/service_details/index.html)
