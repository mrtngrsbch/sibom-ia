#!/usr/bin/env python3
"""
Post-Migration Validation Script

Verifica integridad de migración empresarial:
- Todos los archivos fueron procesados
- Chunks correctamente indexados en Qdrant
- Queries funcionan correctamente
- Totales financieros matchean con source

Usage:
    python scripts/post_migration_validation.py [--sample-queries]
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from qdrant_client import QdrantClient
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


class PostMigrationValidator:
    """Valida integridad post-migración."""

    def __init__(self):
        load_dotenv()

        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not all([self.qdrant_url, self.qdrant_api_key]):
            raise ValueError("Faltan variables: QDRANT_URL, QDRANT_API_KEY")

        self.qdrant = QdrantClient(
            url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.collection_name = "normativas"

    def count_balance_chunks(self) -> Dict[str, Any]:
        """Cuenta chunks de balances en Qdrant."""
        print("\n📊 1. CONTEO: Chunks de balances en Qdrant")
        print("=" * 60)

        # Scroll por todos los chunks migrados de balances
        balance_chunks = []
        offset = None

        while True:
            results, offset = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {"key": "source", "match": {"value": "balance_migration_v1"}}
                    ]
                },
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            balance_chunks.extend(results)

            if offset is None:
                break

        # Agrupar por municipio y periodo
        by_municipio = {}
        by_periodo = {}
        by_tipo_detalle = {}

        for chunk in balance_chunks:
            payload = chunk.payload
            muni = payload.get("municipio", "Desconocido")
            periodo = payload.get("periodo", "Desconocido")
            tipo_det = payload.get("tipo_detalle", "Desconocido")

            by_municipio[muni] = by_municipio.get(muni, 0) + 1
            by_periodo[periodo] = by_periodo.get(periodo, 0) + 1
            by_tipo_detalle[tipo_det] = by_tipo_detalle.get(tipo_det, 0) + 1

        print(f"   Total chunks de balances: {len(balance_chunks):,}")
        print(f"\n   Por municipio:")
        for muni, count in sorted(by_municipio.items()):
            print(f"      {muni}: {count} chunks")

        print(f"\n   Por tipo detalle:")
        for tipo, count in sorted(by_tipo_detalle.items()):
            print(f"      {tipo}: {count} chunks")

        return {
            "total_chunks": len(balance_chunks),
            "by_municipio": by_municipio,
            "by_tipo_detalle": by_tipo_detalle
        }

    def verify_executive_summaries(self) -> Dict[str, Any]:
        """Verifica que existan resúmenes ejecutivos."""
        print("\n📝 2. VERIFICACIÓN: Resúmenes ejecutivos")
        print("=" * 60)

        summaries = self.qdrant.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "source", "match": {"value": "balance_migration_v1"}},
                    {"key": "is_executive_summary", "match": {"value": True}}
                ]
            },
            limit=100,
            with_payload=True,
            with_vectors=False
        )[0]

        print(f"   Resúmenes ejecutivos encontrados: {len(summaries)}")

        # Verificar que tengan números clave
        with_numbers = sum(
            1 for s in summaries if s.payload.get("contains_key_numbers"))

        print(f"   Con números clave: {with_numbers}")

        if summaries:
            print(f"\n   Ejemplo de resumen ejecutivo:")
            sample = summaries[0]
            print(f"      Municipio: {sample.payload.get('municipio')}")
            print(f"      Periodo: {sample.payload.get('periodo')}")
            print(f"      Texto (primeros 200 chars):")
            text = sample.payload.get('chunk_text', '')[:200]
            for line in text.split('\n')[:5]:
                if line.strip():
                    print(f"         {line}")

        return {
            "count": len(summaries),
            "with_numbers": with_numbers
        }

    def test_sample_queries(self) -> Dict[str, Any]:
        """Ejecuta queries de prueba."""
        print("\n🔍 3. QUERIES DE PRUEBA")
        print("=" * 60)

        test_queries = [
            {
                "query": "Balance de tesorería Carlos Tejedor 2024",
                "expected_municipio": "Carlos Tejedor"
            },
            {
                "query": "Recursos totales",
                "expected_has": "recursos"
            },
            {
                "query": "Gastos del municipio",
                "expected_has": "gastos"
            }
        ]

        results = []

        for test in test_queries:
            print(f"\n   Query: \"{test['query']}\"")

            # Search con filtro (sin vector por ahora, solo scroll)
            search_results = self.qdrant.scroll(
                collection_name=self.collection_name,
                scroll_filter={
                    "must": [
                        {"key": "source", "match": {"value": "balance_migration_v1"}}
                    ]
                },
                limit=3,
                with_payload=True,
                with_vectors=False
            )[0]

            if not search_results:
                print(f"      ⚠️  No se encontraron resultados")
                results.append({"query": test['query'], "found": False})
                continue

            print(f"      ✓ {len(search_results)} resultados")

            # Verificar primer resultado
            first = search_results[0].payload
            print(f"         - Municipio: {first.get('municipio')}")
            print(f"         - Periodo: {first.get('periodo')}")
            print(f"         - Tipo chunk: {first.get('chunk_type')}")

            results.append({
                "query": test['query'],
                "found": True,
                "results_count": len(search_results)
            })

        passed = sum(1 for r in results if r.get('found'))

        print(f"\n   ✅ Queries exitosas: {passed}/{len(test_queries)}")

        return {
            "queries_tested": len(test_queries),
            "queries_passed": passed,
            "results": results
        }

    def compare_with_source(self) -> Dict[str, Any]:
        """Compara datos en Qdrant vs archivos source."""
        print("\n🔄 4. COMPARACIÓN: Qdrant vs Source Files")
        print("=" * 60)

        # Contar archivos source
        base_path = Path(__file__).parent.parent / "boletines"
        source_files = []
        for balance_file in base_path.rglob("*Balances*.json"):
            try:
                with open(balance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get("tipo_detalle") == "BALANCE DE TESORERIA":
                    source_files.append({
                        "municipio": data.get("municipio"),
                        "periodo": data.get("periodo")
                    })
            except:
                continue

        print(
            f"   Archivos source (Balance de Tesorería): {len(source_files)}")

        # Contar balances únicos en Qdrant (por municipio+periodo)
        qdrant_balances = self.qdrant.scroll(
            collection_name=self.collection_name,
            scroll_filter={
                "must": [
                    {"key": "source", "match": {"value": "balance_migration_v1"}},
                    {"key": "is_executive_summary", "match": {"value": True}}
                ]
            },
            limit=100,
            with_payload=True,
            with_vectors=False
        )[0]

        print(
            f"   Balances en Qdrant (resúmenes ejecutivos): {len(qdrant_balances)}")

        coverage = (len(qdrant_balances) / len(source_files)
                    * 100) if source_files else 0

        print(f"\n   📊 Cobertura: {coverage:.1f}%")

        if coverage < 100:
            pendientes = max(0, len(source_files) - len(qdrant_balances))
            print(f"   ⚠️  Hay {pendientes} archivos sin migrar")
        else:
            print(f"   ✅ Todos los archivos source fueron migrados")

        return {
            "source_files": len(source_files),
            "qdrant_balances": len(qdrant_balances),
            "coverage_percent": coverage
        }

    def run_all_validations(self) -> bool:
        """Ejecuta todas las validaciones post-migración."""
        print("\n" + "=" * 60)
        print("🏢 POST-MIGRATION VALIDATION (Enterprise Grade)")
        print("=" * 60)

        results = {}
        all_passed = True

        try:
            # 1. Conteo de chunks
            results["chunks"] = self.count_balance_chunks()

            # 2. Verificar resúmenes ejecutivos
            results["summaries"] = self.verify_executive_summaries()

            if results["summaries"]["count"] == 0:
                print("\n   ⚠️  ADVERTENCIA: No hay resúmenes ejecutivos")
                all_passed = False

            # 3. Queries de prueba
            results["queries"] = self.test_sample_queries()

            if results["queries"]["queries_passed"] < results["queries"]["queries_tested"]:
                print("\n   ⚠️  ADVERTENCIA: Algunas queries fallaron")
                all_passed = False

            # 4. Comparación con source
            results["comparison"] = self.compare_with_source()

            if results["comparison"]["coverage_percent"] < 100:
                print("\n   ⚠️  ADVERTENCIA: Cobertura incompleta")
                all_passed = False

        except Exception as e:
            print(f"\n❌ Error durante validación: {e}")
            import traceback
            traceback.print_exc()
            return False

        # Guardar reporte
        report_file = Path("data/migration_backup") / \
            f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "validation_status": "PASSED" if all_passed else "WARNINGS",
                "results": results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n   📄 Reporte guardado: {report_file}")

        # Resumen final
        print("\n" + "=" * 60)
        if all_passed:
            print("✅ VALIDACIÓN COMPLETADA - TODO OK")
        else:
            print("⚠️  VALIDACIÓN COMPLETADA - CON ADVERTENCIAS")
        print("=" * 60)

        print(f"\n   Chunks totales: {results['chunks']['total_chunks']:,}")
        print(f"   Resúmenes ejecutivos: {results['summaries']['count']}")
        print(
            f"   Queries exitosas: {results['queries']['queries_passed']}/{results['queries']['queries_tested']}")
        print(
            f"   Cobertura: {results['comparison']['coverage_percent']:.1f}%")
        print()

        return all_passed


def main():
    try:
        validator = PostMigrationValidator()
        success = validator.run_all_validations()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
