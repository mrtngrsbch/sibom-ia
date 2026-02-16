#!/usr/bin/env python3
"""Crear índices en Qdrant Cloud para filtros eficientes."""

from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Cargar env desde raíz
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

qdrant = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

collection_name = "normativas"

# Índices necesarios para filtros (con tipos correctos)
keyword_fields = [
    "tipo_documento",
    "municipio",
    "periodo",
    "tipo_detalle"
]

bool_fields = [
    "is_executive_summary",
    "contains_key_numbers"
]

print(f"🔧 Creando índices en colección '{collection_name}'...\n")

# Índices KEYWORD
for field in keyword_fields:
    try:
        qdrant.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD
        )
        print(f"   ✓ Índice KEYWORD creado: {field}")
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            print(f"   ⚪ Índice ya existe: {field}")
        else:
            print(f"   ⚠️  Error en {field}: {e}")

# Índices BOOL
for field in bool_fields:
    try:
        qdrant.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.BOOL
        )
        print(f"   ✓ Índice BOOL creado: {field}")
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str:
            print(f"   ⚪ Índice ya existe: {field}")
        else:
            print(f"   ⚠️  Error en {field}: {e}")

print(f"\n✅ Índices configurados")
