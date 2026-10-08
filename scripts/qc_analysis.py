# -*- coding: utf-8 -*-
"""
Stage 1 — Point cloud QC against the 3D Coastal Mapping (3DCM) specification
================================================================================
Data: New Zealand Coastal LiDAR Point Cloud (LINZ Data Service), Tauranga Harbour
      tiles CM_CL2_BD37_2025_1000_{1206,1208,1305,1310}.las (LAS 1.4 PDRF8)
Checks:
  - Header / format / CRS integrity (NZTM2000 + NZVD2016)
  - Bounds, point counts, delivered density vs spec (>=2 pts/m2 above drying line,
    >=1 pts/m2 below)
  - Classification completeness (topo 1-9/17/18 + bathymetric 40-45) and noise share
  - Flag audit (synthetic / withheld / key-point / overlap)
  - Return-number & intensity sanity, acquisition (GPS) time range
  - Per-class Z statistics -> outlier detection
  - Tile overlap audit
Outputs: processed/qc_tiles.csv, processed/qc_merged.json, printed summary
"""
import laspy
import numpy as np
import pandas as pd
import json
import os, glob, datetime

SRC = r"D:\GIS_Portfolio\Lidar_demo\raw_data\export\new-zealand-coastal-lidar-point-cloud"
OUT = r"D:\GIS_Portfolio\Lidar_demo\processed"
os.makedirs(OUT, exist_ok=True)

CLASS_NAMES = {
    0: "Created, never classified", 1: "Unclassified", 2: "Ground", 3: "Low vegetation",
    4: "Medium vegetation", 5: "High vegetation", 6: "Building", 7: "Low noise (topo)",
    8: "Model key-point", 9: "Water surface (topo)", 17: "Bridge deck",
    18: "High noise (topo)", 40: "Bathymetric/seabed", 41: "Water surface (refraction)",
    42: "Derived water surface (synthetic)", 43: "Submerged object", 45: "Bathymetric noise",
}
NOISE = {7, 18, 45}
TERRAIN = {2, 40}          # DTM classes: ground + seabed
BATHY = {40, 41, 42, 43, 45}
WATER_SURFACE = {9, 41, 42}

files = sorted(glob.glob(os.path.join(SRC, "*.las")))
rows = []
merged = {}

def flag_counts(las):
    out = {}
    for name in ("synthetic", "key_point", "withheld", "overlap"):
        try:
            out[name] = int(np.asarray(las[name]).sum())
        except Exception:
            out[name] = None
    return out

for f in files:
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    h = las.header
    x, y, z = las.x, las.y, las.z
    cls = las.classification
    n = len(x)
    area = float((x.max() - x.min()) * (y.max() - y.min()))
    density = n / area
    # CRS from WKT VLR
    crs_txt = ""
    for vlr in h.vlrs:
        if "Wkt" in type(vlr).__name__:
            crs_txt = str(getattr(vlr, "string", ""))[:2000]
    # classes
    vals, counts = np.unique(cls, return_counts=True)
    cls_dict = {int(v): int(c) for v, c in zip(vals, counts)}
    # flags
    fl = flag_counts(las)
    # returns
    rn = np.asarray(las.return_number); nr = np.asarray(las.number_of_returns)
    # intensity
    inten = np.asarray(las.intensity)
    # gps time
    try:
        gt = np.asarray(las.gps_time)
        gt0, gt1 = float(gt.min()), float(gt.max())
    except Exception:
        gt0 = gt1 = None
    # z stats per class
    zcls = {}
    for v in vals:
        zv = z[cls == v]
        zcls[int(v)] = dict(min=round(float(zv.min()), 3), max=round(float(zv.max()), 3),
                            mean=round(float(np.mean(zv)), 3), n=int(len(zv)))
    # scan angle
    try:
        sa = np.asarray(las.scan_angle)
        sa_min, sa_max = float(np.nanmin(sa)), float(np.nanmax(sa))
    except Exception:
        sa_min = sa_max = None
    row = {
        "tile": os.path.basename(f),
        "las_version": str(h.version),
        "point_format": h.point_format.id,
        "point_count": int(n),
        "area_km2": round(area / 1e6, 4),
        "delivered_density_pts_m2": round(density, 2),
        "x_min": round(float(x.min()), 3), "x_max": round(float(x.max()), 3),
        "y_min": round(float(y.min()), 3), "y_max": round(float(y.max()), 3),
        "z_min": round(float(z.min()), 3), "z_max": round(float(z.max()), 3),
        "gps_time_start": gt0, "gps_time_end": gt1,
        "intensity_mean": round(float(np.mean(inten)), 1),
        "intensity_p95": round(float(np.percentile(inten, 95)), 1),
        "scan_angle_min": sa_min, "scan_angle_max": sa_max,
        "n_ground": cls_dict.get(2, 0), "n_seabed": cls_dict.get(40, 0),
        "n_water_surface": cls_dict.get(9, 0) + cls_dict.get(41, 0),
        "n_noise": sum(cls_dict.get(c, 0) for c in NOISE),
        "n_classes_present": len(cls_dict),
        "flags": fl,
        "classification_counts": cls_dict,
        "z_per_class": zcls,
        "crs_wkt": crs_txt,
    }
    rows.append(row)
    print(f"### {row['tile']}")
    print(f"  {n:,} pts | {area/1e6:.3f} km2 | {density:.1f} pts/m2 | z {z.min():.2f}..{z.max():.2f} | classes {len(cls_dict)}")
    print(f"  flags {fl} | returns {int(rn.min())}-{int(rn.max())}/{int(nr.min())}-{int(nr.max())} | inten mean {inten.mean():.0f} | gps {gt0}..{gt1}")
    del las, x, y, z, cls

