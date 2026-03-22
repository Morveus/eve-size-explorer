#!/usr/bin/env python3
"""Enrich ship data with radius from ESI API."""

import json
import os
import time
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SHIPS_JSON = os.path.join(DATA_DIR, "ships.json")
ESI_BASE = "https://esi.evetech.net/latest/universe/types"


def fetch_radius(type_id):
    """Fetch radius for a single type from ESI."""
    url = f"{ESI_BASE}/{type_id}/?datasource=tranquility"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("radius", 0)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  Error fetching {type_id}: {e}")
        return 0


def main():
    with open(SHIPS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    ships = data["ships"]
    total = len(ships)
    updated = 0

    for i, ship in enumerate(ships):
        print(f"[{i+1}/{total}] {ship['name']}...", end=" ", flush=True)
        radius = fetch_radius(ship["typeID"])
        if radius > 0:
            ship["radius"] = radius
            updated += 1
            print(f"radius={radius}m")
        else:
            print("no radius")
        # ESI rate limit: ~20 req/s, be gentle
        if (i + 1) % 20 == 0:
            time.sleep(1)

    with open(SHIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated {updated}/{total} ships with radius data.")


if __name__ == "__main__":
    main()
