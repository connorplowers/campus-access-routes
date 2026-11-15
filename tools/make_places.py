"""Build data/campus-places.json: building names checked against the official HWS campus map.

The HWS map (hws.edu/campus-map.aspx) was used as the reference for names. Its pins were matched to
OpenStreetMap building outlines by position. This script holds the result of that check, so it can be
reviewed and edited by hand. Run it after editing, then rebuild the graph:

    python3 tools/make_places.py
    python3 tools/build_graph.py data/osm-raw.json data/campus-graph.js
"""
import json

# Display name for each building, keyed by OpenStreetMap way id.
NAMES = {
    # OSM label wrong or out of date
    578630748: "Bristol Gymnasium",            # OSM said "Winn-Sealy Gymnasium"
    578630745: "Caird Hall",                   # OSM "Caird" is the residence hall, not the sports center
    578630724: "Adams Intercultural Center",   # OSM "Intercultural Affairs House"
    578632964: "Community Engagement House (McDaniels House)",  # OSM "Hope House"
    825974977: "House of Political Engagement",                  # OSM "Active House"
    578632963: "Light House (Durfee House)",                     # OSM "Geneva 2020"
    578632968: "Mindful Living House",                           # OSM "Lacrosse the Nation"
    825974528: "ORAP House",                                     # OSM "Cultural Connections"
    825974938: "Pride House (Hillcrest House)",                  # OSM "Farm House"
    825975128: "Gloria Robinson Lowry House (Sill House)",       # OSM "Bampton House"
    578632969: "Office of Marketing and Communications",         # OSM "Title IX & Compliance"
    578630737: "Rosenberg Hall / Napier Classroom Center",       # OSM "Napier"
    578634607: "Salisbury Center at Trinity Hall",               # OSM "Trinity Hall"
    # spelling and full names
    578630735: "Gulick Hall", 670837860: "Medbery Hall", 578630728: "Hirshson Hall", 578630727: "Miller House",
    578630744: "McCormick House", 578630751: "Durfee Hall", 578630747: "Emerson Hall", 1096398317: "Demarest Hall",
    578630738: "Lansing Hall", 578632970: "Admissions Center", 825974586: "Abbe Center for Jewish Life",
    825974520: "Carr McGuire House (Office for Advancement)", 578634609: "Chaplain's Residence",
    578632965: "Global Perspectives House", 825975098: "Creative Arts House (Stewardson House)",
    578630749: "Sherrill Hall & College Store", 578630746: "de Cordova Hall", 825974355: "Barn",
    825974933: "Robert A. Bristol Field House", 578627077: "Scandling Campus Center",
    578627078: "Warren Hunting Smith Library", 578630740: "Bozzuto Boathouse and Dock",
    # unnamed in OSM: outline exists, name from the HWS map
    1096402713: "Winn-Seeley Gymnasium", 1096402705: "Caird Center for Sports and Recreation",
    825974328: "Houghton House", 825974489: "Goldstein Family Carriage House", 1096780063: "Henry House",
    825974548: "Katherine D. Elliott Studio Arts Center", 825974602: "Richard S. Perkin Observatory",
    825974731: "Business Office", 825974653: "Bampton House of Leadership and Values",
    825975015: "House of Language Studies", 825975023: "Jackson Hall", 825974800: "Muslim Life & Culture House",
    825974367: "Potter Hall", 825974290: "Rees Hall", 825974574: "Village at Odell's Pond",
    825974579: "Wellness & Recreation House (Farm House)", 825975076: "Writers' House (Trowbridge House)",
    825974896: "Counseling Center", 1096389318: "Harris House", 825974319: "Hubbs Health Center",
    825974512: "LGBTQ+ Resource Center", 1096822145: "Thomas B. Poole '61 and Family Sports Dome",
    1096780061: "Kappa Sigma", 1096780062: "Kappa Alpha", 1096780060: "Delta Chi", 1146044402: "Phi Sigma Kappa",
}

# OSM buildings near campus that aren't college buildings.
HIDE = ["Arby's", "McDonald's", "Canandaigua National Bank & Trust", "Triana and Triana, D.D.S.", "First Presbyterian Church"]

# Offices, rooms and other names inside a building (from the HWS map), so searching for them finds the building.
ALSO = {
    578627078: ["Melly Academic Center", "Rosensweig Learning Commons", "Center for Teaching and Learning",
                "Office of Institutional Research", "IT Services", "Au Bon Pain"],
    578627077: ["SAGA Dining", "The Café", "Faculty Dining", "Post Office", "Print Services", "Student Activities",
                "WEOS-FM", "Residential Education"],
    578630733: ["The Cellar Pub", "Office of the Provost"],
    1096398317: ["Fisher Center", "St. John's Chapel", "Blackwell Room", "Saint Mark's Tower", "Office of the Registrar"],
    578630738: ["Albright Auditorium"],
    578634607: ["Center for Global Education"],
    578632972: ["Center for Community Engagement and Service Learning"],
    578632973: ["Finger Lakes Community Development Center"],
    578632971: ["Title IX Programs and Compliance Office"],
    578632970: ["Office of Financial Aid"],
    578630724: ["Intercultural Affairs Center", "Academic Opportunity Programs"],
    578630730: ["International Student Affairs", "Student Affairs"],
    578630734: ["Building and Grounds"],
    825974328: ["Davis Gallery"],
    578630726: ["Blackwell Honors & Heritage House"],
    578630748: ["Bristol Pool"],
    1096402705: ["Elliott Varsity House"],
    1096389318: ["Conferences & Events"],
    825974800: ["Residential Education"],
    825974319: ["Alcohol and Other Drug Education"],
}

# Search words that aren't names.
KEYWORDS = {
    578627078: "library books study whs", 578627077: "student center dining food mail",
    578630723: "theater theatre music dance performing arts", 1096402713: "gym",
    578630748: "gym pool swimming basketball", 825974933: "gym track field house athletics",
    1096402705: "gym fitness sports recreation weights", 578630734: "security police help",
    578632970: "visit tours", 578630749: "bookstore books", 578630740: "rowing lake boathouse",
    825974319: "health nurse doctor clinic", 825974896: "counseling mental health",
}

# Open spaces and fields from the HWS map. OSM has no building outline for these, so they are points.
POINTS = [
    {"name": "Hobart Quadrangle", "lat": 42.858280, "lon": -76.983251},
    {"name": "William Smith Green", "lat": 42.857351, "lon": -76.985180},
    {"name": "Cozzens Memorial Field", "lat": 42.858784, "lon": -76.987302},
    {"name": "McCooey Memorial Field", "lat": 42.857530, "lon": -76.989803},
    {"name": "William Smith Field", "lat": 42.858494, "lon": -76.990567},
    {"name": "Boswell Field", "lat": 42.858248, "lon": -76.991712},
    {"name": "St. Clair Field", "lat": 42.853648, "lon": -76.991581},
    {"name": "Tennis Center", "lat": 42.858320, "lon": -76.988362},
    {"name": "Sunken Gardens", "lat": 42.850870, "lon": -76.983498},
]

if __name__ == "__main__":
    out = {
        "_about": "Generated by tools/make_places.py. Building names checked against the official HWS campus map.",
        "names": {str(k): v for k, v in NAMES.items()},
        "hide": HIDE,
        "also": {str(k): v for k, v in ALSO.items()},
        "keywords": {str(k): v for k, v in KEYWORDS.items()},
        "points": POINTS,
    }
    with open("data/campus-places.json", "w") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"{len(NAMES)} names, {len(POINTS)} points")
