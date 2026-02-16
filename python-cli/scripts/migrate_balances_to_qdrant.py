#!/usr/bin/env python3
"""
Script de Migración: Balances de Tesorería → Qdrant Cloud

Migra únicamente los 25 BALANCES DE TESORERIA a Qdrant Cloud con embeddings OpenAI.

Proceso:
1. Buscar archivos con tipo_detalle = "BALANCE DE TESORERIA"
2. Generar chunks inteligentes (resumen ejecutivo + tablas)
3. Generar embeddings con OpenAI text-embedding-3-small
4. Subir a Qdrant Cloud con metadata
5. Verificar integridad

Características:
- Resume capability: Guarda progreso cada 5 balances
- Validación post-migración
- Estimación de costos antes de ejecutar
- Manejo de errores robusto

Usage:
    cd python-cli
    python scripts/migrate_balances_to_qdrant.py [--dry-run] [--resume] [--pilot]

Flags:
    --dry-run: Simula migración sin subir a Qdrant
    --resume: Continúa desde último checkpoint guardado
    --pilot: Migra solo 1 archivo para validar (modo piloto empresarial)
"""

from services.chunker import IntelligentChunker, DocumentChunk
from services.embedder import OpenAIEmbedder, EmbeddingResult
import os
import sys
import json
import uuid
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Agregar parent directory al path para imports (ANTES de imports locales)
sys.path.insert(0, str(Path(__file__).parent.parent))


try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct, Distance, VectorParams
except ImportError:
    print("❌ Error: qdrant-client no instalado. Ejecuta: pip install qdrant-client")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv no instalado. Ejecuta: pip install python-dotenv")
    sys.exit(1)


# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuración
BALANCE_TYPE_TARGET = "BALANCE DE TESORERIA"
CHECKPOINT_FILE = "data/migration_checkpoint.json"
COLLECTION_NAME = "normativas"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


