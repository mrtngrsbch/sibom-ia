
import os
import shutil
import re
from pathlib import Path

def organize_files():
    base_dir = Path("python-cli/boletines")
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist.")
        return

    # Regex to match Municipality_Name_Number.json
    # It assumes the number is at the end, separated by an underscore.
    # Everything before the last underscore is the municipality name.
    pattern = re.compile(r"^(.*)_(\d+)\.json$")

    moved_count = 0
    errors = 0

    for file_path in base_dir.glob("*.json"):
        if not file_path.is_file():
            continue

        filename = file_path.name
        match = pattern.match(filename)

        if match:
            municipality_name = match.group(1)
            # number = match.group(2) # Not needed for directory structure

            target_dir = base_dir / municipality_name
            target_path = target_dir / filename

            try:
                if not target_dir.exists():
                    print(f"Creating directory: {target_dir}")
                    target_dir.mkdir(parents=True, exist_ok=True)
                
                print(f"Moving {filename} -> {municipality_name}/")
                shutil.move(str(file_path), str(target_path))
                moved_count += 1
            except Exception as e:
                print(f"Error moving {filename}: {e}")
                errors += 1
        else:
            print(f"Skipping {filename} (does not match pattern)")

    print(f"\nSummary:")
    print(f"Moved: {moved_count}")
    print(f"Errors: {errors}")

if __name__ == "__main__":
    organize_files()
