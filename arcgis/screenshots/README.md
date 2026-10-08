# ArcGIS Pro — Tauranga 3DCM LiDAR 重处理截图

数据源：LINZ New Zealand Coastal LiDAR Point Cloud（layer d3Y5Qkvcp5Q5vXf，CC BY 4.0）
研究区：Tauranga Harbour，4 片 LAZ，40,750,811 点
坐标系：NZTM2000 (EPSG:2193)，垂直基准 NZVD2016

## 截图清单

1. [01_port_wharf_classification_3d.png](01_port_wharf_classification_3d.png)
   按分类着色的码头区 3D 斜视图：红=码头仓库(类6)、棕=地面(类2)、
   深绿=树木(类3-5)、灰=水下桩基与海床(类40)、淡青=水面点(类41/42)。

2. [02_sulphur_point_vegetation_3d.png](02_sulphur_point_vegetation_3d.png)
   Sulphur Point 植被岬角 3D 视图：深绿林地 + 棕色地面 + 灰蓝海床，
   展示陆地到海床的连续过渡。

3. [03_dtm_1m.png](03_dtm_1m.png)
   第一版 DTM（Void Fill = Linear），棕=陆地高、浅黄=岸边、
   蓝=海床疏浚航道（约 -17 m NZVD2016，与 Port of Tauranga 疏浚深度吻合）。

4. [04_dtm_overlay_lidar.png](04_dtm_overlay_lidar.png)
   DTM 表面叠加原始 LiDAR 点云：可见海床点（蓝）、地面点（棕）、
   以及无点空洞（白斑）——验证栅格与点云的对应关系。

5. [05_dtm_nofill.png](05_dtm_nofill.png)
   Void Fill = None 的 DTM：浊水/缺测点保持 nodata（白色方块），
   不做三角插值补满，与正式交付口径一致。

6. [06_dsm_overlay_lidar_ve1.png](06_dsm_overlay_lidar_ve1.png)
   DSM 作为高程表面 + 原始 LiDAR 点云叠加（垂直夸张 1x）：
   可见树冠顶、地面纹理、水面点。

7. [07_dsm_only.png](07_dsm_only.png)
   单独看 DSM：棕色锯齿峰 = 树冠/建筑顶（最高 42 m），
   蓝绿平滑面 = 水面与海床。与 DTM 对比可见植被/建筑高度。

8. [08_lidar_only_no_dsm.png](08_lidar_only_no_dsm.png)
   只显示点云（无 DSM 表面）：分类着色的原始点，
   绿=植被、棕=地面、灰=海床、淡青=水面。

9. [09_wharf_dsm_only.png](09_wharf_dsm_only.png)
   码头区单独看 DSM：棕色柱 = 吊机/桩基，蓝绿色 = 水面与海床。

10. [10_wharf_dsm_overlay_lidar.png](10_wharf_dsm_overlay_lidar.png)
    码头区 DSM + 点云叠加：红=仓库(类6)、棕=地面(类2)、
    灰=水下桩基(类40海床)、绿=树木(类3-5)。

11. [11_wharf_lidar_only.png](11_wharf_lidar_only.png)
    码头区只显示点云：原始分类点，无 DSM 表面。

12. [12_rgb_1m_truecolor.png](12_rgb_1m_truecolor.png)
    真彩色栅格（Value Field = RGB）：Sulphur Point 植被/沙滩、
    Pilot Bay 岸线、码头吊机与集装箱——来自激光点自带颜色。

13. [13_intensity_1m.png](13_intensity_1m.png)
    回波强度图（Value Field = Intensity）：紫=低强度（植被/阴影），
    亮黄=高强度饱和（水面 p95=65530）。用于水陆分界与 QC 诊断。

14. [14_density_1m.png](14_density_1m.png)
    点密度图（LAS Point Statistics As Raster → Point Count，Histogram Equalize）：
    紫=低密度，黄=高密度；斜条纹=航线重叠带。实测 24.6–36.1 pts/m²，
    超 LINZ 规格（≥2 pts/m²）12–18 倍。

15. [15_hillshade.png](15_hillshade.png)
    山体阴影（Hillshade，Azimuth 315°，Altitude 45°）：灰度地形纹理，
    叠在 3D 视图上增强立体感。

16. [16_profile_graph.png](16_profile_graph.png)
    纵剖面图（Profile Graph）：从 Sulphur Point 陆地（~25m）降到水面（~0m），
    水平距离 ~450m。对应报告 fig9 双断面图。

17. [17_land_seabed_dtm.png](17_land_seabed_dtm.png)
    陆地—海床连续 DTM（NZVD2016）3D 视角：红褐=深海床、黄=过渡、绿=岸线、白=陆地。
    白色等高线=海陆分界线。**直接对应 JD 的 "seamless representation of land and sea"。**

18. [18_land_seabed_dtm_2d.png](18_land_seabed_dtm_2d.png)
    同一 DTM 的 2D 正射视图：白色岸线蜿蜒穿过数据区，
    绿=陆地、黄=潮间带、红褐=海床。

19. [19_intertidal_zone.png](19_intertidal_zone.png)
    潮间带 3D 视角（Reclassify：-1.3m 到 +0.6m NZVD2016）：蓝色条带=干湿交替区，
    绿=陆地、黄橙=海床。一阶估算（CD≈-1.3m，MHWS≈+0.6m），非 survey-grade。

20. [20_intertidal_zone_2d.png](20_intertidal_zone_2d.png)
    潮间带 2D 正射视图：蓝色条带沿河岸蜿蜒，绿=陆地、黄橙=海床。

21. [21_intertidal_closeup.png](21_intertidal_closeup.png)
    潮间带特写：蓝色干湿交替区 + 白色岸线 + 红褐海床，
    标注 Base Track 步道。

## 对应 JD 能力

- 分类着色 + 旗标过滤器 → validate EO data / 交付物标准核查
- DTM / DSM 生成 → understanding of LiDAR products
- 海陆连续表面 → seamless representation of land and sea
- NZVD2016 基准与航道深度交叉验证 → datums / tides awareness
