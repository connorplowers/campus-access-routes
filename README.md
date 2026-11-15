# Accessible Campus Routes (HWS prototype)

Step-free walking directions around Hobart and William Smith Colleges, built on OpenStreetMap data,
with live turn-by-turn navigation.

## Run it

```bash
python3 -m http.server 8765
```

Then open http://localhost:8765.

### Live location

Browsers only share location with pages served over **https** (or from `localhost` on the same computer).
To use live directions on a phone, host the folder on an https site, such as GitHub Pages or Netlify.
Opening the page over plain `http://<your-computer's-ip>` from a phone will not get a location.

The app only asks for location when you tap ◎, choose "Your location", or press Start.

### Testing navigation at a desk

Add `?simulate` to the address, e.g. `http://localhost:8765/?simulate`. A fake position walks along the
current route at 3× walking speed. In the browser console, `sim.off = 60` pushes it 60 m off the route
to test rerouting.

## Files

- `index.html`: the app (map, route finder, directions, live navigation, editor)
- `data/osm-raw.json`: OpenStreetMap download for the campus area
- `data/campus-graph.js`: walkway network built from it
- `tools/build_graph.py`: rebuilds the network: `python3 tools/build_graph.py data/osm-raw.json data/campus-graph.js`

## How it works

- **Routing:** walkways are split into segments at every junction. Step-free mode never uses a segment marked as
  stairs or blocked, and it treats steep and rough segments as longer (or skips them if those options are on).
  Routes go to user-marked accessible doors when a building has them, otherwise to the nearest path.
- **Live directions:** each GPS fix is matched to the nearest point on the route. The banner shows the next turn and
  the distance to it, spoken directions announce each turn (mute with 🔊), and the screen is kept awake where the
  browser allows it. Three fixes in a row more than ~25 m from the route trigger a new route from where you are.
- **Colors:** the HWS palette lives in CSS variables at the top of `index.html` (`--hws-purple`, `--hobart-orange`,
  `--ws-green`). The values are close approximations; swap in the official brand values if you have them.

## Known gaps

- OpenStreetMap marks only 4 staircases and no entrances on campus. Use "Fix the map" to mark stairs, slopes and
  accessible doors. Edits are saved in the browser; use "Save to file" / "Load from file" to share them.
- There's no slope data yet.
- Some campus buildings are missing or misspelled in OpenStreetMap. The app fixes the names it knows about,
  but the background map tiles still show the OSM spelling.
- Phone GPS is typically accurate to 5–15 m outdoors and worse near tall buildings, so "Now" prompts can be early or late.
