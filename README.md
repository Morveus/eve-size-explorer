# EVE Size Explorer

A visual, interactive tool for comparing EVE Online ships and structures at true relative scale — from the 4-meter Capsule to the 300-kilometer Keepstar.

Built for the EVE community. All ship renders courtesy of CCP's image server.

---

## How it works

Every ship and structure in EVE Online has a **radius** (in meters) defined in the game data. This tool fetches that data, lays out all 420+ hulls side by side on an infinite pannable canvas, and renders them at **correct relative scale**.

Zoom out to see a Titan dwarf a fleet of frigates. Zoom in to compare assault frigates head to head. The grid and ruler adapt as you navigate so you always know what you're looking at.

### Controls

| Input | Action |
|---|---|
| Drag (mouse / finger) | Pan the canvas |
| Scroll wheel / Pinch | Zoom in & out (centered on cursor) |
| `+` / `-` | Zoom in / out |
| Arrow keys | Pan |
| `0` | Fit everything on screen |
| Hover | Ship details tooltip |

Filter by ship group, search by name, sort by size or alphabetically — all in real time.

---

## Run it

### Docker (recommended)

```bash
docker run -d -p 8080:80 morveus/eve-size-explorer
```

Then open [http://localhost:8080](http://localhost:8080).

### Static files

Serve the project root with any HTTP server:

```bash
python3 -m http.server 8080
```

No build step, no dependencies, no framework. One HTML file, one JSON data file.

---

## Data pipeline

The `scripts/` directory contains the pipeline that generates `data/ships.json`:

```
1. fetch_sde.py      → Downloads the Fuzzwork SQLite SDE conversion
                        Extracts all published ships & structures (categoryID 6 & 65)

2. enrich_radius.py  → Calls ESI /universe/types/{id} for each hull
                        Adds the radius field (meters) to each entry

3. download_renders.py → Downloads 1024px renders from images.evetech.net
                          (optional — the viewer loads them directly from CCP)
```

### Rebuilding the data

```bash
# Requires Python 3.10+
python3 scripts/fetch_sde.py
python3 scripts/enrich_radius.py
```

The SDE download is ~130 MB compressed. The enrichment step makes ~420 ESI API calls and takes a couple of minutes.

---

## What's in the box

```
index.html              → The entire viewer (HTML + CSS + JS, no dependencies)
data/ships.json         → 420+ ships with typeID, name, group, radius, mass, volume
scripts/fetch_sde.py    → SDE download & extraction
scripts/enrich_radius.py → ESI radius enrichment
scripts/download_renders.py → Batch render downloader
Dockerfile              → nginx:alpine serving the static files
```

---

## Size reference

Some notable sizes (diameter = radius x 2):

| Ship | Diameter |
|---|---|
| Capsule | 4 m |
| Rifter | 62 m |
| Drake | 526 m |
| Rorqual | 2.2 km |
| Avatar (Titan) | 13.6 km |
| Keepstar (Citadel) | 300 km |

---

## Credits

- **CCP Games** — EVE Online, the Static Data Export, the ESI API, and the image server
- **Steve Ronuken / Fuzzwork** — SQLite SDE conversion
- EVE Online and all related assets are property of CCP hf.

---

*Not affiliated with or endorsed by CCP Games. EVE Online and all associated logos and designs are the intellectual property of CCP hf.*
