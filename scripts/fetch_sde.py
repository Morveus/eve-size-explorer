#!/usr/bin/env python3
"""Download Fuzzwork SQLite SDE and extract ship data."""

import bz2
import json
import os
import sqlite3
import urllib.request

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SQLITE_BZ2 = os.path.join(DATA_DIR, "sde.sqlite.bz2")
SQLITE_DB = os.path.join(DATA_DIR, "sde.sqlite")
SHIPS_JSON = os.path.join(DATA_DIR, "ships.json")

FUZZWORK_URL = "https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2"

# EVE category ID for ships
CATEGORY_SHIP = 6
# Category for structures (citadels, engineering complexes, etc.)
CATEGORY_STRUCTURE = 65


def download_sde():
    """Download the SQLite SDE from Fuzzwork."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if os.path.exists(SQLITE_DB):
        print(f"SDE already exists at {SQLITE_DB}, skipping download.")
        return

    if not os.path.exists(SQLITE_BZ2):
        print(f"Downloading SDE from {FUZZWORK_URL}...")
        urllib.request.urlretrieve(FUZZWORK_URL, SQLITE_BZ2)
        print("Download complete.")

    print("Decompressing...")
    with bz2.open(SQLITE_BZ2, "rb") as f_in:
        with open(SQLITE_DB, "wb") as f_out:
            while chunk := f_in.read(1024 * 1024):
                f_out.write(chunk)
    print("Decompression complete.")


def extract_ships():
    """Extract ship data from the SDE SQLite database."""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row

    # Get all published ship types with radius from dogma attributes
    # Ships are in categoryID=6, structures in categoryID=65
    # Attribute 162 = radius (meters)
    query = """
    SELECT
        t.typeID,
        t.typeName,
        t.groupID,
        g.groupName,
        t.mass,
        t.volume,
        COALESCE(da.valueFloat, 0) as radius
    FROM invTypes t
    JOIN invGroups g ON t.groupID = g.groupID
    LEFT JOIN dgmTypeAttributes da
        ON da.typeID = t.typeID AND da.attributeID = 162
    WHERE g.categoryID IN (?, ?)
      AND t.published = 1
    ORDER BY g.groupName, t.typeName
    """

    cursor = conn.execute(query, (CATEGORY_SHIP, CATEGORY_STRUCTURE))
    rows = cursor.fetchall()

    ships = []
    for row in rows:
        ship = {
            "typeID": row["typeID"],
            "name": row["typeName"],
            "groupID": row["groupID"],
            "group": row["groupName"],
            "mass": row["mass"],
            "volume": row["volume"],
            "radius": row["radius"],
        }
        ships.append(ship)

    # Try to get additional size info from dogma attributes
    # Check what attribute names contain "length", "width", "height"
    attr_query = """
    SELECT attributeID, attributeName
    FROM dgmAttributeTypes
    WHERE lower(attributeName) LIKE '%length%'
       OR lower(attributeName) LIKE '%width%'
       OR lower(attributeName) LIKE '%height%'
    """
    attr_cursor = conn.execute(attr_query)
    size_attrs = attr_cursor.fetchall()
    if size_attrs:
        print("Found size-related attributes:")
        for attr in size_attrs:
            print(f"  {attr['attributeID']}: {attr['attributeName']}")

    conn.close()

    # Save to JSON
    output = {
        "version": "SDE-latest",
        "count": len(ships),
        "ships": ships,
    }

    with open(SHIPS_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(ships)} ships/structures to {SHIPS_JSON}")
    return ships


if __name__ == "__main__":
    download_sde()
    extract_ships()
