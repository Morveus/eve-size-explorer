#!/usr/bin/env python3
"""Download ship renders from CCP image server."""

import json
import os
import time
import urllib.request
import urllib.error

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RENDERS_DIR = os.path.join(os.path.dirname(__file__), "..", "renders")
SHIPS_JSON = os.path.join(DATA_DIR, "ships.json")

IMAGE_BASE = "https://images.evetech.net/types"
SIZE = 1024


def download_renders():
    os.makedirs(RENDERS_DIR, exist_ok=True)

    with open(SHIPS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    ships = data["ships"]
    total = len(ships)
    downloaded = 0
    skipped = 0
    failed = 0

    for i, ship in enumerate(ships):
        type_id = ship["typeID"]
        filename = f"{type_id}.png"
        filepath = os.path.join(RENDERS_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            skipped += 1
            continue

        url = f"{IMAGE_BASE}/{type_id}/render?size={SIZE}"
        print(f"[{i+1}/{total}] {ship['name']} ({type_id})...", end=" ", flush=True)

        try:
            urllib.request.urlretrieve(url, filepath)
            size_kb = os.path.getsize(filepath) / 1024
            print(f"OK ({size_kb:.0f} KB)")
            downloaded += 1
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            print(f"FAILED: {e}")
            failed += 1
            # Remove partial file
            if os.path.exists(filepath):
                os.remove(filepath)

        # Be respectful of CCP's server
        if (i + 1) % 10 == 0:
            time.sleep(0.5)

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    download_renders()
