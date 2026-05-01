"""
Build a single data.json from the uploaded CSVs.
Output schema is documented at the top of the file.
"""
import csv, json, statistics
from collections import defaultdict

UPLOADS = "/mnt/user-data/uploads"

# ============ TIER MAPPING ============
# Based on the thesis Table 1 (50 brands, 5 tiers).
# Tier 1: French houses
# Tier 2: Italian houses
# Tier 3: British houses
# Tier 4: Belgian/Avant-Garde
# Tier 5: Contemporary luxury
TIERS = {
    # Tier 1 - French houses
    "chanel": 1, "dior": 1, "louis-vuitton": 1, "hermes": 1, "celine": 1,
    "saint-laurent": 1, "givenchy": 1, "lanvin": 1, "chloe": 1, "balenciaga": 1,
    # Tier 2 - Italian houses
    "gucci": 2, "prada": 2, "versace": 2, "fendi": 2, "valentino": 2,
    "dolce-gabbana": 2, "miu-miu": 2, "bottega-veneta": 2, "emporio-armani": 2,
    "max-mara": 2, "missoni": 2, "etro": 2, "alberta-ferretti": 2, "moschino": 2,
    "schiaparelli": 2,
    # Tier 3 - British houses
    "burberry": 3, "alexander-mcqueen": 3, "vivienne-westwood": 3,
    "stella-mccartney": 3, "jw-anderson": 3, "erdem": 3, "molly-goddard": 3,
    "richard-quinn": 3, "roksanda": 3, "simone-rocha": 3,
    # Tier 4 - Belgian/Avant-Garde
    "maison-margiela": 4, "dries-van-noten": 4, "ann-demeulemeester": 4,
    "raf-simons": 4, "rick-owens": 4, "comme-des-garcons": 4,
    "lemaire": 4, "sacai": 4,
    # Tier 5 - Contemporary luxury
    "loewe": 5, "marni": 5, "acne-studios": 5, "altuzarra": 5,
    "isabel-marant": 5, "jacquemus": 5, "proenza-schouler": 5,
}

# Pretty designer names
def pretty(d):
    overrides = {
        "dolce-gabbana": "Dolce & Gabbana", "jw-anderson": "JW Anderson",
        "comme-des-garcons": "Comme des Garçons", "chloe": "Chloé",
        "celine": "Céline", "loewe": "Loewe", "hermes": "Hermès",
        "max-mara": "Max Mara",
    }
    if d in overrides: return overrides[d]
    return " ".join(w.capitalize() for w in d.split("-"))

TIER_NAMES = {
    1: "Tier 1 — French Houses",
    2: "Tier 2 — Italian Houses",
    3: "Tier 3 — British Houses",
    4: "Tier 4 — Belgian / Avant-Garde",
    5: "Tier 5 — Contemporary Luxury",
}
TIER_COLORS = {1: "#1f3a5f", 2: "#7d3c2e", 3: "#5a7d3a", 4: "#4a3a5a", 5: "#a07a3a"}

# ============ ATTRIBUTE LABELS (from thesis CLIP prompts) ============
# clip_by_season has columns like silhouette_freq_0..11 etc.
# We need readable labels for each index.
SILHOUETTE_LABELS = [
    "Tailored / boxy H-line", "Relaxed / unstructured", "Voluminous / dramatic",
    "Slim / pencil", "Bell / A-line", "Mermaid / fitted hourglass",
    "Cocoon / oval", "Empire / high-waisted", "Asymmetric / draped",
    "Oversized / elongated", "Trapeze / swing", "Fit-and-flare"
]
AESTHETIC_LABELS = [
    "Minimalist / quiet luxury", "Maximalist / eclectic", "Romantic / feminine",
    "Gothic / dark", "Y2K / nostalgic", "Futuristic / sculptural",
    "Bohemian / artisanal", "Sportswear / utility", "Tailored / professional",
    "Streetwear / urban", "Folk / heritage", "Glam / evening",
    "Workwear / military", "Punk / subversive", "Pastoral / cottagecore"
]
DESIGN_ELEMENT_LABELS = [
    "Solid plain", "Stripes", "Floral print", "Animal print",
    "Geometric pattern", "Bold graphic print", "Embellished / sequined",
    "Lace / sheer", "Embroidered", "Color-blocked", "Plaid / check", "Tonal texture"
]
LENGTH_LABELS = [
    "Mini / above mid-thigh", "Short / above knee", "Knee-length",
    "Midi / mid-calf", "Maxi / floor-length", "Trousers / pants",
    "Shorts", "Longline coat / extended"
]
FORMALITY_LABELS = [
    "Casual / day", "Streetwear", "Smart day", "Business / professional",
    "Cocktail / party", "Evening / formal"
]

