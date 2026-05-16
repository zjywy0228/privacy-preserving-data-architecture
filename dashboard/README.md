# Interactive Dashboard

A Vite + React + TypeScript data exploration interface for the Privacy-Preserving Data Architecture project.

## What's different from the static site

The static site at `docs/index.html` is zero-build, zero-dependency, and designed for
a non-technical reader who clicks a link once. This dashboard is for researchers who
want to explore the data interactively:

| Feature | Static site | This dashboard |
|---|---|---|
| Build step | None | `npm run build` |
| NIST table | Sort by column | Sort + keyword search + module filter |
| Benchmark | CSS bars | Recharts bar chart with hover tooltips |
| Leakage grid | Static cards | Overall pass-rate banner + per-category bars |
| Navigation | Scroll | Tab-based, no full-page reload |

## Quick start

```bash
cd dashboard
npm install
node scripts/sync-data.cjs   # copy JSON from docs/assets/data/ into public/data/
npm run dev                  # → http://localhost:5173
```

## Build for production

```bash
npm run build    # outputs to dashboard/dist/
```

## Data source

All data is served from `public/data/*.json`. These files mirror `docs/assets/data/`
and are kept in sync by `scripts/sync-data.cjs`. Re-run the script after Saturday's
module builds to refresh line counts, test counts, and benchmark timings.

## Stack

- **React 18** + **TypeScript** — component model, strict types
- **Vite** — dev server + build tool
- **Tailwind CSS** — utility-first styling (same classes as the static site)
- **Recharts** — FHE benchmark bar chart

## File structure

```
dashboard/
├── src/
│   ├── App.tsx                   # tab layout, data loading state
│   ├── main.tsx                  # React root
│   ├── types.ts                  # TypeScript interfaces (Module, NistRow, …)
│   ├── hooks/useData.ts          # parallel fetch with loading/error state
│   ├── components/
│   │   ├── ModuleGrid.tsx        # four module cards
│   │   ├── NistExplorer.tsx      # sortable + filterable NIST table
│   │   ├── LeakageGrid.tsx       # color-coded leakage categories
│   │   └── BenchmarkChart.tsx    # Recharts bar chart
│   └── styles/index.css
├── public/data/                  # JSON data (synced from docs/assets/data/)
├── scripts/sync-data.cjs         # data sync helper
└── README.md
```
