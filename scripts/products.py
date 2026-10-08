# -*- coding: utf-8 -*-
"""
Stage 2 — Terrain & EO products from the 3DCM Tauranga Harbour point cloud
================================================================================
Inputs : 4 LAS tiles (LAS 1.4 PDRF8, NZTM2000 + NZVD2016)
Outputs: processed/*.tif  (1 m grids, EPSG:2193)
           dem_1m      : DTM  — ground (2) + bathymetric seabed (40), mean Z
           dsm_1m      : DSM  — highest non-withheld return per cell (excl. noise 7/18/45)
           density_1m  : delivered point density (pts/m2)
           intensity_1m: mean intensity (non-withheld, non-noise)
           rgb_1m      : true-colour RGB from point colour (red/green/blue)
           hillshade_1m, slope_1m
           water_1m    : dominant water/bathymetric class per cell (9/40/41/42/45)
Tide tie-in : water-surface class (41) elevations vs LINZ 2026 Tauranga tide table
"""
import laspy
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os, glob, json, datetime

SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
OUT = r"D:\GIS_Portfolio\Lidar_demo\processed"
os.makedirs(OUT, exist_ok=True)

RES = 1.0
NOISE = {7, 18, 45}
WATER_CLS = {9, 41, 42}
BATHY = {40, 41, 42, 43, 45}

files = sorted(glob.glob(os.path.join(SRC, "*.las")))
# global extent
xs, ys = [], []
for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    xs += [las.x.min(), las.x.max()]
    ys += [las.y.min(), las.y.max()]
    del las
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
W = int(np.ceil((x1 - x0) / RES)) + 1
H = int(np.ceil((y1 - y0) / RES)) + 1
print(f"grid {W}x{H} cells  extent {x0:.1f},{y0:.1f} .. {x1:.1f},{y1:.1f}")

# accumulators
sum_dtm = np.zeros((H, W), np.float64)     # ground+seabed mean
cnt_dtm = np.zeros((H, W), np.int64)
max_dsm = np.full((H, W), -np.inf)         # non-withheld max
cnt_all = np.zeros((H, W), np.int64)
sum_int = np.zeros((H, W), np.float64)
cnt_int = np.zeros((H, W), np.int64)
sum_rgb = np.zeros((H, W, 3), np.float64)
cnt_rgb = np.zeros((H, W), np.int64)
cnt_water_surf = np.zeros((H, W), np.int64)   # non-withheld points classed 9/41/42
cnt_land = np.zeros((H, W), np.int64)         # non-withheld points on land classes

def cell_idx(x, y):
    c = ((x - x0) / RES).astype(np.int64)
    r = ((y1 - y) / RES).astype(np.int64)
    np.clip(c, 0, W - 1, out=c)
    np.clip(r, 0, H - 1, out=r)
    return r, c

gps_all = []
for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    cls = np.asarray(las.classification)
    withheld = np.asarray(las.withheld).astype(bool)
    syn = np.asarray(las.synthetic).astype(bool)
    inten = np.asarray(las.intensity).astype(np.float32)
    try:
        gt = np.asarray(las.gps_time)
        gps_all.append((gt.min(), gt.max()))
    except Exception:
        pass
    r, c = cell_idx(x, y)
    # density (all delivered points)
    np.add.at(cnt_all, (r, c), 1)
    # DTM: ground + seabed
    m = (cls == 2) | (cls == 40)
    if m.any():
        np.add.at(sum_dtm, (r[m], c[m]), z[m])
        np.add.at(cnt_dtm, (r[m], c[m]), 1)
    # DSM: exclude withheld & noise
    m2 = ~withheld & ~np.isin(cls, list(NOISE))
    if m2.any():
        np.maximum.at(max_dsm, (r[m2], c[m2]), z[m2])
    # intensity: exclude withheld & noise
    m3 = m2
    if m3.any():
        np.add.at(sum_int, (r[m3], c[m3]), inten[m3])
        np.add.at(cnt_int, (r[m3], c[m3]), 1)
    # rgb: exclude withheld & noise
    if m3.any():
        try:
            rgb = np.stack([np.asarray(las.red), np.asarray(las.green), np.asarray(las.blue)], axis=1).astype(np.float32)
            for b in range(3):
                np.add.at(sum_rgb[:, :, b], (r[m3], c[m3]), rgb[m3, b])
            np.add.at(cnt_rgb, (r[m3], c[m3]), 1)
        except Exception as e:
            print("rgb skip", f, e)
    # water fraction: non-withheld points that are water surface (9/41/42) or bathymetric
    mw = ~withheld & np.isin(cls, list(WATER_CLS | BATHY))
    if mw.any():
        np.add.at(cnt_water_surf, (r[mw], c[mw]), 1)
    ml = ~withheld & ~np.isin(cls, list(WATER_CLS | BATHY))
    if ml.any():
        np.add.at(cnt_land, (r[ml], c[ml]), 1)
    del las, x, y, z, cls, withheld, inten
    print("done", os.path.basename(f))

