"""
ONE SCRIPT TO PULL EVERYTHING.
Run: pip install requests
Then: python setup.py

Creates data/ folder with all files needed for index.html.
"""
import requests, json, os, time

OUT = "data"
os.makedirs(OUT, exist_ok=True)

print("="*60)
print("STL TORNADO MAP — DATA SETUP")
print("="*60)

# ============================================================
# 1. FEMA DATA (Owners + Renters by ZIP)
# ============================================================
print("\n[1/6] FEMA data...")
DISASTER = 4877
ZIPS = [
    "63101","63102","63103","63104","63105","63106","63107","63108",
    "63109","63110","63111","63112","63113","63114","63115","63116",
    "63117","63118","63119","63120","63121","63122","63123","63124",
    "63125","63126","63127","63128","63129","63130","63131","63132",
    "63133","63134","63135","63136","63137","63138","63139","63140",
    "63141","63143","63144","63145","63146","63147",
]

for dataset, key in [
    ("HousingAssistanceOwners", "fema_owners"),
    ("HousingAssistanceRenters", "fema_renters"),
]:
    short = key.split("_")[1]
    print(f"  Pulling {short}...")
    all_records = []
    try:
        r = requests.get(
            f"https://www.fema.gov/api/open/v2/{dataset}",
            params={"$filter": f"disasterNumber eq {DISASTER}", "$top": 10000, "$orderby": "zipCode"},
            timeout=60
        )
        r.raise_for_status()
        records = r.json().get(dataset, [])
        if records:
            with open(f"{OUT}/{key}.json", "w") as f:
                json.dump(records, f, indent=2)
            print(f"    Got {len(records)} records")
        else:
            print(f"    No records returned")
    except Exception as e:
        print(f"    Error: {e}")
    time.sleep(0.5)

# ============================================================
# 2. ZIP BOUNDARIES (from GitHub OpenDataDE)
# ============================================================
print("\n[2/6] ZIP boundaries...")
KEEP = {
    '63101','63102','63103','63104','63105','63106','63107','63108',
    '63109','63110','63111','63112','63113','63115','63116','63117',
    '63118','63119','63120','63121','63130','63132','63133','63134',
    '63135','63136','63137','63138','63139','63143','63144','63147',
}
try:
    r = requests.get("https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/mo_missouri_zip_codes_geo.min.json", timeout=60)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", [])
    # Find ZIP field
    sample = feats[0]["properties"]
    zf = None
    for k, v in sample.items():
        if str(v).startswith("6") and len(str(v)) == 5:
            zf = k; break
    stl = [f for f in feats if str(f["properties"].get(zf, "")) in KEEP]
    for f in stl:
        f["properties"] = {"zip": str(f["properties"][zf])}
    with open(f"{OUT}/zip_boundaries.geojson", "w") as fp:
        json.dump({"type": "FeatureCollection", "features": stl}, fp)
    print(f"  Got {len(stl)} ZIP boundaries")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 3. NEIGHBORHOOD BOUNDARIES (from SLU OpenGIS GitHub)
# ============================================================
print("\n[3/6] Neighborhood boundaries...")
try:
    r = requests.get("https://raw.githubusercontent.com/slu-openGIS/STL_BOUNDARY_Nhood/master/data/STL_BOUNDARY_Nhood.geojson", timeout=30)
    r.raise_for_status()
    data = r.json()
    for f in data.get("features", []):
        p = f.get("properties", {})
        name = p.get("NHD_NAME", p.get("Name", ""))
        num = p.get("NHD_NUM", "")
        f["properties"] = {"name": name, "num": num}
    with open(f"{OUT}/neighborhoods.geojson", "w") as fp:
        json.dump(data, fp)
    print(f"  Got {len(data['features'])} neighborhoods")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 4. GEOCODE LANDMARKS
