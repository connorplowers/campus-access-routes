"""Turn a raw OpenStreetMap (Overpass) download into the walking network the app uses.

Usage:  python3 tools/build_graph.py data/osm-raw.json data/campus-graph.js

Output is a JS file that sets window.CAMPUS = {nodes, segments, buildings}.
  nodes:     [[lat, lon], ...]                        every point on a walkway
  segments:  [{id, kind, name, nodes:[...], tags}]    walkway pieces between junctions
  buildings: [{id, name, outline:[[lat,lon]...], center:[lat,lon]}]
"""
import json
import os
import math
import sys
from collections import defaultdict

WALKABLE = {
    "footway", "path", "steps", "pedestrian", "living_street", "service",
    "residential", "track", "corridor", "unclassified", "tertiary", "cycleway",
}
NO_FOOT = {"no", "private"}


def main(src, dst):
    elements = json.load(open(src))["elements"]
    coords = {e["id"]: (e["lat"], e["lon"]) for e in elements if e["type"] == "node"}
    ways = [e for e in elements if e["type"] == "way"]

    walk_ways = []
    for w in ways:
        t = w.get("tags", {})
        if t.get("highway") not in WALKABLE:
            continue
        if t.get("foot") in NO_FOOT or t.get("access") in NO_FOOT and t.get("foot") not in ("yes", "designated"):
            continue
        if t.get("service") == "parking_aisle":
            continue
        walk_ways.append(w)

    # A node used by 2+ ways (or at a way's end) is a junction: segments are split there.
    use = defaultdict(int)
    for w in walk_ways:
        for i, n in enumerate(w["nodes"]):
            use[n] += 2 if i in (0, len(w["nodes"]) - 1) else 1

    node_index = {}
    nodes = []

    def idx(osm_id):
        if osm_id not in node_index:
            node_index[osm_id] = len(nodes)
            lat, lon = coords[osm_id]
            nodes.append([round(lat, 7), round(lon, 7)])
        return node_index[osm_id]

    keep_tags = ("surface", "incline", "wheelchair", "kerb", "width", "smoothness",
                 "footway", "sidewalk", "covered", "tunnel", "bridge", "step_count")
    segments = []
    for w in walk_ways:
        t = w.get("tags", {})
        ids = [n for n in w["nodes"] if n in coords]
        start = 0
        for i in range(1, len(ids)):
            if use[ids[i]] >= 2 or i == len(ids) - 1:
                piece = ids[start:i + 1]
                if len(piece) >= 2:
                    segments.append({
                        # way id + first node id: stays the same when the data is re-downloaded,
                        # so edits saved against it keep working.
                        "id": f"{w['id']}:{piece[0]}",
                        "kind": t["highway"],
                        "name": t.get("name", ""),
                        "nodes": [idx(n) for n in piece],
                        "tags": {k: t[k] for k in keep_tags if k in t},
                    })
                start = i

    # Name corrections checked against the HWS campus map (see tools/make_places.py).
    places_file = os.path.join(os.path.dirname(src), "campus-places.json")
    places = json.load(open(places_file)) if os.path.exists(places_file) else {}
    names, hide = places.get("names", {}), set(places.get("hide", []))
    also, keywords = places.get("also", {}), places.get("keywords", {})

    buildings = []
    for w in ways:
        t = w.get("tags", {})
        wid = str(w["id"])
        name = names.get(wid) or t.get("name")
        if "building" not in t or not name or t.get("name") in hide:
            continue
        outline = [coords[n] for n in w["nodes"] if n in coords]
        if len(outline) < 3:
            continue
        lat = sum(p[0] for p in outline) / len(outline)
        lon = sum(p[1] for p in outline) / len(outline)
        buildings.append({
            "id": f"w{w['id']}",
            "name": name,
            "also": also.get(wid, []),
            "keywords": keywords.get(wid, ""),
            "outline": [[round(a, 7), round(b, 7)] for a, b in outline],
            "center": [round(lat, 7), round(lon, 7)],
            "wheelchair": t.get("wheelchair", ""),
        })
    # Fields and open spaces: a point, given a small square outline so routing can reach it.
    for i, pt in enumerate(places.get("points", [])):
        la, lo, r = pt["lat"], pt["lon"], 0.00008
        buildings.append({
            "id": "p" + pt["name"].lower().replace(" ", "-").replace(".", ""), "name": pt["name"], "also": [], "keywords": "", "point": True,
            "outline": [[la - r, lo - r], [la - r, lo + r], [la + r, lo + r], [la + r, lo - r], [la - r, lo - r]],
            "center": [la, lo], "wheelchair": "",
        })
    buildings.sort(key=lambda b: b["name"].lower())

    # Entrance nodes, if anyone has mapped them.
    entrances = []
    for e in elements:
        t = e.get("tags", {})
        if e["type"] == "node" and "entrance" in t:
            entrances.append({"lat": e["lat"], "lon": e["lon"],
                              "wheelchair": t.get("wheelchair", ""), "kind": t["entrance"]})

    data = {"nodes": nodes, "segments": segments, "buildings": buildings, "entrances": entrances,
            "source": "OpenStreetMap contributors, ODbL"}
    with open(dst, "w") as f:
        f.write("// Generated by tools/build_graph.py from OpenStreetMap data (ODbL). Do not edit by hand.\n")
        f.write("window.CAMPUS = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    print(f"{len(nodes)} nodes, {len(segments)} segments, {len(buildings)} buildings, "
          f"{len(entrances)} entrances, steps={sum(s['kind'] == 'steps' for s in segments)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
