# Runway Trend Atlas

An interactive companion site for *Intelligent Fashion Forecasting: Computer Vision and Fashion Diffusion* (Kontaridis, 2026). Built to be the WGSN/EDITED-style demo.


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