ATTR_GROUPS = {
    "silhouette": SILHOUETTE_LABELS,
    "aesthetic": AESTHETIC_LABELS,
    "design_element": DESIGN_ELEMENT_LABELS,
    "length": LENGTH_LABELS,
    "formality": FORMALITY_LABELS,
}

# ============ SEASON ORDERING ============
def season_to_sort(season):
    # 'fall-winter-2016' -> (2016, 1); 'spring-summer-2017' -> (2017, 0)
    parts = season.split("-")
    year = int(parts[-1])
    sub = 0 if parts[0] == "spring" else 1
    return (year, sub)

def season_to_label(season):
    parts = season.split("-")
    year = parts[-1][-2:]
    prefix = "SS" if parts[0] == "spring" else "FW"
    return f"{prefix}{year}"

# ============ LOAD CLIP_BY_SEASON ============
print("Loading clip_by_season.csv...")
clip_rows = []
with open(f"{UPLOADS}/clip_by_season.csv") as f:
    r = csv.DictReader(f)
    for row in r:
        clip_rows.append(row)

# ordered seasons
all_seasons = sorted({r["season"] for r in clip_rows}, key=season_to_sort)
season_labels = [season_to_label(s) for s in all_seasons]
print(f"  {len(clip_rows)} brand-season rows, {len(all_seasons)} seasons")

# ============ COMPUTE TIER-LEVEL FREQUENCIES ============
# For each (tier, season, attribute_group, label_idx) -> weighted mean frequency
# Weighted by n_looks within each brand-season.
print("Computing tier-level aggregates...")

def attr_n_classes(group):
    return len(ATTR_GROUPS[group])

# tier_data[group][label_idx][tier][season_idx] = freq
tier_data = {}
for group, labels in ATTR_GROUPS.items():
    n_classes = len(labels)
    tier_data[group] = []
    for cls in range(n_classes):
        cls_data = {t: [None]*len(all_seasons) for t in [1,2,3,4,5]}
        # collect for each tier-season
        bucket = defaultdict(lambda: {"sum": 0.0, "n": 0})
        for row in clip_rows:
            d = row["designer"]
            if d not in TIERS: continue
            t = TIERS[d]
            s = row["season"]
            n_looks = int(row["n_looks"])
            freq = float(row[f"{group}_freq_{cls}"])
            bucket[(t, s)]["sum"] += freq * n_looks
            bucket[(t, s)]["n"] += n_looks
        for (t, s), agg in bucket.items():
            if agg["n"] > 0:
                cls_data[t][all_seasons.index(s)] = round(agg["sum"]/agg["n"], 4)
        tier_data[group].append(cls_data)

# ============ PER-BRAND FREQUENCIES (for drill-down) ============
print("Computing per-brand series...")
brand_data = {}
for group, labels in ATTR_GROUPS.items():
    brand_data[group] = []
    for cls in range(len(labels)):
        per_brand = {}
        for row in clip_rows:
            d = row["designer"]
            if d not in TIERS: continue
            if d not in per_brand:
                per_brand[d] = [None]*len(all_seasons)
            per_brand[d][all_seasons.index(row["season"])] = round(
                float(row[f"{group}_freq_{cls}"]), 4
            )
        brand_data[group].append(per_brand)

# ============ COLOR DATA: per-season palette + LAB time series ============
print("Loading color_by_image.csv (this is large)...")
# We want, per (designer, season): aggregate top-5 palette + mean L,a,b
# Approach: weighted mean of the 5 cluster centroids per look, summed across looks

