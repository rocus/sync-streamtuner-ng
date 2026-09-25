#!/usr/bin/env python3

import sys
import json
import time
from pathlib import Path

INTERVAL = 30

###
def atomic_write(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
###

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_pls(path, station):
    url = station.get("url", "")

    lines = [
        "[playlist]",
        "NumberOfEntries=1",
        f"File1={url}",
        f"Title1={station.get('title', '')}",
        "Length1=-1",
        "",
        "# Station information from JSON",
    ]

    for key, value in station.items():
        if key in ("url", "title"):
            continue

        value = json.dumps(value, ensure_ascii=False)
        lines.append(f"# {key}={value}")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

def synchronize(json_path, pls_dir):
    data = load_json(json_path)

    if "favourite" not in data:
        print("ERROR: JSON file has no 'favourite' section.")
        return

    favourites = data["favourite"]

    # Stations currently in JSON, indexed by title.
    json_stations = {}

    for station in favourites:
        title = station.get("title", "")

        if title:
            json_stations[title] = station

    # ------------------------------------------------------------
    # JSON -> PLS
    #
    # JSON is the only source of information.
    # Create a PLS when it does not exist.
    # Existing PLS files are left completely alone.
    # ------------------------------------------------------------

    for title, station in json_stations.items():
        pls_path = pls_dir / f"{title}.pls"

        if not pls_path.exists():
            print(f"Creating: {pls_path.name}")
            write_pls(pls_path, station)

    # ------------------------------------------------------------
    # Remove PLS files that no longer correspond to a favorite.
    #
    # The PLS directory is only a temporary staging directory.
    # Files moved elsewhere are irrelevant to us.
    # ------------------------------------------------------------

    for pls_path in pls_dir.glob("*.pls"):
        if not pls_path.is_file():
            continue

        if pls_path.stem not in json_stations:
            print(f"Removing: {pls_path.name}")

            try:
                pls_path.unlink()
            except OSError as e:
                print(f"  Cannot delete PLS: {e}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} JSONFILE PLSDIRECTORY")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    pls_dir = Path(sys.argv[2])

    if not json_path.is_file():
        print(f"JSON file does not exist: {json_path}")
        sys.exit(1)

    if not pls_dir.is_dir():
        print(f"PLS directory does not exist: {pls_dir}")
        sys.exit(1)

    print("Favourites / PLS synchronizer")
    print(f"JSON      : {json_path}")
    print(f"PLS dir   : {pls_dir}")
    print(f"Interval  : {INTERVAL} seconds")
    print("Press Ctrl-C to stop.")
    print()

    while True:
        try:
            synchronize(json_path, pls_dir)

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except Exception as e:
            print(f"ERROR: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
