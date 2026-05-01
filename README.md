# Runway Trend Atlas

An interactive companion site for *Intelligent Fashion Forecasting: Computer Vision and Fashion Diffusion* (Kontaridis, 2026). Built to be the WGSN/EDITED-style demo the thesis describes — but for your dataset.

## What's in this folder

```
runway-trend-atlas/
├── index.html          # the dashboard (open this)
├── data.json           # all the data the dashboard reads (~415 KB)
├── chart.umd.min.js    # Chart.js (bundled — no internet needed)
├── preprocess.py       # the script that built data.json from your CSVs
└── README.md           # you're reading it
```

## Running it locally

You can't open `index.html` by double-clicking — modern browsers block local file access (CORS). Run a tiny web server instead:

```bash
cd runway-trend-atlas
python3 -m http.server 8000
```

Then open <http://localhost:8000> in your browser. That's it.

## Hosting it for free

Any of these work without a credit card. Pick whichever fits your workflow.

### GitHub Pages (recommended)

1. Create a new public GitHub repo, e.g. `runway-trend-atlas`.
2. Drop these four files into the repo root.
3. Repo → **Settings** → **Pages** → set Source to "Deploy from branch", Branch: `main` / `(root)`.
4. Wait ~30 seconds. Your site is live at `https://<your-username>.github.io/runway-trend-atlas/`.

### Netlify Drop

Go to <https://app.netlify.com/drop>, drag the whole folder onto the page. You get a live URL instantly. Free, no signup needed for a temporary URL.

### Cloudflare Pages, Vercel

Both work the same way — connect the GitHub repo and they'll auto-deploy on push.

## Swapping in your real ARIMA / Prophet / LSTM predictions

The dashboard ships with a **seasonal-naive forecast baseline** (predicted value at season *t* = actual value at season *t-2*, i.e., same season-type one year prior). This is the same benchmark you describe in the thesis Methods section. To replace it with your actual model outputs:

1. Open `data.json` in any text editor.
2. Find the `tier_forecasts` block (~line in the middle of the file). Schema:

   ```json
   "tier_forecasts": {
     "aesthetic": [
       {
         "1": [null, null, ..., 0.21, 0.23, 0.24, 0.22, 0.25],
         "2": [null, ..., 0.18, ...],
         ...
       },
       // one object per attribute index (0..14 for aesthetic, etc.)
     ],
     ...
   }
   ```

   Each tier's array has 21 elements (one per season). The first 16 should be `null` (training period). The last 5 are your model's predictions for SS2024 through FW2026.

3. Find `color_forecast`. Same idea — predicted L*, a*, b*, chroma values for the test seasons.

4. Optionally update `meta.forecast_method` from `"seasonal_naive_baseline"` to `"attention_lstm"` or whichever model's outputs you've plugged in.

If you'd rather regenerate everything from your model outputs as CSVs, edit `preprocess.py`:

- The function `forecast_series(series)` (about line 320) is what produces the seasonal-naive numbers. Replace it with `pd.read_csv` calls that pull from your trained-model output files.

Then re-run:
```bash
python3 preprocess.py
```

## Things you might want to change

| Where | What |
|---|---|
| `data.json` → `meta.note` | The dashboard reads this. Change it to credit yourself / your model when you swap forecasts. |
| `index.html` → `<title>` and `.masthead` block | Title, subtitle, author footer. |
| `index.html` → CSS variables at top of `<style>` | `--accent`, `--paper`, `--ink`, tier colors. The whole color story flows from these. |
| `preprocess.py` → `TIERS` dict | I assigned the 50 brands to tiers based on my reading of the thesis Table 1. Verify this is what you intended; some brands sit in fuzzy territory (e.g., Schiaparelli could arguably be Tier 1 not Tier 2). |
| `preprocess.py` → `*_LABELS` lists | I wrote human-readable labels for each CLIP class index based on common fashion vocabulary. If you have your exact original prompts from the CLIP setup, drop those in instead — the dashboard will show whatever strings you put there. |

## What's interactive

- **Section 1 — Explorer**: dropdown attribute group + attribute, toggle between tier breakdown and industry average, toggle forecast overlay.
- **Section 2 — Tier Drill-Down**: click any tier (left rail) to load its brand grid; click any brand to open a sparkline for that brand's trajectory on the currently-selected attribute.
- **Section 3 — Color Atlas**: click any season column in the strip to load its full 5-color breakdown with LAB coordinates and percentages.
- **Section 4 — Forecast Lab**: cards are static (one per test season). The grid auto-flows based on width.
- **Chart legend**: click any tier in the legend to mute/un-mute it on the chart.

## Known limitations

- **Forecast errors (MAE)** in Section 4 are computed from the seasonal-naive baseline against your color time series. They're real numbers, but they're benchmark numbers, not your model's. They'll change when you swap in real predictions.
- **No mobile-first design**: the layout collapses sensibly under 900px wide, but the editorial typography is meant for desktop reading.
- **No URL state**: navigating away loses your selected attribute/tier/season. If you want shareable deep-links, that's a half-day's work to add — happy to do it on request.

---

Built from `clip_by_season.csv` and `color_by_image.csv`. Aesthetic inspired by editorial publications more than dashboards — the goal was for someone landing on this for the first time to feel they're reading a research issue, not poking at a tool.
