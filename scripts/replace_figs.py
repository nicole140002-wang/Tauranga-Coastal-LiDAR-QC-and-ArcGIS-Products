# -*- coding: utf-8 -*-
"""
Replace base64 figures with ArcGIS screenshot references, matched by caption.
"""
import re, os

HTML = r"D:\GIS_Portfolio\Lidar_demo\images\linz_3dcm_demo_report.html"

with open(HTML, "r", encoding="utf-8") as f:
    html = f.read()

# Caption substring -> screenshot filename (in same images/ folder)
cap_to_img = [
    ("All 3DCM classes present", "01_port_wharf_classification_3d.png"),
    ("Every tile delivers 24.6", "14_density_1m.png"),
    ("True colour from LiDAR RGB", "12_rgb_1m_truecolor.png"),
    ("Delivered density (log)", "14_density_1m.png"),
    ("Mean intensity", "13_intensity_1m.png"),
    ("DSM — highest return", "06_dsm_overlay_lidar_ve1.png"),
    ("Ground (class 2) + seabed", "17_land_seabed_dtm.png"),
    ("Intertidal band", "19_intertidal_zone.png"),
    ("Raw, non-withheld returns", "16_profile_graph.png"),
]

# Replace each <figure><img src="data:..."><figcaption>...</figcaption></figure>
# We process figure by figure. Pattern: <figure><img src="data:image/png;base64,...."></figure>
# But the img tag may have other attributes. Match the whole img tag.
fig_re = re.compile(
    r'<figure><img src="data:image/png;base64,[^"]*"[^>]*></figure>',
    re.DOTALL,
)

# We need to process figures in document order, matching captions in order.
# Find all figure blocks with their following caption.
# Simpler: split html by <figure, process chunks.

parts = html.split("<figure>")
out = [parts[0]]
for i, chunk in enumerate(parts[1:], 1):
    # chunk ends at </figure>
    if "</figure>" not in chunk:
        out.append("<figure>" + chunk)
        continue
    fig_end = chunk.index("</figure>") + len("</figure>")
    fig_html = "<figure>" + chunk[:fig_end]
    rest = chunk[fig_end:]
    # find caption inside
    cap_m = re.search(r'<figcaption>(.*?)</figcaption>', fig_html, re.DOTALL)
    cap_text = cap_m.group(1) if cap_m else ""
    # match
    new_img = None
    for cap_substr, img_fn in cap_to_img:
        if cap_substr in cap_text:
            new_img = img_fn
            break
    if new_img:
        # replace the img tag
        new_fig = re.sub(
            r'<img src="data:image/png;base64,[^"]*"[^>]*>',
            f'<img src="{new_img}" style="max-width:100%;border:1px solid #d0d7de;border-radius:4px;">',
            fig_html,
        )
        out.append(new_fig + rest)
        print(f"fig {i}: {cap_text[:60]}... -> {new_img}")
    else:
        out.append(fig_html + rest)
        print(f"fig {i}: NO MATCH for {cap_text[:60]}")

new_html = "".join(out)
with open(HTML, "w", encoding="utf-8") as f:
    f.write(new_html)
print("\ndone. new size:", len(new_html), "bytes")