# For the aggregated palette per season (not per brand): collect ALL colors
# from ALL looks in that season, weighted by their cluster weights.
# Then re-cluster down to 5 representative colors. That's expensive in pure python.
# Simpler: just take, for each season, the dominant color of each look (color1)
# and compute mean L,a,b of those dominant colors. Plus a sampled palette strip.

# Simpler still: compute mean L*, mean chroma, mean a*, mean b* per season
# (matches your Figure 4). And build a palette strip of representative colors.

color_season_lab = {s: {"L": [], "a": [], "b": [], "chroma": []} for s in all_seasons}
# For palette strip: collect a sample of (weight, hex) per season
color_season_palette_raw = {s: [] for s in all_seasons}

with open(f"{UPLOADS}/color_by_image.csv") as f:
    r = csv.DictReader(f)
    count = 0
    for row in r:
        s = row["season"]
        if s not in color_season_lab: continue
        # Use all 5 cluster colors weighted by their weight
        for k in range(1, 6):
            w = float(row[f"color{k}_weight"])
            L = float(row[f"color{k}_L"])
            a = float(row[f"color{k}_a"])
            b = float(row[f"color{k}_b"])
            hex_ = row[f"color{k}_hex"]
            chroma = (a*a + b*b) ** 0.5
            # weight contributions for season-level mean
            color_season_lab[s]["L"].append((L, w))
            color_season_lab[s]["a"].append((a, w))
            color_season_lab[s]["b"].append((b, w))
            color_season_lab[s]["chroma"].append((chroma, w))
            color_season_palette_raw[s].append((w, L, a, b, hex_))
        count += 1
    print(f"  Processed {count} look-rows")

def weighted_mean(pairs):
    if not pairs: return None
    sw = sum(w for _, w in pairs)
    if sw == 0: return None
    return round(sum(v*w for v,w in pairs) / sw, 2)

color_series = {
    "L": [weighted_mean(color_season_lab[s]["L"]) for s in all_seasons],
    "a": [weighted_mean(color_season_lab[s]["a"]) for s in all_seasons],
    "b": [weighted_mean(color_season_lab[s]["b"]) for s in all_seasons],
    "chroma": [weighted_mean(color_season_lab[s]["chroma"]) for s in all_seasons],
}

# ============ PALETTE STRIP: representative 5 colors per season ============
# Cluster the (L,a,b) points per season into 5 representative colors using
# a simple weighted k-means in Python.
print("Building per-season palette strip...")

import random
random.seed(42)

def lab_to_rgb_hex(L, a, b):
    # Convert Lab to sRGB hex (standard formula, D65 illuminant).
    # CIE Lab -> XYZ
    fy = (L + 16) / 116
    fx = a/500 + fy
    fz = fy - b/200
    eps = 0.008856
    kappa = 903.3
    def finv(t):
        return t**3 if t**3 > eps else (116*t - 16)/kappa
    Xn, Yn, Zn = 0.95047, 1.0, 1.08883
    X = Xn * finv(fx)
    Y = Yn * finv(fy)
    Z = Zn * finv(fz)
    # XYZ -> sRGB linear
    r =  3.2406*X - 1.5372*Y - 0.4986*Z
    g = -0.9689*X + 1.8758*Y + 0.0415*Z
    bl = 0.0557*X - 0.2040*Y + 1.0570*Z
    def gamma(c):
        c = max(0, min(1, c))
        return 12.92*c if c <= 0.0031308 else 1.055*(c**(1/2.4)) - 0.055
    rgb = [gamma(r), gamma(g), gamma(bl)]
    rgb = [int(round(max(0, min(1, c))*255)) for c in rgb]
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def kmeans_lab(points, k=5, iters=20):
    # points: list of (weight, L, a, b, hex) — we ignore hex and recompute
    pts4 = [(p[0], p[1], p[2], p[3]) for p in points]
    if len(pts4) <= k:
        return pts4
    import numpy as np
    from sklearn.cluster import KMeans
    arr = np.array([(L, a, b) for (_, L, a, b) in pts4])
    weights = np.array([p[0] for p in pts4])
    km = KMeans(n_clusters=k, n_init=5, max_iter=iters, random_state=42)
    labels = km.fit_predict(arr, sample_weight=weights)
    result = []
    for i in range(k):
        mask = labels == i
        total_w = float(weights[mask].sum())
        if total_w > 0:
            cL, ca, cb = km.cluster_centers_[i]
            result.append((total_w, float(cL), float(ca), float(cb)))
    return sorted(result, key=lambda x: -x[0])

