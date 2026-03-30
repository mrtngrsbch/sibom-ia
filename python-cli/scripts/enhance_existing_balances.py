#!/usr/bin/env python3
"""
enhance_existing_balances.py

Actualiza archivos Balance existentes con mejoras de Layer 1 y Layer 2:
- Layer 1 (BalanceExtractor): Agrega resumen_ejecutivo_numerico
- Layer 2 (HierarchicalChunker): Actualiza rag_chunks con formato TIER-1/2/3

Uso:
    python scripts/enhance_existing_balances.py --all
    python scripts/enhance_existing_balances.py --municipality "Carlos Tejedor"
    python scripts/enhance_existing_balances.py --file boletines/X/file.json
    python scripts/enhance_existing_balances.py --all --overwrite

@created 2026-02-15
@author SIBOM IA
"""

from services.hierarchical_chunker import HierarchicalChunker, compatibility_wrapper
from extractors.balance_extractor import BalanceExtractor
import sys
import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import shutil
from datetime import datetime

# Agregar python-cli al path
sys.path.insert(0, str(Path(__file__).parent.parent))


class BalanceEnhancer:
    """Mejora archivos Balance con Layer 1 y Layer 2"""

    def __init__(self, verbose: bool = True, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.balance_extractor = BalanceExtractor(verbose=verbose)
        self.hierarchical_chunker = HierarchicalChunker(verbose=verbose)

        self.stats = {
            'total_files': 0,
            'enhanced': 0,
            'skipped': 0,
            'errors': 0,
            'already_enhanced': 0,
        }

    def find_balance_files(self, municipality: str = None) -> List[Path]:
        """
        Encuentra archivos Balance en boletines/

        Args:
            municipality: Filtrar por municipio (None = todos)
                         Nota: Los espacios se convierten a guiones bajos automáticamente

        Returns:
            Lista de paths a archivos Balance JSON
        """
        boletines_dir = Path(__file__).parent.parent / 'boletines'

        if not boletines_dir.exists():
            print(f"❌ Error: Directorio {boletines_dir} no existe")
            return []

        # Normalizar nombre de municipio (reemplazar espacios por guiones bajos)
        if municipality:
            municipality = municipality.replace(' ', '_')

        balance_files = []

        # Buscar en todos los municipios o uno específico
        search_dirs = [
            boletines_dir / municipality] if municipality else list(boletines_dir.iterdir())

        for muni_dir in search_dirs:
            if not muni_dir.is_dir():
                continue

            # Buscar archivos que contengan "Balances" en el nombre
            for file_path in muni_dir.glob('*Balances*.json'):
                balance_files.append(file_path)

        return sorted(balance_files)

    def is_already_enhanced(self, doc_data: Dict[str, Any]) -> bool:
        """
        Verifica si el archivo ya tiene las mejoras aplicadas.

        Criterios:
        - Tiene resumen_ejecutivo_numerico (Layer 1)
        - rag_chunks tiene al menos 1 chunk con tier=1 (Layer 2)
        """
        # Check Layer 1
        has_layer1 = 'resumen_ejecutivo_numerico' in doc_data

        # Check Layer 2
        has_layer2 = False
        if 'rag_chunks' in doc_data and doc_data['rag_chunks']:
            # Verificar si algún chunk tiene tier=1
            for chunk in doc_data['rag_chunks']:
                if isinstance(chunk, dict) and chunk.get('tier') == 1:
                    has_layer2 = True
                    break

        return has_layer1 and has_layer2

    def enhance_file(self, file_path: Path, overwrite: bool = False) -> bool:
        """
        Mejora un archivo Balance con Layer 1 y Layer 2.

        Args:
            file_path: Ruta al archivo JSON
            overwrite: Si False y el archivo ya tiene mejoras, lo salta

        Returns:
            True si se mejoró exitosamente
        """
        try:
            # 1. Cargar archivo
            if self.verbose:
                print(f"\n📄 Procesando: {file_path.name}")

            with open(file_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)

            # 2. Verificar si ya está mejorado
            if not overwrite and self.is_already_enhanced(doc_data):
                if self.verbose:
                    print(f"  ✅ Ya tiene mejoras (Layer 1+2), saltando...")
                self.stats['already_enhanced'] += 1
                return False

            # Crear backup si no es dry run
            if not self.dry_run:
                backup_path = file_path.with_suffix('.json.bak')
                shutil.copy2(file_path, backup_path)
                if self.verbose:
                    print(f"  📦 Backup creado: {backup_path.name}")

            # 3. Layer 1 - Extraer resumen ejecutivo
            if self.verbose:
                print(f"  🔧 Layer 1: Extrayendo resumen ejecutivo...")

            summary = self.balance_extractor.extract(doc_data)
            doc_data['resumen_ejecutivo_numerico'] = summary.to_dict()

            if self.verbose:
                extracted_count = summary.campos_extraidos
                total_fields = 7  # Total de campos críticos
                print(
                    f"     Extraídos: {extracted_count}/{total_fields} campos")
                if summary.saldo_inicial:
                    print(f"     Saldo Inicial: ${summary.saldo_inicial:,.2f}")
                if summary.saldo_final:
                    print(f"     Saldo Final: ${summary.saldo_final:,.2f}")

            # 4. Layer 2 - Generar chunks jerárquicos
            if self.verbose:
                print(f"  🔧 Layer 2: Generando chunks TIER-1/2/3...")

            hierarchical_chunks = self.hierarchical_chunker.chunk_balance(
                doc_data)

            # Convertir a formato compatible
            doc_data['rag_chunks'] = compatibility_wrapper(hierarchical_chunks)

            if self.verbose:
                tier1_count = sum(
                    1 for c in hierarchical_chunks if c.tier == 1)
                tier2_count = sum(
                    1 for c in hierarchical_chunks if c.tier == 2)
                tier3_count = sum(
                    1 for c in hierarchical_chunks if c.tier == 3)
                print(f"     Chunks generados: {len(hierarchical_chunks)}")
                print(
                    f"     TIER-1: {tier1_count}, TIER-2: {tier2_count}, TIER-3: {tier3_count}")

            # 5. Actualizar metadata
            doc_data.setdefault('metadata', {})
            doc_data['metadata']['enhanced_date'] = datetime.now().isoformat()
            doc_data['metadata']['enhanced_layers'] = [
                'layer1_balance_extractor', 'layer2_hierarchical_chunks']

            # 6. Guardar archivo actualizado
            if self.dry_run:
                if self.verbose:
                    print(f"  🔍 [DRY RUN] No se guardaron cambios")
                self.stats['enhanced'] += 1
                return True

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)

            if self.verbose:
                print(f"  ✅ Archivo actualizado exitosamente")

            self.stats['enhanced'] += 1
            return True

        except Exception as e:
            print(f"  ❌ Error procesando {file_path.name}: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            self.stats['errors'] += 1
            return False

    def enhance_all(self, municipality: str = None, file_path: str = None,
                    overwrite: bool = False) -> None:
        """
        Mejora todos los archivos Balance encontrados.

        Args:
            municipality: Filtrar por municipio (None = todos)
            file_path: Procesar solo un archivo específico
            overwrite: Sobrescribir archivos ya mejorados
        """
        print("🚀 ENHANCE EXISTING BALANCES - Layer 1 + Layer 2")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if self.dry_run:
            print("🔍 [DRY RUN MODE] No se guardarán cambios")
            print()

        # Buscar archivos
        if file_path:
            # Procesar un solo archivo
            target_file = Path(file_path)
            if not target_file.exists():
                print(f"❌ Error: Archivo {file_path} no existe")
                return
            files = [target_file]
        else:
            # Buscar todos los archivos Balance
            files = self.find_balance_files(municipality)

        if not files:
            print(f"❌ No se encontraron archivos Balance")
            if municipality:
                print(f"   Municipio filtrado: {municipality}")
            print(f"   Directorio buscado: boletines/")
            return

        self.stats['total_files'] = len(files)

        print(f"📊 Archivos encontrados: {len(files)}")
        if municipality:
            print(f"   Municipio: {municipality}")
        if overwrite:
            print(f"   Modo: OVERWRITE (actualizará archivos ya mejorados)")
        else:
            print(f"   Modo: SKIP (saltará archivos ya mejorados)")
        print()

        # Procesar cada archivo
        for i, file_path in enumerate(files, 1):
            # Mostrar path relativo si es posible, sino absoluto
            try:
                display_path = file_path.relative_to(Path.cwd())
            except ValueError:
                display_path = file_path
            print(f"[{i}/{len(files)}] {display_path}")
            self.enhance_file(file_path, overwrite=overwrite)

        # Resumen final
        print()
        print("=" * 60)
        print("📊 RESUMEN DE EJECUCIÓN")
        print("=" * 60)
        print(f"Total archivos procesados: {self.stats['total_files']}")
        print(f"✅ Mejorados exitosamente:  {self.stats['enhanced']}")
        print(f"⏭️  Ya tenían mejoras:       {self.stats['already_enhanced']}")
        print(f"❌ Errores:                 {self.stats['errors']}")

        if self.stats['enhanced'] > 0:
            print()
            print("🎉 Mejoras aplicadas:")
            print("   - Layer 1: resumen_ejecutivo_numerico agregado")
            print("   - Layer 2: rag_chunks actualizados con TIER-1/2/3")
            print()
            print("💡 Próximos pasos:")
            print(
                "   1. Re-migrar a Qdrant: python scripts/migrate_balances_to_qdrant.py --yes")
            print("   2. Test en chatbot: cd ../chatbot && pnpm run dev")


def main():
    parser = argparse.ArgumentParser(
        description='Mejora archivos Balance con Layer 1 y Layer 2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  # Mejorar todos los archivos Balance
  python scripts/enhance_existing_balances.py --all
  
  # Mejorar solo un municipio
  python scripts/enhance_existing_balances.py --municipality "Carlos Tejedor"
  
  # Mejorar un archivo específico
  python scripts/enhance_existing_balances.py --file boletines/Azul/Azul_Balances_xxx.json
  
  # Forzar actualización de archivos ya mejorados
  python scripts/enhance_existing_balances.py --all --overwrite
  
  # Dry run (no guardar cambios)
  python scripts/enhance_existing_balances.py --all --dry-run
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Procesar todos los archivos Balance'
    )

    parser.add_argument(
        '--municipality',
        type=str,
        help='Procesar solo archivos de un municipio específico'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Procesar un archivo específico'
    )

    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Sobrescribir archivos que ya tienen mejoras'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Modo simulación (no guardar cambios)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Modo silencioso (menos output)'
    )

    args = parser.parse_args()

    # Validar argumentos
    if not (args.all or args.municipality or args.file):
        parser.error("Debe especificar --all, --municipality o --file")

    # Crear enhancer
    enhancer = BalanceEnhancer(
        verbose=not args.quiet,
        dry_run=args.dry_run
    )

    # Ejecutar
    enhancer.enhance_all(
        municipality=args.municipality,
        file_path=args.file,
        overwrite=args.overwrite
    )


if __name__ == '__main__':
    main()
