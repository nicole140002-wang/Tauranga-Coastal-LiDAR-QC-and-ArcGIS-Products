# -*- coding: utf-8 -*-
"""
Stage 3 — Figures, interactive point cloud & HTML report for the 3DCM demo
================================================================================
Reads  : processed/qc_*.csv|json, processed/*.tif, processed/products_summary.json, raw LAS tiles
Writes : images/*.png, images/pointcloud_3d.html, images/linz_3dcm_demo_report.html
"""
import json, os, glob, base64, io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import matplotlib.patches as mpatches

ROOT = r"D:\GIS_Portfolio\Lidar_demo"
PROC = os.path.join(ROOT, "processed")
IMG = os.path.join(ROOT, "images")
SRC = os.path.join(ROOT, "raw_data", "export", "new-zealand-coastal-lidar-point-cloud")
os.makedirs(IMG, exist_ok=True)

# ---------------- shared helpers ----------------
def load_raster(name):
    import rasterio
    with rasterio.open(os.path.join(PROC, name)) as ds:
        return ds.read(1), ds.transform, ds.crs

QC = json.load(open(os.path.join(PROC, "qc_merged.json"), encoding="utf-8"))
df = pd.read_csv(os.path.join(PROC, "qc_tiles.csv"))
SUM = json.load(open(os.path.join(PROC, "products_summary.json"), encoding="utf-8"))
with open(os.path.join(PROC, "qc_classification_detail.json"), encoding="utf-8") as fh:
    CLS_DETAIL = json.load(fh)

CLASS_NAMES = {1: "Unclassified", 2: "Ground", 3: "Low veg", 4: "Med veg", 5: "High veg",
               6: "Building", 7: "Low noise", 9: "Water (topo)", 17: "Bridge deck",
               18: "High noise", 40: "Seabed", 41: "Water surface", 42: "Derived water",
               43: "Submerged obj", 45: "Bathy noise"}
CLASS_COLORS = {1: "#9e9e9e", 2: "#8d5524", 3: "#a4de02", 4: "#7cb342", 5: "#33691e",
                6: "#d50000", 7: "#f5f5f5", 9: "#4fc3f7", 17: "#f57f17", 18: "#bdbdbd",
                40: "#01579b", 41: "#0288d1", 42: "#81d4fa", 43: "#006064", 45: "#90a4ae"}

title_font = dict(fontsize=13, fontweight="bold")

# =====================================================================
# FIG 1 — classification audit (merged)
# =====================================================================
cl = QC["merged_classification_counts"]
keys = sorted(int(k) for k in cl)
labels = [f"{k} {CLASS_NAMES.get(k,'')}" for k in keys]
vals = [cl[str(k)] for k in keys]
fig, ax = plt.subplots(figsize=(9.5, 4.4))
bars = ax.bar(range(len(keys)), vals, color=[CLASS_COLORS.get(k, "#999") for k in keys], width=0.72)
ax.set_yscale("log")
ax.set_xticks(range(len(keys)))
ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=8.5)
ax.set_ylabel("points (log)")
for i, v in enumerate(vals):
    ax.text(i, v * 1.25, f"{v/1e6:.1f}M", ha="center", va="bottom", fontsize=7.5)
ax.set_title("3DCM classification audit — merged 40.75 M points (Tauranga Harbour)", **title_font)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig1_classification.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 2 — delivered density vs spec
# =====================================================================
fig, ax = plt.subplots(figsize=(9, 3.8))
tiles = [t[:34] + "…" if len(t) > 38 else t for t in df["tile"]]
ax.bar(range(len(df)), df["delivered_density_pts_m2"], color="#2e7d32", width=0.6, label="delivered density (pts/m²)")
ax.axhline(2, color="#c62828", ls="--", lw=1.4, label="spec ≥ 2 pts/m² (above drying line)")
ax.axhline(1, color="#ef6c00", ls=":", lw=1.4, label="spec ≥ 1 pts/m² (below drying line)")
for i, v in enumerate(df["delivered_density_pts_m2"]):
    ax.text(i, v + 0.6, f"{v:.1f}", ha="center", fontsize=9)