palette_strip = {}
for s in all_seasons:
    pts = color_season_palette_raw[s]
    if not pts:
        palette_strip[s] = []
        continue
    # Subsample to keep computation fast
    if len(pts) > 5000:
        pts = random.sample(pts, 5000)
    centroids = kmeans_lab(pts, k=5, iters=15)
    palette_strip[s] = [
        {"hex": lab_to_rgb_hex(L, a, b), "L": round(L,1), "a": round(a,1), "b": round(b,1), "weight": round(w,2)}
        for (w, L, a, b) in centroids
    ]
    print(f"  {s}: {[c['hex'] for c in palette_strip[s]]}")

# ============ FORECAST PLACEHOLDER ============
# We don't have your actual ARIMA/Prophet/LSTM outputs. We compute a
# seasonal-naive forecast: predicted[s] = actual[s - 2] (one year prior).
# This is the same baseline you described in the thesis.
# Test seasons: SS2024..FW2026 (last 6).
print("Computing seasonal-naive forecast baseline...")

train_test_split = 16  # last 5-6 seasons reserved for "test"

def forecast_series(series):
    forecast = [None] * len(series)
    for i in range(train_test_split, len(series)):
        # take value 2 seasons ago (same season-type, prior year)
        if i >= 2 and series[i-2] is not None:
            forecast[i] = series[i-2]
    return forecast

forecasts = {"silhouette": [], "aesthetic": [], "design_element": [], "length": [], "formality": []}
for group in forecasts:
    for cls in range(len(ATTR_GROUPS[group])):
        per_tier = {}
        for t in [1,2,3,4,5]:
            actual = tier_data[group][cls][t]
            per_tier[t] = forecast_series(actual)
        forecasts[group].append(per_tier)

color_forecast = {
    "L": forecast_series(color_series["L"]),
    "a": forecast_series(color_series["a"]),
    "b": forecast_series(color_series["b"]),
    "chroma": forecast_series(color_series["chroma"]),
}

# ============ ASSEMBLE OUTPUT ============
print("Assembling data.json...")
output = {
    "meta": {
        "n_brands": 50, "n_seasons": len(all_seasons),
        "n_looks": 48534, "season_range": "FW2016 - FW2026",
        "test_seasons_start_idx": train_test_split,
        "forecast_method": "seasonal_naive_baseline",
        "note": "Forecast values are a seasonal-naive baseline (value from same season-type one year prior). Replace with your trained model outputs to use the real ARIMA/Prophet/LSTM forecasts.",
    },
    "seasons": all_seasons,
    "season_labels": season_labels,
    "tiers": [
        {"id": t, "name": TIER_NAMES[t], "color": TIER_COLORS[t],
         "brands": sorted([d for d, ti in TIERS.items() if ti == t],
                          key=lambda x: pretty(x))}
        for t in [1,2,3,4,5]
    ],
    "brand_pretty": {d: pretty(d) for d in TIERS},
    "attribute_groups": {
        "silhouette":     {"name": "Silhouette",      "labels": SILHOUETTE_LABELS},
        "aesthetic":      {"name": "Aesthetic",       "labels": AESTHETIC_LABELS},
        "design_element": {"name": "Design Element",  "labels": DESIGN_ELEMENT_LABELS},
        "length":         {"name": "Length / Hemline","labels": LENGTH_LABELS},
        "formality":      {"name": "Formality",       "labels": FORMALITY_LABELS},
    },
    "tier_series": tier_data,
    "brand_series": brand_data,
    "tier_forecasts": forecasts,
    "color_series": color_series,
    "color_forecast": color_forecast,
    "palette_strip": palette_strip,
}

import json
with open("data.json", "w") as f:
    json.dump(output, f, separators=(",", ":"))
import os
print(f"Done. data.json size: {os.path.getsize('data.json')/1024:.1f} KB")
