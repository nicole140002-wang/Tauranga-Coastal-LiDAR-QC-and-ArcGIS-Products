# -*- coding: utf-8 -*-
import json
p = r"D:\GIS_Portfolio\Lidar_demo\processed\products_summary.json"
d = json.load(open(p, encoding="utf-8"))
d["acquisition_utc"] = {
    "note": "gps_time is vendor-adjusted epoch (1980-epoch conversion yields 1993, inconsistent with LINZ metadata 'acquired 2024 to present'); relative time deltas valid, absolute dates to be confirmed against survey logs.",
    "gps_time_raw_range": {"min_s": 422131598.7543452, "max_s": 423950546.02802277},
}
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=str)
print("patched")