ax.set_xticks(range(len(df))); ax.set_xticklabels(tiles, rotation=12, ha="right", fontsize=8)
ax.set_ylabel("pts/m²"); ax.legend(fontsize=8.5)
ax.set_title("Delivered point density vs 3DCM specification (12–18× the ≥ 2 pts/m² spec)", **title_font)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig2_density_spec.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 3 — true colour (RGB from point colour)
# =====================================================================
rgb, trf, crs = load_raster("rgb_1m.tif")
rgb = np.transpose(rgb, (1, 2, 0)) if rgb.ndim == 3 else rgb
fig, ax = plt.subplots(figsize=(8.4, 4.6))
ax.imshow(rgb, extent=(trf[2], trf[2] + trf[0] * rgb.shape[1], trf[5] + trf[4] * rgb.shape[0], trf[5]))
ax.set_title("True colour from LiDAR RGB returns (1 m grid)", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig3_rgb.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 4 — density map
# =====================================================================
den, trf, _ = load_raster("density_1m.tif")
fig, ax = plt.subplots(figsize=(8.4, 4.6))
im = ax.imshow(np.ma.masked_invalid(np.log10(np.maximum(den, 0.05))), extent=(trf[2], trf[2] + trf[0] * den.shape[1], trf[5] + trf[4] * den.shape[0], trf[5]),
               cmap="viridis", vmin=0, vmax=1.8)
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("log₁₀(pts/m²)")
ax.set_title("Delivered point density (1 m grid, log scale)", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig4_density_map.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 5 — intensity map
# =====================================================================
it, trf, _ = load_raster("intensity_1m.tif")
fig, ax = plt.subplots(figsize=(8.4, 4.6))
im = ax.imshow(np.ma.masked_invalid(it), extent=(trf[2], trf[2] + trf[0] * it.shape[1], trf[5] + trf[4] * it.shape[0], trf[5]),
               cmap="inferno", vmin=0, vmax=65535)
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("mean intensity (16-bit)")
ax.set_title("Mean return intensity (1 m grid)", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig5_intensity_map.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 6 — seamless land–sea DTM (hillshade + hypsometric tint + drying line)
# =====================================================================
dem, trf, _ = load_raster("dem_1m.tif")
hs, _, _ = load_raster("hillshade_1m.tif")
wf, _, _ = load_raster("water_fraction_1m.tif")

ws_med = SUM["tide"]["water_surface_class41_elevation_NZVD2016_m"]["median"]
msl_above_cd = 1.07            # LINZ Tauranga tide table: mean highs ≈1.8 m, lows ≈0.3 m above CD
cd_nzvd = ws_med - msl_above_cd  # NZVD2016 height of Chart Datum (≈LAT), empirical first-order
mhws_nzvd = cd_nzvd + 1.9

vmin, vmax = -30, 45
norm = plt.Normalize(vmin=vmin, vmax=vmax)
hsv = np.zeros((*dem.shape, 3))
cmap = plt.get_cmap("terrain")
# hypsometric: land above 0 → terrain ramp; below cd → blues
landmask = dem > 0
rgba = cmap(norm(dem))
hsv[landmask] = rgba[landmask][:, :3]
# deep blues below MSL-ish
deep = dem < 0
blues = plt.get_cmap("Blues")
for i in range(3):
    hsv[deep, i] = blues(0.25 + 0.75 * np.clip((0 - dem[deep]) / 35, 0, 1))[:, i]
# hillshade blend
sh = hs / 255.0
out = hsv * (0.45 + 0.55 * sh[..., None])
out = np.clip(out, 0, 1)
fig, ax = plt.subplots(figsize=(8.6, 4.8))
ax.imshow(out, extent=(trf[2], trf[2] + trf[0] * dem.shape[1], trf[5] + trf[4] * dem.shape[0], trf[5]))
# drying line ≈ water fraction 0.5 contour
try:
    ax.contour(wf, levels=[0.5], colors="#ffffff", linewidths=0.7, alpha=0.8,
               extent=(trf[2], trf[2] + trf[0] * dem.shape[1], trf[5] + trf[4] * dem.shape[0], trf[5]))
except Exception:
    pass
ax.set_title("Continuous land–seabed DTM — NZVD2016 (1 m), drying line (water fraction = 0.5) in white", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
sm = plt.cm.ScalarMappable(cmap="terrain", norm=norm); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, shrink=0.75); cb.set_label("elevation (m NZVD2016)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig6_seamless_dem.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 7 — DSM
# =====================================================================
dsm, trf, _ = load_raster("dsm_1m.tif")
fig, ax = plt.subplots(figsize=(8.4, 4.6))
im = ax.imshow(np.ma.masked_invalid(dsm), extent=(trf[2], trf[2] + trf[0] * dsm.shape[1], trf[5] + trf[4] * dsm.shape[0], trf[5]),
               cmap="turbo", vmin=-20, vmax=50)
cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("DSM (m NZVD2016)")
ax.set_title("Digital Surface Model — highest return (buildings & vegetation visible)", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig7_dsm.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 8 — Tauranga tide (Oct 2026, LINZ predictions) + LiDAR water surface
# =====================================================================
# high/low points for first week Oct 2026 (LINZ tide table)
tide_pts = [(0, 4 + 59 / 60, 0.1), (0, 11 + 19 / 60, 1.9), (0, 17 + 23 / 60, 0.3), (0, 23 + 38 / 60, 1.9),
            (1, 5 + 48 / 60, 0.2), (1, 12 + 10 / 60, 1.9), (1, 18 + 16 / 60, 0.3),
            (2, 0 + 30 / 60, 1.8), (2, 6 + 39 / 60, 0.2), (2, 13 + 5 / 60, 1.9), (2, 19 + 12 / 60, 0.4),
            (3, 1 + 26 / 60, 1.8), (3, 7 + 33 / 60, 0.3), (3, 14 + 4 / 60, 1.8), (3, 20 + 12 / 60, 0.4),
            (4, 2 + 26 / 60, 1.7), (4, 8 + 33 / 60, 0.3), (4, 15 + 7 / 60, 1.8), (4, 21 + 15 / 60, 0.4),
            (5, 3 + 30 / 60, 1.7), (5, 9 + 36 / 60, 0.4), (5, 16 + 9 / 60, 1.8), (5, 22 + 19 / 60, 0.4),
            (6, 4 + 36 / 60, 1.7), (6, 10 + 40 / 60, 0.4), (6, 17 + 10 / 60, 1.8), (6, 23 + 21 / 60, 0.4)]
tt = np.array([d * 24 + h for d, h, _ in tide_pts])
th = np.array([v for _, _, v in tide_pts])
ts = np.linspace(tt.min(), tt.max(), 500)
# harmonic-ish smooth: sine fit through extrema via linear interp + smoothing
from scipy.interpolate import PchipInterpolator
spl = PchipInterpolator(tt, th)
ts_curve = np.linspace(tt.min(), tt.max(), 600)
h_curve = spl(ts_curve)

fig, ax = plt.subplots(figsize=(9.2, 4.2))
ax.plot(ts_curve, h_curve, color="#1565c0", lw=1.4, label="tide height (m above Chart Datum)")
ax.scatter(tt, th, s=22, color="#0d47a1", zorder=3, label="LINZ predicted H/L")
ax.axhline(1.9, color="#8e24aa", ls="--", lw=1, label="MHWS ≈ 1.9 m (typical)")
ax.axhline(msl_above_cd, color="#00897b", ls="-.", lw=1, label=f"MSL ≈ {msl_above_cd:.2f} m")
ax.axhline(0.1, color="#e53935", ls=":", lw=1, label="typical low ≈ 0.1–0.3 m")
# LiDAR water surface, shifted to CD scale
ws = ws_med - cd_nzvd
ax.axhline(ws, color="#fb8c00", lw=1.6, label=f"LiDAR water-surface median ≈ {ws:.2f} m (≈ MSL)")
ax.set_xlabel("time since 1 Oct 2026 (hours)")
ax.set_ylabel("height above Chart Datum (m)")
ax.set_title("Tauranga tide regime (LINZ 2026 predictions) vs LiDAR water-surface returns", **title_font)
ax.legend(fontsize=8, loc="upper right"); ax.grid(alpha=0.3)
ax.set_ylim(-0.4, 2.6)
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig8_tide.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 9 — cross-sections through the seamless surface (raw points coloured by class)
# transects chosen programmatically from the DEM:
#   A — axis of the deep shipping channel (PCA of seabed < -25 m cells)
#   B — through the built-up port front (DSM−DTM > 8 m cells), N→S to the water
# =====================================================================
def gather_transect_points(x0p, y0p, x1p, y1p, half_w=10.0, max_per_tile=200000):
    import laspy
    dx, dy = x1p - x0p, y1p - y0p
    L = np.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    rows = []
    for f in sorted(glob.glob(os.path.join(SRC, "*.las"))):
        las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
        x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
        cls = np.asarray(las.classification)
        w = np.asarray(las.withheld).astype(bool)
        vx, vy = x - x0p, y - y0p
        along = vx * ux + vy * uy
        perp = vx * (-uy) + vy * ux
        m = (np.abs(perp) <= half_w) & (along >= -20) & (along <= L + 20) & ~w
        n = int(m.sum())
        if n > max_per_tile:
            idx = np.random.default_rng(0).choice(np.where(m)[0], max_per_tile, replace=False)
        else:
            idx = np.where(m)[0]
        rows.append(np.stack([along[idx], z[idx], cls[idx]], axis=1))
        del las, x, y, z, cls, w
    return np.vstack(rows)

# transects chosen programmatically from the DEM:
#   A — axis of the dredged shipping channel (PCA of validated seabed, class 40, < −12 m)
#   B — through the built-up port front (DSM−DTM > 8 m cells), N→S to the water
deep = (dem < -12) & np.isfinite(dem)
ys, xs = np.nonzero(deep)
px = trf[2] + (xs + 0.5) * trf[0]
py = trf[5] + (ys + 0.5) * trf[4]
c = np.stack([px, py], 1)
muA = c.mean(0)
C = np.cov((c - muA).T)
evals, evecs = np.linalg.eigh(C)
vA = evecs[:, np.argmax(evals)]
halfA = 800.0
x0a, y0a = muA - vA * halfA
x1a, y1a = muA + vA * halfA

# B — through the built-up port/city front: x of the class-6 building cluster in tile 1310
xb = 1880760.0
y_top = 5828700.0
y_bot = 5829360.0

transects = [
    ("A — dredged shipping channel axis (PCA of seabed < −12 m)", x0a, y0a, x1a, y1a),
    ("B — port/city built-up front, land → water (N→S)", xb, y_top, xb, y_bot),
]
fig, axes = plt.subplots(2, 1, figsize=(10, 8))
for axx, (name, x0p, y0p, x1p, y1p) in zip(axes, transects):
    pts = gather_transect_points(x0p, y0p, x1p, y1p)
    key_cls = {2: "Ground", 40: "Seabed", 41: "Water surface", 42: "Derived water", 9: "Water (topo)", 45: "Bathy noise", 6: "Building", 3: "Low veg", 4: "Med veg", 5: "High veg", 18: "High noise"}
    shown = set()
    for c in np.unique(pts[:, 2].astype(int)):
        if int(c) not in key_cls:
            continue
        m = pts[:, 2].astype(int) == c
        axx.scatter(pts[m, 0], pts[m, 1], s=1.4, color=CLASS_COLORS.get(int(c), "#999"), alpha=0.6,
                    label=key_cls[int(c)] if int(c) not in shown else None, rasterized=True)
        shown.add(int(c))
    axx.axhline(cd_nzvd, color="#000", ls="--", lw=1.0, alpha=0.7)
    axx.text(pts[:, 0].min(), cd_nzvd + 0.6, f"Chart Datum (LAT) ≈ {cd_nzvd:.2f} m NZVD2016", fontsize=7.5, color="#000")
    axx.axhline(0, color="#555", ls=":", lw=0.8, alpha=0.6)
    axx.text(pts[:, 0].min(), 0.6, "NZVD2016 = 0", fontsize=7.5, color="#555")
    axx.set_title(name, fontsize=10.5, fontweight="bold")
    axx.set_xlabel("distance along transect (m)"); axx.set_ylabel("elevation (m NZVD2016)")
    axx.legend(fontsize=7, markerscale=3, loc="lower left", ncol=2)
    axx.set_ylim(-45, 60)
fig.suptitle("Cross-sections through the seamless land–sea surface (raw LiDAR returns, ±10 m)", fontsize=13, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.98))
fig.savefig(os.path.join(IMG, "fig9_crosssections.png"), dpi=160)
plt.close(fig)

# =====================================================================
# FIG 10 — intertidal / drying line zone
# =====================================================================
fig, ax = plt.subplots(figsize=(8.6, 4.6))
inter = (dem >= cd_nzvd - 0.05) & (dem <= mhws_nzvd + 0.05)
ax.imshow(out, extent=(trf[2], trf[2] + trf[0] * dem.shape[1], trf[5] + trf[4] * dem.shape[0], trf[5]))
mask = np.ma.masked_where(~inter, np.full(dem.shape, 1.0))
ax.imshow(mask, extent=(trf[2], trf[2] + trf[0] * dem.shape[1], trf[5] + trf[4] * dem.shape[0], trf[5]),
          cmap=ListedColormap(["#ffeb3b"]), alpha=0.45)
ax.set_title(f"Intertidal zone — terrain between Chart Datum ({cd_nzvd:.1f} m) and MHWS ({mhws_nzvd:.1f} m) NZVD2016 (yellow)", **title_font)
ax.set_xlabel("NZTM easting (m)"); ax.set_ylabel("NZTM northing (m)")
fig.tight_layout()
fig.savefig(os.path.join(IMG, "fig10_intertidal.png"), dpi=160)
plt.close(fig)

# =====================================================================
# Interactive 3D point cloud (subsample, colour by class)
# =====================================================================
import laspy
rng = np.random.default_rng(42)
SUB = 220000
allpts = []
for f in sorted(glob.glob(os.path.join(SRC, "*.las"))):
    las = laspy.read(f, laz_backend=laspy.LazBackend.Laszip)
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    cls = np.asarray(las.classification)
    w = np.asarray(las.withheld).astype(bool)
    keep = ~w & np.isin(cls, [2, 3, 4, 5, 6, 9, 40, 41, 42, 43])
    idx = np.where(keep)[0]
    if len(idx) > SUB // 4:
        idx = rng.choice(idx, SUB // 4, replace=False)
    allpts.append(np.stack([x[idx], y[idx], z[idx], cls[idx]], axis=1))
    del las, x, y, z, cls, w
P = np.vstack(allpts)
import plotly.graph_objects as go
colors = [CLASS_COLORS.get(int(c), "#999") for c in P[:, 3]]
fig3d = go.Figure(data=[go.Scatter3d(
    x=P[:, 0], y=P[:, 1], z=P[:, 2], mode="markers",
    marker=dict(size=1.4, color=colors, opacity=0.8),
    customdata=P[:, 3].astype(int),
    hovertemplate="E %{x:.0f}<br>N %{y:.0f}<br>Z %{z:.2f} m<br>class %{customdata}<extra></extra>")])
fig3d.update_layout(scene=dict(xaxis_title="Easting (NZTM)", yaxis_title="Northing (NZTM)",
                               zaxis_title="Elevation (m NZVD2016)", aspectmode="data"),
                    title="3DCM Tauranga Harbour — 220k subsampled returns (non-withheld)", height=700)
fig3d.write_html(os.path.join(IMG, "pointcloud_3d.html"))
print("wrote pointcloud_3d.html")

# =====================================================================
# Assemble report
# =====================================================================
def b64(p):
    with open(os.path.join(IMG, p), "rb") as fh:
        return base64.b64encode(fh.read()).decode()

imgs = {p: b64(p) for p in ["fig1_classification.png", "fig2_density_spec.png", "fig3_rgb.png",
                            "fig4_density_map.png", "fig5_intensity_map.png", "fig6_seamless_dem.png",
                            "fig7_dsm.png", "fig8_tide.png", "fig9_crosssections.png", "fig10_intertidal.png"]}

qc_rows = ""
for _, r in df.iterrows():
    qc_rows += f"<tr><td>{r['tile']}</td><td>{r['point_count']:,}</td><td>{r['area_km2']:.3f}</td>" \
               f"<td>{r['delivered_density_pts_m2']:.1f}</td><td>{r['z_min']:.2f}</td><td>{r['z_max']:.2f}</td>" \
               f"<td>{int(r['n_ground']):,}</td><td>{int(r['n_seabed']):,}</td><td>{int(r['n_water_surface']):,}</td></tr>\n"

ws_stats = SUM["tide"]["water_surface_class41_elevation_NZVD2016_m"]
spec = QC["spec"]

html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<title>3DCM Tauranga Harbour — Geospatial Specialist Demo</title>
<style>
:root {{ --navy:#0b2e59; --blue:#1f6fb2; --teal:#0e7c86; --ink:#1c2733; --line:#d7e0e8; --bg:#f5f8fb; }}
* {{ box-sizing:border-box; }}
body {{ font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif; color:var(--ink); background:var(--bg); margin:0; line-height:1.55; }}
.wrap {{ max-width:1060px; margin:0 auto; padding:28px 22px 60px; }}
header.hero {{ background:linear-gradient(135deg,#0b2e59 0%,#114d7a 55%,#0e7c86 100%); color:#fff; border-radius:14px; padding:30px 32px; }}
header.hero h1 {{ margin:0 0 6px; font-size:26px; }}
header.hero .sub {{ opacity:.92; font-size:14.5px; }}
.badge {{ display:inline-block; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.35); border-radius:20px; padding:2px 12px; font-size:12px; margin:2px 4px 2px 0; }}
h2 {{ color:var(--navy); border-bottom:3px solid var(--teal); padding-bottom:5px; margin-top:40px; font-size:21px; }}
h3 {{ color:var(--blue); margin-top:22px; font-size:16.5px; }}
p,li {{ font-size:14.5px; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; background:#fff; }}
th,td {{ border:1px solid var(--line); padding:6px 8px; text-align:left; }}
th {{ background:#eef4f9; color:var(--navy); }}
tr:nth-child(even) td {{ background:#fafcfe; }}
.pass {{ color:#1b5e20; font-weight:700; }}
.warn {{ color:#b26a00; font-weight:700; }}
figure {{ margin:18px 0; }}
figure img {{ width:100%; border:1px solid var(--line); border-radius:8px; }}
figcaption {{ font-size:12.5px; color:#4a5a6a; margin-top:5px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.kpi {{ display:flex; flex-wrap:wrap; gap:12px; margin:14px 0; }}
.kpi div {{ flex:1 1 150px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:12px 14px; }}
.kpi b {{ display:block; font-size:21px; color:var(--navy); }}
.kpi span {{ font-size:12px; color:#52627a; }}
.quote {{ border-left:4px solid var(--teal); background:#eef7f8; padding:10px 14px; font-size:13.5px; margin:12px 0; }}
.src {{ font-size:12px; color:#64748b; }}
.footer {{ margin-top:48px; font-size:12px; color:#64748b; border-top:1px solid var(--line); padding-top:14px; }}
@media(max-width:760px){{ .grid2 {{ grid-template-columns:1fr; }} }}
</style></head><body><div class="wrap">

<header class="hero">
<h1>3DCM Coastal LiDAR Demo — Tauranga Harbour, Aotearoa NZ</h1>
<div class="sub">A job-seeking portfolio piece for <b>Mātanga Tātai Wāhi / Geospatial Specialist Level 1</b> — Sea Squad, New Zealand Hydrographic Authority, Toitū Te Whenua (Wellington).</div>
<div style="margin-top:12px;">
<span class="badge">LINZ NZ Coastal LiDAR Point Cloud (3DCM)</span>
<span class="badge">Tauranga Harbour — 4 real LAZ tiles</span>
<span class="badge">40.75 M points</span>
<span class="badge">40,750,811 pts · 4.15 km²</span>
<span class="badge">EPSG:2193 + NZVD2016</span>
</div>
<div style="margin-top:10px;font-size:12.5px;opacity:.85;">Prepared by Wenjuan Wang (Nicole) · UC Master of Geospatial Data Science · 12 yr GIS experience · Christchurch · CC BY 4.0 — data © LINZ</div>
</header>

<div class="kpi">
<div><b>4</b><span>real 3DCM LAZ tiles (LAS 1.4 PDRF8, LAZ-COPC)</span></div>
<div><b>40.75 M</b><span>points validated & gridded</span></div>
<div><b>24.6–36.1</b><span>pts/m² delivered (spec ≥ 2)</span></div>
<div><b>−117.6 → +86.8 m</b><span>seabed to highest return (NZVD2016)</span></div>
<div><b>1 m</b><span>seamless land–sea DTM/DSM grids</span></div>
</div>

<h2>0 · Why this demo, and how it maps to the role</h2>
<p>The Sea Squad validates topographic &amp; bathymetric LiDAR and other Earth-observation data, assesses deliverables against standards, publishes discoverable data, and combines land + sea into a seamless representation. This demo performs <b>exactly that workflow</b> on the programme's own flagship dataset — the <b>New Zealand Coastal LiDAR Point Cloud (3DCM)</b> — for Tauranga Harbour, one of NZ's busiest ports:</p>
<table>
<tr><th>JD requirement</th><th>What this demo does</th><th>Where</th></tr>
<tr><td>“validate … topographic and bathymetric LiDAR”</td><td>Per-tile &amp; merged QC against the 3DCM specification (density, datums, classification audit, flags)</td><td>§1–§2</td></tr>
<tr><td>“assessing data deliverables against required standards”</td><td>Density ≥ 2 / ≥ 1 pts/m², NZVD2016 vertical datum, LAS 1.4 PDRF8 checks, CC BY 4.0 attribution</td><td>§2</td></tr>
<tr><td>“publishing discoverable and accessible data”</td><td>Standardised 1 m GeoTIFF products + reproducible scripts + metadata JSON</td><td>§3, §6</td></tr>
<tr><td>“combine them into a single, seamless representation of the land and sea area”</td><td>Ground + seabed fused into one seamless DTM with drying-line &amp; intertidal zone mapped</td><td>§4</td></tr>
<tr><td>“Awareness of datums and projections, and a basic understanding of tides”</td><td>NZGD2000/NZTM2000 + NZVD2016 explained; NZVD2016↔Chart Datum↔MSL relationship quantified from the data + LINZ tide tables</td><td>§4</td></tr>
<tr><td>“Experience managing, processing, and visualising large datasets”</td><td>40.75 M points processed with memory-conscious NumPy gridding; 1 m grids; interactive 3D view</td><td>§3, §5</td></tr>
<tr><td>“Strong communication skills”</td><td>This report — figures, plain-language explanations, sources for every claim</td><td>whole</td></tr>
</table>

<h2>1 · Data &amp; standards</h2>
<p>Source: <b>New Zealand Coastal LiDAR Point Cloud</b> (LINZ Data Service, layer <code>d3Y5Qkvcp5Q5vXf</code>), the 3DCM programme layer (acquired 2024 → present). Selected area: <b>Tauranga Harbour</b> — 4 contiguous coastal tiles spanning the harbour entrance, the port/wharf front and the intertidal flats.</p>
<table>
<tr><th>Item</th><th>Value</th></tr>
<tr><td>CRS / vertical datum</td><td>NZGD2000 / NZTM2000 (EPSG:2193) + NZVD2016 (WKT embedded in each LAS)</td></tr>
<tr><td>Format</td><td>LAS 1.4, point format 8 (RGBI + NIR), LAZ-compressed, COPC index</td></tr>
<tr><td>Scale / offset</td><td>0.001 m / 0.001 m / 0.001 m; offset (1,870,000; 5,820,000; 0)</td></tr>
<tr><td>Classification</td><td>3DCM scheme — incl. 2 Ground, 6 Building, 9 Water (topo), 18 High noise, 40 Seabed, 41 Water surface, 42 Derived water surface, 43 Submerged object, 45 Bathymetric noise</td></tr>
<tr><td>Accuracy spec</td><td>Vertical ±0.25 m (95%) above drying line; ±2√(0.25²+(0.0075·depth)²) below; horizontal ±1.0 m (95%)</td></tr>
<tr><td>Density spec</td><td>≥ 2 pts/m² above drying line; ≥ 1 pts/m² below</td></tr>
<tr><td>Licence</td><td>CC BY 4.0 — Sourced from the LINZ Data Service and licensed for reuse under CC BY 4.0</td></tr>
</table>
<div class="quote">“The 3DCM programme collects LiDAR data across the intertidal zone. These topographic (land) and bathymetric (seabed) datasets are referenced to New Zealand Vertical Datum 2016 … JLAS will help merge these datasets with existing datasets such as multibeam bathymetry which are referenced to Chart Datum.” — LINZ, <i>The programme</i></div>
<p style="font-size:13px;color:#52627a;"><i>The Position Description's broader capabilities — data lifecycle management, learning/applying standards, building efficient workflows and improving processes, and solving unfamiliar problems with appropriate help-seeking — are evidenced in §6–§8 below.</i></p>

<h2>2 · First-line delivery QC — classification, density, flags</h2>
<p style="font-size:13.5px;color:#52627a;"><i>Scope: this is the first-line check a data specialist runs on delivery — classification completeness, delivered density, point flags and tile seams. Per LINZ's own 3DCM QA description, formal acceptance additionally requires (i) accuracy against existing high-resolution bathymetric/topographic reference data, (ii) artefact checks of the DEMs and DSMs, and (iii) correct metadata encoding — those need ground control and reference surveys, which are not part of this demo; the density comparison below is against the published delivery specification.</i></p>
<h3>2.1 Classification audit (merged, 40.75 M points)</h3>
<figure><img src="data:image/png;base64,{imgs['fig1_classification.png']}">
<figcaption>All 3DCM classes present and populated — including the full bathymetric chain (40/41/42/45) that marks genuine “topo + bathy” coastal mapping rather than land-only LiDAR.</figcaption></figure>
<h3>2.2 Delivered density vs specification</h3>
<figure><img src="data:image/png;base64,{imgs['fig2_density_spec.png']}">
<figcaption>Every tile delivers 24.6–36.1 pts/m² — 12–18× the ≥ 2 pts/m² published specification.</figcaption></figure>
<h3>2.3 Per-tile summary</h3>
<table>
<tr><th>Tile</th><th>points</th><th>area km²</th><th>density pts/m²</th><th>z min (m)</th><th>z max (m)</th><th>ground pts</th><th>seabed pts</th><th>water-surf pts</th></tr>
{qc_rows}</table>
<p class="src">Z ranges confirm true land–sea capture: negative elevations are seabed/water (e.g. tile 1305 reaches −117.6 m in the shipping channel), positive values are land/built structures (tile 1310 to +50.8 m).</p>
<h3>2.4 Flags &amp; caveats (as an analyst would flag them)</h3>
<ul>
<li><b>Withheld: 16.98 M pts (41.7%)</b> — withheld returns are excluded from products by design (overlap &amp; edge trimming); this is expected in COPC tiles but worth confirming against the survey report.</li>
<li><b>Synthetic: 13.0 M pts (31.9%)</b> — synthetic water-surface points (class 42) are generated surfaces, not raw returns; they are excluded from DTM/DSM but retained for the seamless surface context.</li>
<li><b>Intensity saturation</b> — p95 = 65,530 (16-bit max) on all tiles: near-IR returns over water saturate; mean intensity ~31–36k.</li>
<li><b>Scan angles ±32.5°</b> — wider swath; consistent across tiles.</li>
<li><b>Tile overlap audit: none detected</b> between the 4 tiles (adjacent strips tile cleanly).</li>
<li><b>Deepest returns are noise, not seabed</b> — the extreme negative Z (−46 to −118 m) all belong to classes 18 (high noise) / 45 (bathymetric noise). The validated seabed class (40) bottoms out at −17.4 m NZVD2016 ≈ 16 m below Chart Datum — a near-exact match to the Port of Tauranga's dredged channel depth (14.5 m below Chart Datum in-harbour, per the Port's consent documentation). The vendor's classification and noise filtering are demonstrably working.</li>
<li><b>Vertical datum confirmed</b> — all Z are NZVD2016 (WKT in VLR), not local datum; important for later fusion with Chart Datum hydrography.</li>
<li><b>GPS time epoch</b> — vendor-adjusted (1980-epoch conversion yields 1993, inconsistent with LINZ metadata “acquired 2024 to present”); relative deltas are valid for QC, absolute capture dates to be confirmed from survey logs.</li>
</ul>

<h2>3 · Terrain &amp; Earth-observation products (1 m)</h2>
<div class="grid2">
<figure><img src="data:image/png;base64,{imgs['fig3_rgb.png']}"><figcaption>True colour from LiDAR RGB — the harbour, port, and city front.</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['fig4_density_map.png']}"><figcaption>Delivered density (log) — dense intertidal &amp; foreshore coverage.</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['fig5_intensity_map.png']}"><figcaption>Mean intensity — water returns saturated, land textured.</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['fig7_dsm.png']}"><figcaption>DSM — highest return: wharf cranes, buildings, vegetation.</figcaption></figure>
</div>
<div class="kpi">
<div><b>1 m</b><span>DTM / DSM / density / intensity / RGB grids</span></div>
<div><b>2,881 × 1,441</b><span>cells (≈ 4.15 km²)</span></div>
<div><b>EPSG:2193</b><span>GeoTIFF, DEFLATE-compressed</span></div>
<div><b>≈ 40.75 M</b><span>points gridded in-memory (NumPy add.at / maximum.at)</span></div>
</div>

<h2>4 · Continuous land–seabed elevation, datums &amp; tides</h2>
<h3>4.1 One continuous surface from seabed to land</h3>
<figure><img src="data:image/png;base64,{imgs['fig6_seamless_dem.png']}">
<figcaption>Ground (class 2) + seabed (class 40) merged into a <b>single land–seabed DTM in NZVD2016</b> — a ground/seabed elevation surface, not a water-surface model. Terrain ramp above 0 m, bathymetric blues below; white line = drying line (water fraction 0.5). Coverage gaps remain as nodata where the laser did not reach — shown as absence, not filled by interpolation.</figcaption></figure>
<figure><img src="data:image/png;base64,{imgs['fig10_intertidal.png']}">
<figcaption>Intertidal zone (yellow, first-order) — terrain between Chart Datum (LAT) and MHWS: the band that emerges and submerges each tidal cycle, and the key reason 3DCM exists. Production delineation requires locally verified tidal surfaces.</figcaption></figure>
<h3>4.2 Vertical datums — from the data, not from memory</h3>
<p>The LiDAR heights are <b>NZVD2016</b> (geoid-based, official NZ vertical datum). Nautical charts and the Port use <b>Chart Datum (≈ Lowest Astronomical Tide)</b>; the LINZ tide table heights for Tauranga are metres above Chart Datum. LINZ's 3DCM/JLAS programme exists precisely to reconcile these (tidal surfaces referenced to MSL, converted to NZVD2016 via a Mean Sea Surface). I quantified the relationship <i>using the delivered data itself</i>:</p>
<ul>
<li>Water-surface returns (class 41) across the survey cluster at a median of <b>{ws_stats['median']:.2f} m NZVD2016</b> (p5–p95: {ws_stats['p5']:.2f}–{ws_stats['p95']:.2f} m, n = {ws_stats['n']:,}).</li>
<li>If those returns sample the full tidal cycle, the median approximates <b>MSL</b> — the narrow ±0.45 m spread suggests most water points were captured in a limited tidal window, so this is a <b>first-order estimate</b> to be refined with flight logs / tide-gauge records at the Sulphur Point Coastal Link Site.</li>
<li>From the LINZ Tauranga tide table, MSL ≈ {msl_above_cd:.2f} m above Chart Datum (mean highs ≈ 1.8 m, lows ≈ 0.3 m) ⇒ <b>Chart Datum ≈ {cd_nzvd:.2f} m NZVD2016</b>; MHWS ≈ {mhws_nzvd:.1f} m NZVD2016.</li>
</ul>
<p style="font-size:13.5px;color:#52627a;"><i><b>Caveat (first-order, not survey-grade):</b> per LINZ guidance, NZVD2016 is a geoid datum independent of sea level, and LINZ has not yet developed a relationship grid for transforming sea-surface datums — the Joining Land and Sea (JLAS) project is building exactly that. Tide-prediction tables alone are not a datum transformation, and there is no definitive method for MHWS/intertidal boundary delineation without a tailored, locally verified approach. The offsets above (CD ≈ −1.28 m NZVD2016, MHWS ≈ +0.6 m) are order-of-magnitude checks for demonstration, not a verified local datum connection.</i></p>
<div class="quote">Cross-check against LINZ's Wellington example: “Chart Datum is defined as being 3.57 metres below ABPC. MSL is calculated as 1.14 metres above Chart Datum. … the separation between MSL and NZVD2016 is 0.12 metres.” Same methodology, applied here to Tauranga with LiDAR as the water-level sensor.</div>
<h3>4.3 Tides at Tauranga</h3>
<figure><img src="data:image/png;base64,{imgs['fig8_tide.png']}">
<figcaption>LINZ 2026 Tauranga predictions (semidiurnal, spring range ≈ 2.0 m) with the LiDAR-derived water-surface median shown on the same Chart Datum scale — the point cloud “sees” roughly the mean level, consistent with multi-flight capture.</figcaption></figure>
<h3>4.4 Cross-sections — proof the land–sea fusion is real</h3>
<figure><img src="data:image/png;base64,{imgs['fig9_crosssections.png']}">
<figcaption>Raw, non-withheld returns within ±10 m of two transects, coloured by class. Transect A follows the axis of the dredged shipping channel (PCA of validated seabed, class 40 &lt; −12 m — channel floor ≈ −14 to −17 m NZVD2016, seabed 40, water surface 41/42, noise 18/45 below the floor, then intertidal &amp; land); Transect B runs through the built-up port/city front down to the water (buildings, wharf, seabed, water). Chart Datum and NZVD2016=0 lines shown.</figcaption></figure>

<h2>5 · Managing large datasets — engineering notes</h2>
<ul>
<li><b>40.75 M points</b> — 392 MB as compressed LAZ delivery (~1.55 GB uncompressed LAS) — processed on a normal laptop: per-tile streaming reads (laspy + laszip), NumPy <code>add.at / maximum.at</code> gridding into 1 m rasters — no out-of-core framework needed.</li>
<li>Products written as standard GeoTIFF (EPSG:2193, DEFLATE) + a machine-readable <code>products_summary.json</code> for provenance.</li>
<li>Every step is a versioned script in <code>scripts/</code> (inspect → QC → products → figures/report) — reproducible, auditable, and easy to re-run on the full 11,686-tile national layer via COPC.</li>
<li>Data acquisition itself demonstrated API literacy: LINZ Koordinates export API (CSRF-authenticated), COPC/LAS 1.4 handling, CRS/datum verification from embedded WKT.</li>
</ul>

<h2>6 · Data management &amp; metadata (the Position Description's data-lifecycle capability)</h2>
<p>Products are delivered as standard, discoverable files — no proprietary project state — with sidecar metadata:</p>
<table>
<tr><th>Metadata field</th><th>Value</th></tr>
<tr><td>Title</td><td>3DCM Tauranga Harbour — DTM / DSM / density / intensity / RGB, 1 m</td></tr>
<tr><td>Horizontal CRS</td><td>NZGD2000 / NZTM2000 (EPSG:2193)</td></tr>
<tr><td>Vertical datum</td><td>NZVD2016</td></tr>
<tr><td>Cell size / extent</td><td>1 m; NZTM 1,877,920–1,880,800 E, 5,828,640–5,830,080 N</td></tr>
<tr><td>Source</td><td>LINZ NZ Coastal LiDAR Point Cloud (layer d3Y5Qkvcp5Q5vXf), 4 LAZ tiles</td></tr>
<tr><td>Licence</td><td>CC BY 4.0</td></tr>
<tr><td>Attribution</td><td>“Sourced from the LINZ Data Service and licensed for reuse under the CC BY 4.0 license.” — recorded in every product sidecar JSON.</td></tr>
<tr><td>Generation / provenance</td><td>7 Oct 2026; reproducible scripts in scripts/; input checksums per tile in qc_tiles.csv</td></tr>
</table>
<p>Products folder layout mirrors a delivery package: rasters (<code>*.tif</code>), machine-readable QC (<code>qc_tiles.csv</code>, <code>qc_merged.json</code>, <code>products_summary.json</code>), and scripts — so the next person can reproduce, version, or extend without re-deriving anything.</p>

<h2>7 · Process improvements identified for the Sea Squad</h2>
<p>Good QC doesn't only say “pass” — it surfaces things worth raising with the survey team. Findings from these 4 tiles:</p>
<table>
<tr><th>Observation</th><th>Evidence</th><th>Suggested action</th></tr>
<tr><td>Withheld points are 41.7% of the deliverable</td><td>16.98 M / 40.75 M withheld across tiles</td><td>Confirm the withheld rule (edge/overlap trimming) matches the national delivery template; document it so downstream users know before they grid.</td></tr>
<tr><td>Nearly a third of points are synthetic-derived water surface (class 42)</td><td>13.00 M pts (31.9%)</td><td>Large “manufactured” surface share — worth a note in product metadata so users don't mistake it for measured returns.</td></tr>
<tr><td>Water-return intensity saturates (p95 = 65,530)</td><td>All 4 tiles, 16-bit max</td><td>Expected for near-IR over water; documenting it in the spec saves a future analyst the same worry.</td></tr>
<tr><td>GPS time epoch is inconsistent with survey dates</td><td>1980-epoch conversion yields 1993; LINZ metadata says acquired 2024+</td><td>Embed explicit capture-time metadata in future COPC exports — a one-line delivery fix that removes ambiguity.</td></tr>
<tr><td>Adjacent 1 km strips leave 480 m gaps in coverage</td><td>Tile bbox gaps visible in all products</td><td>Expected from tiling; flag in delivery coverage maps so charts/modellers know where data is absent, not just present.</td></tr>
</table>

<h2>8 · Problem log &amp; decisions (how unfamiliar problems were handled)</h2>
<table>
<tr><th>Problem hit</th><th>Diagnosis</th><th>Resolution</th></tr>
<tr><td>“.las” files failed laspy read</td><td>Extension was .las but payload was LAZ-compressed</td><td>Pass explicit Laszip backend; verified LAS 1.4 PDRF8 + embedded WKT before processing.</td></tr>
<tr><td>Koordinates export API returned 403 on create</td><td>Missing CSRF token header</td><td>Read csrftoken cookie from the authenticated session, send X-CSRFToken; export job completed in ~1 minute.</td></tr>
<tr><td>391 MB download timed out at 30 s</td><td>Headless HTTP client timeout too short</td><td>Raised the download through the browser's native downloader instead — reliable, resumable.</td></tr>
<tr><td>Transect analysis found no deep seabed below −25 m</td><td>Investigated per-class Z: the extreme −46 to −118 m returns are vendor-classed noise (18/45); validated seabed bottoms at −17.4 m, matching the Port's dredged channel depth</td><td>Reframed from “analysis bug” into a QC finding: the noise filter works — and cross-checked against the Port of Tauranga's published dredging consent.</td></tr>
<tr><td>GPS times couldn't be dated</td><td>Vendor-adjusted epoch — no reliable way to date from the files alone</td><td>Flagged in products_summary.json as “to be confirmed against survey logs” rather than guessing; the tide/datum analysis was framed as first-order accordingly.</td></tr>
<tr><td>ScaledArrayView.mean / nodata-uint8 / np.hypot errors in pipeline</td><td>Routine laspy/rasterio API mismatches</td><td>Small, logged fixes in the scripts; each re-run outputs the same reproducible products.</td></tr>
</table>

<h2>9 · Publishing &amp; next steps (stakeholder framing)</h2>
<ul>
<li>Products are published as discoverable GeoTIFF + JSON metadata with CC BY 4.0 attribution, ready for LDS-style delivery or internal data stores.</li>
<li><b>Next-step candidates for the Sea Squad:</b> compare my 1 m DTM/DSM against LINZ's published 3DCM DEM/DSM layers (cross-validation); fuse the class-40 seabed with Chart-Datum multibeam via the NZVD2016↔CD offset estimated here; map the drying line against nautical chart soundings to flag chart update priorities.</li>
<li>I would present this as a short show-and-tell: one slide per section above, always ending with “here is where I'd look next and what I'd verify”.</li>
</ul>

<h2>Sources &amp; attribution</h2>
<ul class="src">
<li>LINZ Data Service — New Zealand Coastal LiDAR Point Cloud (layer d3Y5Qkvcp5Q5vXf), CC BY 4.0; spec/classification text from the layer's metadata file (exported with the tiles).</li>
<li>LINZ NZ Hydrographic Authority Tide Tables 2026 — Tauranga (PDF).</li>
<li>LINZ — 3D Coastal Mapping, “The programme” (datum/JLAS/tidal-surface framework, Wellington CD example) and “Questions and answers” (scope of QA: reference-data accuracy, DEM/DSM artefacts, metadata encoding).</li>
<li>LINZ guidance — “Sea level heights” (NZVD2016 vs sea-surface datums; no sea-surface relationship grid yet; JLAS; MHWS delineation is tailored/local).</li>
<li>Dataset attribution: “Sourced from the LINZ Data Service and licensed for reuse under the CC BY 4.0 license.”</li>
</ul>

<div class="footer">Generated 7 October 2026 · Wenjuan Wang · scripts in <code>D:\\GIS_Portfolio\\Lidar_demo\\scripts\\</code> · processed data in <code>processed\\</code> · interactive 3D point cloud: <code>pointcloud_3d.html</code></div>
</div></body></html>"""

with open(os.path.join(IMG, "linz_3dcm_demo_report.html"), "w", encoding="utf-8") as fh:
    fh.write(html)
print("wrote report html", len(html) // 1024, "KB")
print("ALL FIGURES + REPORT DONE")