# ============================================================
print("\n[4/6] Geocoding landmarks...")
PLACES = [
    {"name": "Vashon High School", "addr": "3035 Cass Ave, St. Louis, MO 63106", "type": "school", "desc": "Historic Black high school (1927). In tornado damage zone.", "src": "https://en.wikipedia.org/wiki/Vashon_High_School"},
    {"name": "Sumner High School", "addr": "4248 Cottage Ave, St. Louis, MO 63113", "type": "school", "desc": "First Black high school west of the Mississippi (1875). Used as FEMA DRC.", "src": "https://en.wikipedia.org/wiki/Charles_H._Sumner_High_School"},
    {"name": "Harris-Stowe State University", "addr": "3026 Laclede Ave, St. Louis, MO 63103", "type": "school", "desc": "HBCU. Near tornado path.", "src": "https://en.wikipedia.org/wiki/Harris%E2%80%93Stowe_State_University"},
    {"name": "Fontbonne University", "addr": "6800 Wydown Blvd, Clayton, MO 63105", "type": "school", "desc": "EF1-EF2 campus damage. Power poles snapped.", "src": "https://www.weather.gov/lsx/05_16_2025"},
    {"name": "Washington University", "addr": "1 Brookings Dr, St. Louis, MO 63130", "type": "school", "desc": "Trees/fences blown over. MetroLink overhead power damaged.", "src": "https://en.wikipedia.org/wiki/2025_St._Louis_tornado"},
    {"name": "Centennial Christian Church", "addr": "4950 Fountain Ave, St. Louis, MO 63113", "type": "church", "desc": "Complete roof collapse trapping people. 911 redirected to non-emergency.", "src": "https://en.wikipedia.org/wiki/2025_St._Louis_tornado"},
    {"name": "Union Tabernacle M.B. Church", "addr": "626 N Newstead Ave, St. Louis, MO 63108", "type": "church", "desc": "FEMA Disaster Recovery Center.", "src": "https://www.fema.gov/press-release/20250620/disaster-recovery-centers-opening-city-st-louis"},
    {"name": "Forest Park", "addr": "Forest Park, St. Louis, MO", "type": "park", "desc": "1,300 acres. Zoo had 10,000 guests — all survived.", "src": "https://en.wikipedia.org/wiki/2025_St._Louis_tornado"},
    {"name": "O'Fallon Park", "addr": "4397 W Florissant Ave, St. Louis, MO 63115", "type": "park", "desc": "Townhouses collapsed at park edge. EF2.", "src": "https://www.weather.gov/lsx/05_16_2025"},
    {"name": "Saint Louis Zoo", "addr": "1 Government Dr, St. Louis, MO 63110", "type": "landmark", "desc": "10,000 guests during tornado. All survived. Butterfly enclosure damaged.", "src": "https://en.wikipedia.org/wiki/2025_St._Louis_tornado"},
    {"name": "George B. Vashon Museum", "addr": "2223 St. Louis Ave, St. Louis, MO 63106", "type": "landmark", "desc": "African American history museum. 4,000+ artifacts spanning 250 years. Founded by retired educator Calvin Riley in 2015. National Register of Historic Places.", "src": "https://georgevashonmuseum.org/"},
]

results = []
headers = {"User-Agent": "STLTornadoMap/1.0"}
for place in PLACES:
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": place["addr"], "format": "json", "limit": 1},
                         headers=headers, timeout=15)
        data = r.json()
        if data:
            place["lat"] = float(data[0]["lat"])
            place["lon"] = float(data[0]["lon"])
            results.append(place)
            print(f"  ✓ {place['name']}: {place['lat']:.6f}, {place['lon']:.6f}")
        else:
            print(f"  ✗ {place['name']}: not found")
        time.sleep(1.1)
    except Exception as e:
        print(f"  ✗ {place['name']}: {e}")

# Add tornado event points (from NWS report directly) — REMOVED: now shown as path segments on map