class BalanceMigrator:
    """Migrador de balances a Qdrant Cloud con validación empresarial."""

    def __init__(self, dry_run: bool = False, pilot_mode: bool = False, auto_approve: bool = False):
        self.dry_run = dry_run
        self.pilot_mode = pilot_mode
        self.auto_approve = auto_approve

        # Cargar environment variables
        load_dotenv()

        # Inicializar servicios
        print("🔧 Inicializando servicios...\n")

        self.chunker = IntelligentChunker()
        self.embedder = OpenAIEmbedder(model=EMBEDDING_MODEL)

        if not dry_run:
            qdrant_url = os.getenv("QDRANT_URL")
            qdrant_api_key = os.getenv("QDRANT_API_KEY")

            if not qdrant_url or not qdrant_api_key:
                raise ValueError(
                    "QDRANT_URL y QDRANT_API_KEY deben estar configurados en .env")

            self.qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            print(f"✅ Conectado a Qdrant Cloud: {qdrant_url[:50]}...")
        else:
            self.qdrant = None
            print("🔍 Modo DRY-RUN: No se subirá a Qdrant")

        if pilot_mode:
            print("🧪 Modo PILOTO: Solo se procesará 1 archivo para validación")

        print()

    def find_balance_files(self, base_path: str = "boletines") -> List[Path]:
        """
        Encuentra archivos JSON con tipo_detalle = "BALANCE DE TESORERIA".

        Returns:
            Lista de Path objects de archivos válidos
        """
        print(f"🔍 Buscando balances en {base_path}/...\n")

        balance_files = []
        all_balance_files = list(Path(base_path).rglob("*Balances*.json"))

        print(
            f"   Archivos *Balances*.json encontrados: {len(all_balance_files)}")

        for file_path in all_balance_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                tipo_detalle = data.get("tipo_detalle", "").strip()

                if tipo_detalle == BALANCE_TYPE_TARGET:
                    balance_files.append(file_path)

            except Exception as e:
                logger.warning(f"Error leyendo {file_path}: {e}")
                continue

        print(f"   ✅ Balances de Tesorería: {len(balance_files)}\n")

        return balance_files

    def load_checkpoint(self) -> Dict[str, Any]:
        """Carga checkpoint de migración previa."""
        checkpoint_path = Path(CHECKPOINT_FILE)

        if checkpoint_path.exists():
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)
            print(
                f"📂 Checkpoint encontrado: {checkpoint['processed_files']} archivos procesados")
            return checkpoint

        return {
            "processed_files": 0,
            "processed_chunks": 0,
            "processed_file_paths": [],
            "last_updated": None
        }

    def save_checkpoint(self, checkpoint: Dict[str, Any]):
        """Guarda checkpoint de progreso."""
        checkpoint["last_updated"] = datetime.now().isoformat()

        checkpoint_path = Path(CHECKPOINT_FILE)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, indent=2, fp=f)

    def estimate_costs(self, balance_files: List[Path]) -> Dict[str, Any]:
        """
        Estima tokens y costos para la migración.

        Returns:
            Dict con estimaciones de tokens, chunks y costo
        """
        print("📊 Estimando costos...\n")

        # Guard clause: if no files to process
        if len(balance_files) == 0:
            print("   ⚠️  No hay archivos para procesar")
            return {
                "estimated_tokens": 0,
                "estimated_cost": 0.0,
                "estimated_chunks": 0
            }

        sample_size = min(3, len(balance_files))
        sample_files = balance_files[:sample_size]

        total_chunks = 0
        total_chars = 0

        for file_path in sample_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                balance_data = json.load(f)

            chunks = self.chunker.chunk_balance(balance_data)
            total_chunks += len(chunks)
            total_chars += sum(len(c.chunk_text) for c in chunks)

        # Extrapolación
        avg_chunks_per_file = total_chunks / sample_size if sample_size > 0 else 0
        avg_chars_per_chunk = total_chars / total_chunks if total_chunks > 0 else 0

        estimated_total_chunks = int(avg_chunks_per_file * len(balance_files))
        estimated_total_chars = int(
            avg_chars_per_chunk * estimated_total_chunks)

        # OpenAI tokens: ~4 chars = 1 token
        estimated_tokens = estimated_total_chars // 4
        estimated_cost = (estimated_tokens / 1_000_000) * 0.02

        print(f"   Archivos a procesar: {len(balance_files)}")
        print(f"   Chunks estimados: {estimated_total_chunks:,}")
        print(f"   Tokens estimados: {estimated_tokens:,}")
        print(f"   Costo estimado: ${estimated_cost:.4f}")
        print()

        return {
            "files": len(balance_files),
            "chunks": estimated_total_chunks,
            "tokens": estimated_tokens,
            "cost_usd": estimated_cost
        }

    def migrate(self, resume: bool = False) -> Dict[str, Any]:
        """
        Ejecuta migración completa.

        Args:
            resume: Si True, continúa desde último checkpoint

        Returns:
            Estadísticas de migración
        """
        # 1. Encontrar archivos
        balance_files = self.find_balance_files()

        if not balance_files:
            print("❌ No se encontraron Balances de Tesorería")
            return {}

        # 2. Cargar checkpoint si resume
        checkpoint = self.load_checkpoint() if resume else {
            "processed_files": 0,
            "processed_chunks": 0,
            "processed_file_paths": [],
            "last_updated": None
        }

        # 3. Filtrar archivos ya procesados
        if resume and checkpoint["processed_file_paths"]:
            processed_set = set(checkpoint["processed_file_paths"])
            balance_files = [f for f in balance_files if str(
                f) not in processed_set]
            print(f"📂 Resumiendo: {len(balance_files)} archivos restantes\n")

        # 4. Modo piloto: solo 1 archivo
        if self.pilot_mode:
            balance_files = balance_files[:1]
            print(
                f"🧪 MODO PILOTO: Procesando solo {len(balance_files)} archivo(s)\n")

        # 5. Estimar costos
        estimates = self.estimate_costs(balance_files)

        if not self.dry_run and not self.pilot_mode and not self.auto_approve:
            response = input(
                f"💰 Costo estimado: ${estimates['cost_usd']:.4f}. ¿Continuar? (y/n): ")
            if response.lower() != 'y':
                print("❌ Migración cancelada")
                return {}
        elif self.auto_approve and not self.pilot_mode:
            print(f"✅ Auto-aprobado (--yes): ${estimates['cost_usd']:.4f}")

        # 5. Procesar archivos
        print("\n" + "="*60)
        print("🚀 INICIANDO MIGRACIÓN")
        print("="*60 + "\n")

        all_chunks = []
        all_embeddings = []
        stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "points_uploaded": 0,
            "errors": []
        }

        for idx, file_path in enumerate(balance_files, start=1):
            try:
                print(
                    f"📄 [{idx}/{len(balance_files)}] Procesando: {file_path.name}")

                # Leer balance
                with open(file_path, 'r', encoding='utf-8') as f:
                    balance_data = json.load(f)

                # Generar chunks
                chunks = self.chunker.chunk_balance(balance_data)
                print(f"   ✓ {len(chunks)} chunks generados")

                # Filtrar chunks super largos (> 6000 chars = ~1500 tokens)
                MAX_CHUNK_CHARS = 6000
                filtered_chunks = []
                for chunk in chunks:
                    if len(chunk.chunk_text) > MAX_CHUNK_CHARS:
                        print(
                            f"   ⚠️  Truncando chunk {chunk.chunk_id} ({len(chunk.chunk_text)} → {MAX_CHUNK_CHARS} chars)")
                        chunk.chunk_text = chunk.chunk_text[:MAX_CHUNK_CHARS] + \
                            "\n\n[... truncado]"
                    filtered_chunks.append(chunk)

                # Generar embeddings UNO POR UNO (evita exceder límite de tokens por batch)
                embeddings = self.embedder.embed_chunks(
                    filtered_chunks,
                    batch_size=1,  # ← Cambio crítico: 1 chunk a la vez
                    show_progress=False
                )
                print(f"   ✓ {len(embeddings)} embeddings generados")

                all_chunks.extend(filtered_chunks)
                all_embeddings.extend(embeddings)

                stats["files_processed"] += 1
                stats["chunks_created"] += len(chunks)
                stats["embeddings_generated"] += len(embeddings)

                # Agregar archivo procesado a la lista del checkpoint
                checkpoint["processed_file_paths"].append(str(file_path))

                # Checkpoint cada 5 archivos
                if idx % 5 == 0 or idx == len(balance_files) - 1:
                    checkpoint["processed_files"] = len(
                        checkpoint["processed_file_paths"])
                    checkpoint["processed_chunks"] = stats["chunks_created"]
                    checkpoint["last_updated"] = datetime.now().isoformat()
                    self.save_checkpoint(checkpoint)
                    print(
                        f"   💾 Checkpoint guardado: {len(checkpoint['processed_file_paths'])} archivos")

                print()

            except Exception as e:
                logger.error(f"Error procesando {file_path}: {e}")
                stats["errors"].append(
                    {"file": str(file_path), "error": str(e)})
                continue

        # 6. Subir a Qdrant
        if not self.dry_run and all_chunks and all_embeddings:
            print("\n" + "="*60)
            print("☁️  SUBIENDO A QDRANT CLOUD")
            print("="*60 + "\n")

            points = []
            for chunk, embedding_result in zip(all_chunks, all_embeddings):
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding_result.embedding,
                    payload={
                        "chunk_text": chunk.chunk_text,
                        "chunk_type": chunk.chunk_type,
                        "chunk_id": chunk.chunk_id,
                        "municipio": chunk.metadata.get("municipio"),
                        "tipo_documento": chunk.metadata.get("tipo_documento"),
                        "tipo_detalle": chunk.metadata.get("tipo_detalle"),
                        "periodo": chunk.metadata.get("periodo"),
                        "fecha_documento": chunk.metadata.get("fecha_documento"),
                        "is_executive_summary": chunk.metadata.get("is_executive_summary", False),
                        "contains_key_numbers": chunk.metadata.get("contains_key_numbers", False),
                        "source": "balance_migration_v1"
                    }
                ))

            # Upload en batches de 100
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch
                )
                print(
                    f"   ✓ Batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size} subido ({len(batch)} points)")

            stats["points_uploaded"] = len(points)

        # 7. Verificación final
        if not self.dry_run and self.qdrant:
            print("\n" + "="*60)
            print("✅ VERIFICACIÓN FINAL")
            print("="*60 + "\n")

            collection_info = self.qdrant.get_collection(COLLECTION_NAME)
            print(
                f"   Total points en colección: {collection_info.points_count:,}")
            print(
                f"   Puntos agregados en esta migración: {stats['points_uploaded']:,}")

        # 8. Resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE MIGRACIÓN")
        print("="*60 + "\n")
        print(
            f"   Archivos procesados: {stats['files_processed']}/{len(balance_files)}")
        print(f"   Chunks creados: {stats['chunks_created']:,}")
        print(f"   Embeddings generados: {stats['embeddings_generated']:,}")
        print(f"   Points subidos: {stats['points_uploaded']:,}")
        print(f"   Tokens usados: {self.embedder.total_tokens_used:,}")
        print(
            f"   Costo real: ${self.embedder.estimate_cost(self.embedder.total_tokens_used):.4f}")

        if stats["errors"]:
            print(f"\n⚠️  Errores: {len(stats['errors'])}")
            for error in stats["errors"]:
                print(f"     - {error['file']}: {error['error']}")

        print()

        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migra Balances de Tesorería a Qdrant Cloud con embeddings OpenAI"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula migración sin subir a Qdrant"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continúa desde último checkpoint"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Modo piloto: migra solo 1 archivo para validación empresarial"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Aprobar automáticamente (sin pedir confirmación)"
    )

    args = parser.parse_args()

    mode_str = "PILOTO" if args.pilot else (
        "DRY-RUN" if args.dry_run else "PRODUCCIÓN")

    print("\n" + "="*60)
    print(f"🏦 MIGRACIÓN: BALANCES DE TESORERÍA → QDRANT CLOUD ({mode_str})")
    print("="*60 + "\n")

    try:
        migrator = BalanceMigrator(
            dry_run=args.dry_run,
            pilot_mode=args.pilot,
            auto_approve=args.yes
        )
        stats = migrator.migrate(resume=args.resume)

        if stats:
            print("✅ Migración completada exitosamente\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Migración interrumpida por usuario")
        print("   Usa --resume para continuar desde último checkpoint\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}\n")
        logger.exception("Error en migración")
        sys.exit(1)


if __name__ == "__main__":
    main()
