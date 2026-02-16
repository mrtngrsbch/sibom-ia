#!/usr/bin/env python3
"""Genera reporte final de migración."""

import json
from pathlib import Path

cp_file = Path("data/migration_checkpoint.json")
if not cp_file.exists():
    print("No checkpoint found")
    exit(1)

with open(cp_file) as f:
    cp = json.load(f)

files_done = len(cp["processed_file_paths"])
chunks = cp["processed_chunks"]

print(f"✅ ESTADO ACTUAL:")
print(f"   Archivos: {files_done}/169 ({int(files_done*100/169)}%)")
print(f"   Chunks: {chunks}")
print(f"   Última actualización: {cp['last_updated']}")
