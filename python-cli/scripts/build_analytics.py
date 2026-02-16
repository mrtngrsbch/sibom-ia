import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import glob
import re

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "indexes"
BOLETINES_DIR = BASE_DIR / "boletines"
OUTPUT_FILE = DATA_DIR / "analytics_snapshot.json"


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def parse_date_safe(date_str):
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def normalize_muni_name(filename_stem, known_munis=None):
    # 0. Basic cleanup
    clean_stem = filename_stem.replace('_', ' ')

    # 1. Check against known list (Longest match first priority)
    if known_munis:
        # Sort by length descending to catch "Adolfo Gonzales Chaves" before "Adolfo" if such existed
        # Using a list sorted by length is recommended
        for muni in sorted(known_munis, key=len, reverse=True):
            if clean_stem.lower().startswith(muni.lower()):
                return muni

    # 2. Heuristics for unknown
    # Remove _123 suffix if present
    stem = re.sub(r'_\d+$', '', filename_stem)

    # Handle specific patterns like "Carlos_Tejedor_Balances_..."
    if '_Balances_' in stem:
        stem = stem.split('_Balances_')[0]

    stem = stem.replace('_', ' ')
    return stem.strip()


def main():
    print("🚀 Agent 1: Starting Robust Analytics Build Process...")

    # Load known municipalities for normalization
    known_munis = set()
    try:
        city_map = load_json(BOLETINES_DIR / "CITY_MAP.json")
        known_munis = set(city_map.values())
        print(f"Loaded {len(known_munis)} known municipalities from CITY_MAP")
    except Exception as e:
        print(f"Warning: Could not load CITY_MAP.json: {e}")

    muni_stats = defaultdict(lambda: {
        "boletines_count": 0,
        "first_seen": None,
        "last_seen": None,
        "years": defaultdict(int)
    })

    bulletin_id_map = {}  # ID (str) -> Municipality Name

    # 1. Scan Bulletins Directly (Source of Truth)
    print("📂 Scanning bulletin files...")
    # Matches /boletines/*.json and /boletines/*/*.json
    files = list(BOLETINES_DIR.glob('**/*.json'))

    count_scanned = 0
    for f in files:
        if f.name.startswith('.'):
            continue
        if f.name == 'CITY_MAP.json':
            continue
        if f.name == 'boletines_index.json':
            continue

        try:
            content = load_json(f)
        except:
            continue

        # Infer municipality from filename usually reliable
        # Or from path parent if it's a directory
        stem = f.stem
        muni_name = normalize_muni_name(stem, known_munis)

        # Verify if content has 'municipality' field or infer
        # Usually content has "description": "142º de Coronel Pringles"
        # But filename is safer for normalization consistency

        # Extract Bulletin ID
        # "link": "/bulletins/7241" OR "boletin_url": "https://.../bulletins/7241"
        link = content.get('link') or content.get('boletin_url', '')
        b_id = None

        if link and '/bulletins/' in link:
            try:
                # Handle both absolute and relative URLs
                # Split by /bulletins/ and take the part after
                # "https://sibom.../bulletins/13662" -> "13662"
                # "/bulletins/7241" -> "7241"
                after_bulletins = link.split('/bulletins/')[1]
                # Take the first segment (avoid contents/...)
                b_id = after_bulletins.split('/')[0]

                if b_id:
                    bulletin_id_map[b_id] = muni_name
            except Exception:
                pass

        # Stats
        stats = muni_stats[muni_name]
        stats["boletines_count"] += 1

        d_str = content.get('date')
        if d_str:
            d = parse_date_safe(d_str)
            if d:
                if not stats["first_seen"] or d < stats["first_seen"]:
                    stats["first_seen"] = d
                if not stats["last_seen"] or d > stats["last_seen"]:
                    stats["last_seen"] = d
                stats["years"][d.year] += 1

        count_scanned += 1
        if count_scanned % 500 == 0:
            print(f"   Processed {count_scanned} files...")

    print(f"✅ Mapped {len(bulletin_id_map)} bulletin IDs to municipalities.")

    # 2. Process Normativas (using Map)
    normativas = load_json(DATA_DIR / "normativas_index_minimal.json")
    print(f"📊 Processing {len(normativas)} normativas...")

    normativa_stats = defaultdict(lambda: {
        "total_normativas": 0,
        "by_type": defaultdict(int),
        "by_year": defaultdict(int)
    })

    for n in normativas:
        muni = n.get("m")

        # Try resolve
        if not muni:
            url = n.get("url", "")
            if "/bulletins/" in url:
                try:
                    b_id = url.split("/bulletins/")[1].split("/")[0]
                    muni = bulletin_id_map.get(b_id)
                except:
                    pass

        if not muni:
            # Still unknown? Skip
            continue

        muni = muni.strip()
        n_stats = normativa_stats[muni]
        n_stats["total_normativas"] += 1

        t = n.get("t", "unknown") or "unknown"
        n_stats["by_type"][t.lower()] += 1

        y = n.get("y")
        if y:
            try:
                y_int = int(y)
                if 1900 <= y_int <= 2100:
                    n_stats["by_year"][y_int] += 1
            except:
                pass

    # 3. Merge & Output
    output_municipalities = []
    global_docs = 0

    all_munis = set(muni_stats.keys()) | set(normativa_stats.keys())

    for muni in sorted(all_munis):
        b_data = muni_stats[muni]
        n_data = normativa_stats[muni]

        first = b_data["first_seen"].isoformat(
        ) if b_data["first_seen"] else None
        last = b_data["last_seen"].isoformat() if b_data["last_seen"] else None

        item = {
            "name": muni,
            "stats": {
                "bulletins": b_data["boletines_count"],
                "normativas": n_data["total_normativas"],
                "first_date": first,
                "last_date": last,
            },
            "breakdown": {
                "by_type": dict(n_data["by_type"]),
                "by_year": [{"year": k, "count": v} for k, v in sorted(n_data["by_year"].items())]
            },
            "data_score": min(100, int((n_data["total_normativas"] / 500) * 100)) if n_data["total_normativas"] > 0 else 0
        }
        output_municipalities.append(item)
        global_docs += n_data["total_normativas"]

    final_snapshot = {
        "generated_at": datetime.now().isoformat(),
        "global": {
            "total_municipalities": len(output_municipalities),
            "total_documents": global_docs,
            "total_bulletins": count_scanned
        },
        "municipalities": output_municipalities
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_snapshot, f, ensure_ascii=False, indent=2)

    print(f"✅ Success! Saved to {OUTPUT_FILE}")
    print(f"   Total Documents: {global_docs}")


if __name__ == "__main__":
    main()