with open(f"{OUT}/landmarks.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"  Saved {len(results)} landmarks")

# ============================================================
# 5. VACANT BUILDING DATA
# ============================================================
print("\n[5/6] Vacant building data...")
vacant = {}
if os.path.exists(f"{OUT}/vacant_overview.json"):
    with open(f"{OUT}/vacant_overview.json") as f:
        vacant = json.load(f)
    print(f"  Already have {len(vacant)} parcels")
else:
    try:
        r = requests.get("https://www.stlcitypermits.com/API/VacantBuilding/GetVacantBuildingOverview", timeout=180)
        r.raise_for_status()
        vacant = r.json()
        with open(f"{OUT}/vacant_overview.json", "w") as f:
            json.dump(vacant, f)
        print(f"  Got {len(vacant)} vacant parcels")
    except Exception as e:
        print(f"  Error: {e}")

# ============================================================
# 6. PARCEL COORDINATES (match to vacant buildings)
# ============================================================
print("\n[6/6] Parcel coordinates...")
if os.path.exists(f"{OUT}/vacant_buildings.geojson"):
    sz = os.path.getsize(f"{OUT}/vacant_buildings.geojson")
    if sz > 100:
        print(f"  Already have vacant_buildings.geojson ({sz:,} bytes)")
        print("  To rebuild, delete it and re-run.")
    else:
        print("  File exists but empty. Pulling parcels...")

if not os.path.exists(f"{OUT}/vacant_buildings.geojson") or os.path.getsize(f"{OUT}/vacant_buildings.geojson") < 100:
    print("  Pulling parcels from city GIS (Layer 4)...")
    base = "https://maps6.stlouis-mo.gov/arcgis/rest/services/CITYWORKS/CW_BASE/MapServer/4/query"
    all_parcels = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "outFields": "ParcelId,HANDLE,ColParcelId,LowerAsrParcelId",
            "geometry": "-90.35,38.62,-90.05,38.72",
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "inSR": 4326, "outSR": 4326, "f": "json",
            "returnGeometry": "true",
            "resultRecordCount": 2000, "resultOffset": offset,
        }
        try:
            r = requests.get(base, params=params, timeout=60)
            d = r.json()
            feats = d.get("features", [])
            if not feats: break
            all_parcels.extend(feats)
            offset += len(feats)
            if offset % 10000 == 0: print(f"    {offset} parcels...")
            if len(feats) < 2000: break
            time.sleep(0.3)
        except Exception as e:
            print(f"    Error at offset {offset}: {e}")
            break

    print(f"  Total parcels: {len(all_parcels)}")

    # Match using HANDLE field
    lookup = {}
    for feat in all_parcels:
        a = feat.get("attributes", {})
        g = feat.get("geometry", {})
        pid = str(a.get("HANDLE", "")).strip()
        if pid and "rings" in g:
            ring = g["rings"][0]
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)
            if -91 < cx < -89 and 38 < cy < 39:
                lookup[pid] = [cx, cy]

    print(f"  HANDLE lookup: {len(lookup)} entries")

    features = []
    for pid, info in vacant.items():
        coords = lookup.get(pid.strip())
        if coords:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coords},
                "properties": {
                    "parcelId": pid,
                    "monthsVacant": info.get("mo", 0),
                    "minorViolations": info.get("vmin", 0),
                    "majorViolations": info.get("vmaj", 0),
                    "csbComplaints": info.get("csb", 0),
                    "unpaidFees": info.get("unpd", 0),
                }
            })

    with open(f"{OUT}/vacant_buildings.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
    print(f"  Matched {len(features)} vacant buildings")

# ============================================================
# 7. NWS DAMAGE SURVEY POINTS (Damage Assessment Toolkit)
# ============================================================
print("\n[7/7] NWS damage survey points...")
# Layer 0 = individual damage points with EF ratings
# Bounding box covers STL tornado path area
DAT_URL = "https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer/0/query"
try:
    r = requests.get(DAT_URL, params={
        "where": "1=1",
        "geometry": "-90.35,38.62,-90.10,38.72",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326, "outSR": 4326,
        "outFields": "*",
        "f": "geojson",
        "resultRecordCount": 2000,
    }, timeout=60)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", [])
    print(f"  Got {len(feats)} damage points")

    if feats:
        # Check what fields are available
        sample = feats[0].get("properties", {})
        print(f"  Fields: {list(sample.keys())[:10]}")

        # Filter to May 2025 if date field exists
        filtered = []
        for f in feats:
            p = f.get("properties", {})
            # DAT uses eventdate or event_date_utc
            dt = p.get("eventdate", p.get("event_date_utc", p.get("date", "")))
            # Keep points from May 2025 or if no date filter is possible, keep all
            if dt:
                dt_str = str(dt)
                # Epoch ms or date string — check for May 2025
                if len(dt_str) > 10:
                    # Likely epoch ms
                    try:
                        import datetime
                        ts = int(dt_str) / 1000
                        d = datetime.datetime.fromtimestamp(ts)
                        if d.year == 2025 and d.month == 5:
                            filtered.append(f)
                    except:
                        filtered.append(f)
                elif "2025-05" in dt_str or "2025/05" in dt_str:
                    filtered.append(f)
                else:
                    filtered.append(f)
            else:
                filtered.append(f)

        if filtered:
            out_data = {"type": "FeatureCollection", "features": filtered}
        else:
            out_data = data

        with open(f"{OUT}/nws_damage_points.geojson", "w") as fp:
            json.dump(out_data, fp)
        sz = os.path.getsize(f"{OUT}/nws_damage_points.geojson")
        print(f"  Saved {len(out_data['features'])} points to data/nws_damage_points.geojson ({sz:,} bytes)")

        # Show EF rating breakdown
        ef_counts = {}
        for f in out_data["features"]:
            p = f.get("properties", {})
            ef = p.get("efrating", p.get("ef_rating", p.get("rating", "?")))
            ef_counts[ef] = ef_counts.get(ef, 0) + 1
        for ef, ct in sorted(ef_counts.items(), key=lambda x: -x[1]):
            print(f"    EF{ef}: {ct} points")
    else:
        print("  No damage points found in bounding box")
        print("  The NWS DAT may require different date/location filters")

except Exception as e:
    print(f"  Error: {e}")
    print("  NWS DAT may be down. The map will still work without it.")

# ============================================================
print("\n" + "=" * 60)
print("DONE! Files in data/:")
print("=" * 60)
for fn in sorted(os.listdir(OUT)):
    sz = os.path.getsize(f"{OUT}/{fn}")
    print(f"  {fn}  ({sz:,} bytes)")
print("\nOpen index.html with Live Server.")