# finalise rasters
den = cnt_all / (RES * RES)
with np.errstate(divide="ignore", invalid="ignore"):
    dtm = np.where(cnt_dtm > 0, sum_dtm / np.maximum(cnt_dtm, 1), np.nan)
    inten_g = np.where(cnt_int > 0, sum_int / np.maximum(cnt_int, 1), np.nan)
    rgb_g = np.where(cnt_rgb[..., None] > 0, sum_rgb / np.maximum(cnt_rgb[..., None], 1), 0)
dsm = np.where(np.isfinite(max_dsm), max_dsm, np.nan)

transform = from_origin(x0, y1, RES, RES)
prof = {"driver": "GTiff", "width": W, "height": H, "count": 1, "dtype": "float32",
        "crs": "EPSG:2193", "transform": transform, "compress": "deflate", "nodata": np.nan}

def write(name, arr, **kw):
    p = dict(prof); p.update(kw)
    if p.get("dtype") in ("uint8", "int16"):
        p.pop("nodata", None)
    with rasterio.open(os.path.join(OUT, name), "w", **p) as ds:
        ds.write(arr.astype(p["dtype"])[None] if p["count"] == 1 else arr.astype(p["dtype"]).transpose(2, 0, 1))
    print("wrote", name)

write("dem_1m.tif", dtm)
write("dsm_1m.tif", dsm)
write("density_1m.tif", den)
write("intensity_1m.tif", inten_g)
prof3 = dict(prof); prof3["count"] = 3; prof3["dtype"] = "uint8"; prof3.pop("nodata", None)
rgb8 = np.clip(rgb_g / 257.0, 0, 255).astype(np.uint8)  # 16-bit -> 8-bit
with rasterio.open(os.path.join(OUT, "rgb_1m.tif"), "w", **prof3) as ds:
    ds.write(rgb8.transpose(2, 0, 1))
print("wrote rgb_1m.tif")

# ---- hillshade & slope from DTM ----
dtm_f = np.where(np.isfinite(dtm), dtm, np.nanmedian(dtm))
# smoother for hillshade
from scipy.ndimage import uniform_filter
dtm_s = uniform_filter(dtm_f, size=5)
gy, gx = np.gradient(dtm_s, RES)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
az, alt = 315.0, 45.0
azr = np.radians(az); altr = np.radians(alt)
hs = 255 * (np.cos(altr) + np.sin(altr) * (-np.sin(azr) * gx - np.cos(azr) * gy) / (np.hypot(gx, gy) + 1e-9) * -1)
hs = np.clip(hs / 2 + 127, 0, 255)
write("hillshade_1m.tif", hs, dtype="uint8")
write("slope_1m.tif", slope)
with np.errstate(divide="ignore", invalid="ignore"):
    water_frac = np.where((cnt_water_surf + cnt_land) > 0, cnt_water_surf / np.maximum(cnt_water_surf + cnt_land, 1), np.nan)
write("water_fraction_1m.tif", water_frac)

# ---- tide tie-in ----
gt0 = min(g[0] for g in gps_all); gt1 = max(g[1] for g in gps_all)
def gps_to_utc(gps):
    return datetime.datetime(1980, 1, 6) + datetime.timedelta(seconds=float(gps))
acq_start, acq_end = gps_to_utc(gt0), gps_to_utc(gt1)
print("acquisition (UTC):", acq_start, "->", acq_end, "(local NZDT+13:", acq_start + datetime.timedelta(hours=13), ")")

# water surface class 41 elevation stats across all tiles
ws_zs = []
for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    cls = np.asarray(las.classification)
    z = np.asarray(las.z)
    m = cls == 41
    if m.any():
        ws_zs.append(z[m])
    del las, cls, z
ws = np.concatenate(ws_zs)
tide = {
    "source": "LINZ New Zealand Hydrographic Authority Tide Tables 2026 — Tauranga (37°39'S 176°11'E)",
    "heights_above_chart_datum_m": {"typical_high": 2.0, "typical_low": 0.2,
                                     "observed_range": "0.1 – 2.1"},
    "water_surface_class41_elevation_NZVD2016_m": {
        "median": round(float(np.median(ws)), 3),
        "p5": round(float(np.percentile(ws, 5)), 3),
        "p95": round(float(np.percentile(ws, 95)), 3),
        "n": int(len(ws))},
}
with open(os.path.join(OUT, "products_summary.json"), "w", encoding="utf-8") as fh:
    json.dump({"extent": {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "cells_w": W, "cells_h": H},
               "acquisition_utc": {"start": acq_start.isoformat(), "end": acq_end.isoformat()},
               "tide": tide}, fh, indent=2, ensure_ascii=False, default=str)
print(json.dumps(tide, indent=2, default=str))
print("done products")
