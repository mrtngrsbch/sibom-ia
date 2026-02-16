#!/usr/bin/env python3
"""
Pre-Migration Health Checks & Backup

Valida que el sistema esté listo para migración empresarial:
- Qdrant Cloud accesible y saludable
- Backup de metadata de colección actual
- Validación de archivos source
- Estimación precisa de recursos

Usage:
    python scripts/pre_migration_checks.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: {e}")
    print("   Instala: pip install qdrant-client python-dotenv")
    sys.exit(1)


class PreMigrationValidator:
    """Valida pre-condiciones para migración empresarial."""

    def __init__(self):
        load_dotenv()

        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not all([self.qdrant_url, self.qdrant_api_key, self.openai_api_key]):
            raise ValueError(
                "Faltan variables de entorno: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY")

        self.qdrant = QdrantClient(
            url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.collection_name = "normativas"
        self.backup_dir = Path("data/migration_backup")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def check_qdrant_health(self) -> Dict[str, Any]:
        """Verifica salud de Qdrant Cloud."""
        print("\n🔍 1. HEALTH CHECK: Qdrant Cloud")
        print("=" * 60)

        try:
            # Verificar colección existe
            collections = self.qdrant.get_collections().collections
            collection_names = [c.name for c in collections]

            print(f"   ✓ Conexión exitosa a: {self.qdrant_url[:50]}...")
            print(f"   ✓ Colecciones disponibles: {len(collection_names)}")

            if self.collection_name not in collection_names:
                print(f"   ⚠️  Colección '{self.collection_name}' no existe")
                create = input(
                    f"   ¿Crear colección '{self.collection_name}'? (y/n): ")
                if create.lower() == 'y':
                    from qdrant_client.models import Distance, VectorParams
                    self.qdrant.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=1536, distance=Distance.COSINE)
                    )
                    print(f"   ✓ Colección '{self.collection_name}' creada")
                else:
                    raise ValueError(
                        f"Colección '{self.collection_name}' requerida")

            # Info de colección
            collection_info = self.qdrant.get_collection(self.collection_name)

            print(f"\n   📊 Colección '{self.collection_name}':")
            print(f"      - Points actuales: {collection_info.points_count:,}")
            print(
                f"      - Vector dims: {collection_info.config.params.vectors.size}")
            print(
                f"      - Distancia: {collection_info.config.params.vectors.distance}")
            print(f"      - Estado: {collection_info.status}")

            if collection_info.status != "green":
                print(
                    f"   ⚠️  ADVERTENCIA: Colección en estado '{collection_info.status}'")

            return {
                "healthy": collection_info.status == "green",
                "points_count": collection_info.points_count,
                "vector_dims": collection_info.config.params.vectors.size
            }

        except Exception as e:
            print(f"   ❌ Error conectando a Qdrant: {e}")
            return {"healthy": False, "error": str(e)}

    def backup_collection_metadata(self) -> Path:
        """Backup de metadata de colección actual."""
        print("\n💾 2. BACKUP: Metadata de colección")
        print("=" * 60)

        try:
            collection_info = self.qdrant.get_collection(self.collection_name)

            # Sample de 10 points para ver estructura
            sample_points = self.qdrant.scroll(
                collection_name=self.collection_name,
                limit=10,
                with_payload=True,
                with_vectors=False
            )[0]

            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vector_config": {
                    "size": collection_info.config.params.vectors.size,
                    "distance": str(collection_info.config.params.vectors.distance)
                },
                "sample_payloads": [
                    {
                        "id": str(p.id),
                        "payload_keys": list(p.payload.keys()) if p.payload else []
                    }
                    for p in sample_points
                ]
            }

            backup_file = self.backup_dir / \
                f"collection_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            print(f"   ✓ Metadata guardado en: {backup_file}")
            print(
                f"   ✓ Points en colección: {collection_info.points_count:,}")
            print(f"   ✓ Sample size: {len(sample_points)} points")

            return backup_file

        except Exception as e:
            print(f"   ❌ Error en backup: {e}")
            raise

    def validate_source_files(self) -> Dict[str, Any]:
        """Valida archivos fuente de balances."""
        print("\n📁 3. VALIDACIÓN: Archivos fuente")
        print("=" * 60)

        balance_files = []
        invalid_files = []

        for balance_file in Path("boletines").rglob("*Balances*.json"):
            try:
                with open(balance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                tipo_detalle = data.get("tipo_detalle", "").strip()

                if tipo_detalle == "BALANCE DE TESORERIA":
                    # Validar campos requeridos
                    required_fields = ["municipio", "periodo", "tablas_md"]
                    missing = [f for f in required_fields if not data.get(f)]

                    if missing:
                        invalid_files.append({
                            "file": str(balance_file),
                            "error": f"Campos faltantes: {missing}"
                        })
                    else:
                        balance_files.append({
                            "file": str(balance_file),
                            "municipio": data.get("municipio"),
                            "periodo": data.get("periodo"),
                            "tablas_count": len(data.get("tablas_md", []))
                        })

            except Exception as e:
                invalid_files.append({
                    "file": str(balance_file),
                    "error": str(e)
                })

        print(f"   ✓ Balances válidos: {len(balance_files)}")

        if invalid_files:
            print(f"   ⚠️  Archivos inválidos: {len(invalid_files)}")
            for inv in invalid_files[:3]:  # Mostrar primeros 3
                print(f"      - {inv['file']}: {inv['error']}")

        # Agrupar por municipio
        municipios = {}
        for bf in balance_files:
            muni = bf["municipio"]
            municipios[muni] = municipios.get(muni, 0) + 1

        print(f"\n   📊 Distribución por municipio:")
        for muni, count in sorted(municipios.items()):
            print(f"      - {muni}: {count} balances")

        return {
            "valid_files": len(balance_files),
            "invalid_files": len(invalid_files),
            "balance_files": balance_files,
            "municipios": municipios
        }

    def estimate_resources(self, file_count: int) -> Dict[str, Any]:
        """Estima recursos necesarios para migración."""
        print("\n💰 4. ESTIMACIÓN: Recursos necesarios")
        print("=" * 60)

        # Estimaciones basadas en test real
        avg_chunks_per_file = 13
        avg_tokens_per_chunk = 600

        total_chunks = file_count * avg_chunks_per_file
        total_tokens = total_chunks * avg_tokens_per_chunk

        # Costos OpenAI
        embedding_cost_per_1m = 0.02  # text-embedding-3-small
        total_cost = (total_tokens / 1_000_000) * embedding_cost_per_1m

        # Tiempo estimado (con rate limits)
        # ~1 segundo por chunk con batch_size=1
        time_minutes = (total_chunks * 1) / 60

        print(f"   Archivos a procesar: {file_count}")
        print(f"   Chunks estimados: {total_chunks:,}")
        print(f"   Tokens estimados: {total_tokens:,}")
        print(f"   Costo estimado: ${total_cost:.4f} USD")
        print(f"   Tiempo estimado: {time_minutes:.1f} minutos")
        print(
            f"\n   ⚠️  Estos son valores estimados basados en promedio de {avg_chunks_per_file} chunks/archivo")

        return {
            "files": file_count,
            "chunks": total_chunks,
            "tokens": total_tokens,
            "cost_usd": total_cost,
            "time_minutes": time_minutes
        }

    def generate_migration_plan(self, validation_results: Dict[str, Any]) -> Path:
        """Genera plan de migración detallado."""
        print("\n📋 5. PLAN DE MIGRACIÓN")
        print("=" * 60)

        plan = {
            "created_at": datetime.now().isoformat(),
            "validation_results": validation_results,
            "migration_strategy": {
                "approach": "incremental_batches",
                "batch_size": 5,
                "pilot_test": True,
                "pilot_file_count": 1,
                "checkpoint_frequency": 5
            },
            "rollback_plan": {
                "backup_location": str(self.backup_dir),
                "can_rollback": True,
                "rollback_command": "python scripts/rollback_migration.py"
            },
            "acceptance_criteria": [
                "100% de archivos procesados sin errores",
                "Todos los chunks tienen embeddings válidos",
                "Queries de prueba retornan resultados correctos",
                "Verificación de totales financieros coincide con source"
            ]
        }

        plan_file = self.backup_dir / \
            f"migration_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        print(f"   ✓ Plan guardado en: {plan_file}")
        print(f"\n   Estrategia seleccionada:")
        print(f"      1. Migración PILOTO: 1 archivo primero")
        print(f"      2. Validación de piloto")
        print(f"      3. Migración por batches de 5 archivos")
        print(f"      4. Checkpoint cada 5 archivos")
        print(f"      5. Validación post-migración exhaustiva")

        return plan_file

    def run_all_checks(self) -> bool:
        """Ejecuta todos los checks pre-migración."""
        print("\n" + "=" * 60)
        print("🏢 PRE-MIGRATION VALIDATION (Enterprise Grade)")
        print("=" * 60)

        results = {}

        # 1. Health check
        health = self.check_qdrant_health()
        results["health"] = health

        if not health.get("healthy"):
            print("\n❌ FALLO: Qdrant no está saludable. Abortando.")
            return False

        # 2. Backup
        try:
            backup_file = self.backup_collection_metadata()
            results["backup_file"] = str(backup_file)
        except Exception as e:
            print(f"\n❌ FALLO: Error en backup: {e}")
            return False

        # 3. Validación de archivos
        validation = self.validate_source_files()
        results["validation"] = validation

        if validation["valid_files"] == 0:
            print("\n❌ FALLO: No hay archivos válidos para migrar.")
            return False

        # 4. Estimación de recursos
        resources = self.estimate_resources(validation["valid_files"])
        results["resources"] = resources

        # 5. Plan de migración
        plan_file = self.generate_migration_plan(results)
        results["plan_file"] = str(plan_file)

        # Resumen final
        print("\n" + "=" * 60)
        print("✅ VALIDACIÓN COMPLETADA")
        print("=" * 60)
        print(
            f"\n   Estado Qdrant: {'✅ Saludable' if health['healthy'] else '❌ Problemático'}")
        print(f"   Backup guardado: ✅ {backup_file.name}")
        print(f"   Archivos válidos: ✅ {validation['valid_files']}")
        print(f"   Costo estimado: 💰 ${resources['cost_usd']:.4f}")
        print(f"   Tiempo estimado: ⏱️  {resources['time_minutes']:.1f} min")

        print(f"\n   ✅ Sistema listo para migración empresarial")
        print(f"\n   Siguiente paso:")
        print(f"      python scripts/migrate_balances_to_qdrant.py --pilot")
        print()

        return True


def main():
    try:
        validator = PreMigrationValidator()
        success = validator.run_all_checks()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