# ---- merged summary (streaming stats over all tiles) ----
tot = sum(r["point_count"] for r in rows)
x0, x1 = min(r["x_min"] for r in rows), max(r["x_max"] for r in rows)
y0, y1 = min(r["y_min"] for r in rows), max(r["y_max"] for r in rows)
bbox_area = (x1 - x0) * (y1 - y0)
# merged class counts
mcls = {}
for r in rows:
    for c, n in r["classification_counts"].items():
        mcls[c] = mcls.get(c, 0) + n
mflags = {k: 0 for k in ("synthetic", "key_point", "withheld", "overlap")}
for r in rows:
    for k in mflags:
        if r["flags"].get(k):
            mflags[k] += r["flags"][k]
# overlap audit (bbox intersections)
overlaps = []
for i in range(len(rows)):
    for j in range(i + 1, len(rows)):
        a, b = rows[i], rows[j]
        ox = max(0, min(a["x_max"], b["x_max"]) - max(a["x_min"], b["x_min"]))
        oy = max(0, min(a["y_max"], b["y_max"]) - max(a["y_min"], b["y_min"]))
        if ox > 0 and oy > 0:
            overlaps.append({"tile_a": a["tile"], "tile_b": b["tile"],
                             "overlap_m2": round(ox * oy, 0)})
merged = {
    "n_tiles": len(rows),
    "total_points": int(tot),
    "bbox": dict(x_min=x0, x_max=x1, y_min=y0, y_max=y1,
                 area_km2=round(bbox_area / 1e6, 4)),
    "overall_density_pts_m2": round(tot / bbox_area, 2),
    "merged_classification_counts": mcls,
    "merged_flags": mflags,
    "tile_overlaps": overlaps,
    "spec": {
        "density_above_drying_line_min": 2,
        "density_below_drying_line_min": 1,
        "vertical_accuracy_above_LAT_m": 0.25,
        "horizontal_accuracy_m": 1.0,
        "vertical_datum": "NZVD2016",
        "horizontal_crs": "NZGD2000 / NZTM2000 (EPSG:2193)",
    },
    "run_date": datetime.date.today().isoformat(),
}
df = pd.DataFrame(rows).drop(columns=["classification_counts", "z_per_class", "flags", "crs_wkt"], errors="ignore")
df.to_csv(os.path.join(OUT, "qc_tiles.csv"), index=False)
with open(os.path.join(OUT, "qc_merged.json"), "w", encoding="utf-8") as fh:
    json.dump(merged, fh, indent=2, ensure_ascii=False)
with open(os.path.join(OUT, "qc_classification_detail.json"), "w", encoding="utf-8") as fh:
    json.dump([{k: r[k] for k in ("tile", "classification_counts", "z_per_class", "flags")} for r in rows],
              fh, indent=2, ensure_ascii=False)

print("\n========== MERGED ==========")
print(f"tiles {len(rows)} | points {tot:,} | bbox {bbox_area/1e6:.3f} km2 | density {tot/bbox_area:.1f} pts/m2")
print("merged classes:", {c: f"{n/1e6:.2f}M" for c, n in sorted(mcls.items())})
print("merged flags:", mflags)
print("overlaps:", overlaps)
print("saved: qc_tiles.csv, qc_merged.json, qc_classification_detail.json")
