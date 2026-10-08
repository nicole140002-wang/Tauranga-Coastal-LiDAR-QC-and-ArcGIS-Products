# Tauranga Coastal LiDAR — QC & 1 m ArcGIS Products

Independent portfolio demonstration on LINZ 3D Coastal Mapping data (New Zealand Coastal LiDAR Point Cloud), prepared for the Toitū Te Whenua Sea Squad Geospatial Specialist role.

**Report:** [`images/linz_3dcm_demo_report.html`](images/linz_3dcm_demo_report.html) — open in a browser.

## What this is

- 4 selected tiles around Tauranga Harbour, **40,750,811 point records** (LAS 1.4 PDRF8, NZTM2000 / NZVD2016).
- First-line QC: classification audit, withheld/synthetic counts, per-class elevation ranges, intensity statistics.
- 1 m ArcGIS Pro products: DTM (ground + seabed), DSM, RGB, mean intensity, point density, hillshade, elevation profile.
- Explicit limits: no formal acceptance, no verified Chart Datum connection, no intertidal boundary.

## Structure

```
images/      HTML report + ArcGIS screenshots (PNG)
scripts/     Python QC scripts (laspy / numpy)
arcgis/      ArcGIS project notes and screenshot README
```

Point-cloud data (.laz/.las) and GeoTIFFs are excluded from Git; the report describes them without committing the large files.

## Data source

Sourced from the [LINZ Data Service](https://data.linz.govt.nz/layer/d3Y5Qkvcp5Q5vXf/new-zealand-coastal-lidar-point-cloud/) and licensed by Toitū Te Whenua Land Information New Zealand under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Wenjuan Wang (Nicole) · Christchurch, NZ · 2026
