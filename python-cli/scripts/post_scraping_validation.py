#!/usr/bin/env python3
"""
Post-Scraping Validation Hook - SIBOM Scraper Assistant
Valida automáticamente los resultados del scraping y genera reportes de calidad

Uso:
    python post_scraping_validation.py
    python post_scraping_validation.py --directory boletines/
    python post_scraping_validation.py --verbose
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import re


class PostScrapingValidator:
    def __init__(self, directory: str = "boletines", verbose: bool = False):
        self.directory = Path(directory)
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'total_normas': 0,
            'total_montos': 0,
            'total_tablas': 0,
            'municipalities': set(),
            'years': set(),
            'error_types': Counter()
        }

    def validate_directory(self) -> bool:
        """Valida todos los archivos JSON en el directorio"""

        print(f"\n{'='*60}")
        print("POST-SCRAPING VALIDATION")
        print(f"{'='*60}")
        print(f"\n📁 Directorio: {self.directory}")
        print(f"🔍 Buscando archivos JSON...\n")

        # Find all JSON files (excluding progress files)
        json_files = sorted(
            [f for f in self.directory.glob('*.json') if not f.name.startswith('.progress')]
        )

        if not json_files:
            print("❌ No se encontraron archivos JSON para validar")
            return False

        self.stats['total_files'] = len(json_files)
        print(f"✓ Encontrados {len(json_files)} archivos\n")

        # Validate each file
        for i, file_path in enumerate(json_files, 1):
            if self.verbose:
                print(f"[{i}/{len(json_files)}] Validando {file_path.name}...")

            self.validate_bulletin_file(file_path)

            # Progress update
            if not self.verbose and i % 50 == 0:
                print(f"  Progreso: {i}/{len(json_files)} ({i/len(json_files)*100:.1f}%)")

        return len(self.errors) == 0

    def validate_bulletin_file(self, file_path: Path):
        """Valida un archivo de boletín individual"""

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            structure_valid = self._validate_structure(data, file_path)
            if not structure_valid:
                self.stats['invalid_files'] += 1
                return

            # Validate content
            content_valid = self._validate_content(data, file_path)
            if not content_valid:
                self.stats['invalid_files'] += 1
                return

            # Update statistics
            self._update_statistics(data)

            self.stats['valid_files'] += 1

        except json.JSONDecodeError as e:
            error_msg = f"JSON inválido en {file_path.name}: {e}"
            self.errors.append(error_msg)
            self.stats['error_types']['json_decode'] += 1
            self.stats['invalid_files'] += 1

        except Exception as e:
            error_msg = f"Error procesando {file_path.name}: {e}"
            self.errors.append(error_msg)
            self.stats['error_types']['unknown'] += 1
            self.stats['invalid_files'] += 1

    def _validate_structure(self, data: Dict, file_path: Path) -> bool:
        """Valida estructura del boletín"""

        required_fields = [
            'municipio', 'numero_boletin', 'fecha_boletin',
            'boletin_url', 'status', 'normas'
        ]

        for field in required_fields:
            if field not in data:
                error_msg = f"{file_path.name}: Campo requerido '{field}' faltante"
                self.errors.append(error_msg)
                self.stats['error_types']['missing_field'] += 1
                return False

        # Validate normas is a list
        if not isinstance(data['normas'], list):
            error_msg = f"{file_path.name}: 'normas' debe ser una lista"
            self.errors.append(error_msg)
            self.stats['error_types']['invalid_structure'] += 1
            return False

        # Check for empty normas
        if len(data['normas']) == 0:
            warning_msg = f"{file_path.name}: Lista de normas vacía"
            self.warnings.append(warning_msg)
            self.stats['error_types']['empty_normas'] += 1

        return True

    def _validate_content(self, data: Dict, file_path: Path) -> bool:
        """Valida contenido del boletín y normas"""

        # Validate each normativa
        for i, norma in enumerate(data['normas']):
            if not isinstance(norma, dict):
                error_msg = f"{file_path.name}: Norma {i} no es un diccionario"
                self.errors.append(error_msg)
                self.stats['error_types']['invalid_norma'] += 1
                return False

            # Check required fields in norma
            norma_required = ['id', 'tipo', 'numero', 'titulo', 'fecha', 'contenido']
            for field in norma_required:
                if field not in norma:
                    error_msg = f"{file_path.name}: Norma {i} - Campo '{field}' faltante"
                    self.errors.append(error_msg)
                    self.stats['error_types']['norma_missing_field'] += 1
                    return False

            # Validate content quality
            contenido = norma.get('contenido', '')
            if not contenido or not contenido.strip():
                warning_msg = f"{file_path.name}: Norma {i} ({norma.get('numero')}) - Contenido vacío"
                self.warnings.append(warning_msg)
                self.stats['error_types']['empty_content'] += 1

            elif len(contenido) < 100:
                warning_msg = f"{file_path.name}: Norma {i} ({norma.get('numero')}) - Contenido muy corto ({len(contenido)} chars)"
                self.warnings.append(warning_msg)
                self.stats['error_types']['short_content'] += 1

        # Check for duplicate normativa IDs
        ids = [n.get('id') for n in data['normas'] if 'id' in n]
        if len(ids) != len(set(ids)):
            warning_msg = f"{file_path.name}: IDs de normas duplicados encontrados"
            self.warnings.append(warning_msg)
            self.stats['error_types']['duplicate_ids'] += 1

        # Check for duplicate normativa numbers within bulletin
        numbers = [n.get('numero') for n in data['normas'] if 'numero' in n]
        if len(numbers) != len(set(numbers)):
            warning_msg = f"{file_path.name}: Números de normas duplicados encontrados"
            self.warnings.append(warning_msg)
            self.stats['error_types']['duplicate_numbers'] += 1

        return True

    def _update_statistics(self, data: Dict):
        """Actualiza estadísticas globales"""

        # Municipality
        if 'municipio' in data:
            self.stats['municipalities'].add(data['municipio'])

        # Year from date
        if 'fecha_boletin' in data:
            date_str = data['fecha_boletin']
            try:
                year = int(date_str.split('/')[-1])
                self.stats['years'].add(year)
            except:
                pass

        # Normas count
        if 'normas' in data:
            self.stats['total_normas'] += len(data['normas'])

            # Extract metadata
            for norma in data['normas']:
                if 'montos_extraidos' in norma and norma['montos_extraidos']:
                    self.stats['total_montos'] += len(norma['montos_extraidos'])

                if 'tablas' in norma and norma['tablas']:
                    self.stats['total_tablas'] += len(norma['tablas'])

    def check_integrity_with_index(self, index_file: str = "boletines_index.json") -> bool:
        """Verifica integridad referencial con el índice"""

        print(f"\n📋 Verificando integridad con índice...\n")

        if not Path(index_file).exists():
            print(f"⚠️  Índice no encontrado: {index_file}")
            return True  # Not critical, skip

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)

            # Check that index is a list
            if not isinstance(index, list):
                error_msg = f"Índice inválido: debe ser una lista"
                self.errors.append(error_msg)
                return False

            # Count bulletins in index
            index_count = len(index)
            file_count = self.stats['valid_files']

            print(f"  Índice: {index_count} entradas")
            print(f"  Archivos: {file_count} archivos válidos")

            # Check for discrepancies
            if index_count != file_count:
                warning_msg = f"Discrepancia entre índice ({index_count}) y archivos ({file_count})"
                self.warnings.append(warning_msg)
                self.stats['error_types']['index_mismatch'] += 1

            # Check for missing files referenced in index
            indexed_files = set()
            for entry in index:
                if 'filename' in entry:
                    indexed_files.add(entry['filename'])

            for filename in indexed_files:
                if not (self.directory / filename).exists():
                    warning_msg = f"Archivo en índice no existe: {filename}"
                    self.warnings.append(warning_msg)
                    self.stats['error_types']['missing_file'] += 1

            # Check for orphaned files
            actual_files = set(f.name for f in self.directory.glob('*.json') if not f.name.startswith('.progress'))
            indexed_files_only = set(f for f in indexed_files if f.endswith('.json'))
            orphaned = actual_files - indexed_files_only

            if orphaned:
                warning_msg = f"Archivos huérfanos (no en índice): {len(orphaned)} archivos"
                self.warnings.append(warning_msg)
                self.stats['error_types']['orphaned_files'] += 1
                if self.verbose:
                    for filename in orphaned:
                        print(f"    - {filename}")

            return True

        except Exception as e:
            error_msg = f"Error verificando integridad con índice: {e}"
            self.errors.append(error_msg)
            return False

    def check_data_quality(self) -> bool:
        """Realiza análisis de calidad de datos"""

        print(f"\n🔬 Analizando calidad de datos...\n")

        quality_issues = []

        # Check municipality distribution
        if self.stats['municipalities']:
            print(f"  Municipios únicos: {len(self.stats['municipalities'])}")
            for municipio in sorted(self.stats['municipalities']):
                municipio_files = list(self.directory.glob(f"{municipio}_*.json"))
                print(f"    - {municipio}: {len(municipio_files)} archivos")

        # Check year distribution
        if self.stats['years']:
            print(f"\n  Años cubiertos: {len(self.stats['years'])}")
            for year in sorted(self.stats['years']):
                year_files = [f for f in self.directory.glob('*.json')
                             if year in str(f) and not f.name.startswith('.progress')]
                print(f"    - {year}: {len(year_files)} archivos")

            # Check for unusual years
            current_year = datetime.now().year
            unusual_years = [y for y in self.stats['years'] if y < 2010 or y > current_year + 1]
            if unusual_years:
                warning_msg = f"Años inusuales detectados: {unusual_years}"
                self.warnings.append(warning_msg)
                self.stats['error_types']['unusual_years'] += 1
                quality_issues.append(warning_msg)

        # Check normas distribution
        if self.stats['total_files'] > 0:
            avg_normas = self.stats['total_normas'] / self.stats['total_files']
            print(f"\n  Normas por boletín (promedio): {avg_normas:.1f}")

            if avg_normas < 5:
                warning_msg = f"Promedio de normas muy bajo ({avg_normas:.1f} por boletín)"
                self.warnings.append(warning_msg)
                self.stats['error_types']['low_norma_count'] += 1
                quality_issues.append(warning_msg)

        # Check extracted data
        print(f"\n  Montos extraídos: {self.stats['total_montos']}")
        print(f"  Tablas extraídas: {self.stats['total_tablas']}")

        if self.stats['total_montos'] == 0 and self.stats['total_normas'] > 100:
            warning_msg = "No se extrajeron montos (posiblemente no se ejecutó monto_extractor.py)"
            self.warnings.append(warning_msg)
            self.stats['error_types']['missing_montos'] += 1
            quality_issues.append(warning_msg)

        return len(quality_issues) == 0

    def print_report(self):
        """Imprime reporte de validación"""

        print(f"\n{'='*60}")
        print("REPORTE DE VALIDACIÓN")
        print(f"{'='*60}\n")

        # Statistics
        print(f"📊 ESTADÍSTICAS:")
        print(f"  Archivos totales: {self.stats['total_files']}")
        print(f"  Archivos válidos: {self.stats['valid_files']}")
        print(f"  Archivos inválidos: {self.stats['invalid_files']}")
        print(f"  Total normas: {self.stats['total_normas']}")
        print(f"  Municipios: {len(self.stats['municipalities'])}")
        print(f"  Años cubiertos: {len(self.stats['years'])}")

        # Errors
        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for error in self.errors[:30]:  # Limit to first 30
                print(f"  • {error}")
            if len(self.errors) > 30:
                print(f"  ... y {len(self.errors) - 30} errores más")
        else:
            print(f"\n✅ No se encontraron errores")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings[:30]:  # Limit to first 30
                print(f"  • {warning}")
            if len(self.warnings) > 30:
                print(f"  ... y {len(self.warnings) - 30} advertencias más")
        else:
            print(f"\n✅ No se encontraron advertencias")

        # Error types
        if self.stats['error_types']:
            print(f"\n📋 TIPOS DE ERRORES:")
            for error_type, count in self.stats['error_types'].most_common():
                print(f"  • {error_type}: {count}")

        # Final status
        print(f"\n{'='*60}")
        if not self.errors and not self.warnings:
            print("✅ VALIDACIÓN EXITOSA - Datos en excelente estado")
            print(f"{'='*60}")
        elif not self.errors:
            print("✅ VALIDACIÓN EXITOSA - Solo advertencias menores")
            print(f"{'='*60}")
        else:
            print("❌ VALIDACIÓN FALLIDA - Se encontraron errores críticos")
            print(f"{'='*60}")

    def save_report(self, output_file: str = "validation_report.json"):
        """Guarda reporte en formato JSON"""

        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': {
                'total_files': self.stats['total_files'],
                'valid_files': self.stats['valid_files'],
                'invalid_files': self.stats['invalid_files'],
                'total_normas': self.stats['total_normas'],
                'total_montos': self.stats['total_montos'],
                'total_tablas': self.stats['total_tablas'],
                'municipalities': sorted(list(self.stats['municipalities'])),
                'years': sorted(list(self.stats['years'])),
                'error_types': dict(self.stats['error_types'])
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'valid' if not self.errors else 'invalid'
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Reporte guardado en: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Validación post-scraping para SIBOM')
    parser.add_argument('--directory', default='boletines', help='Directorio con archivos JSON')
    parser.add_argument('--index', default='boletines_index.json', help='Archivo de índice')
    parser.add_argument('--output', default='validation_report.json', help='Archivo de reporte de salida')
    parser.add_argument('--verbose', action='store_true', help='Modo verboso')
    parser.add_argument('--no-index-check', action='store_true', help='Saltar verificación de índice')

    args = parser.parse_args()

    # Create validator
    validator = PostScrapingValidator(args.directory, args.verbose)

    # Validate directory
    valid = validator.validate_directory()

    # Check integrity with index
    if not args.no_index_check:
        valid_index = validator.check_integrity_with_index(args.index)
        valid = valid and valid_index

    # Check data quality
    valid_quality = validator.check_data_quality()
    valid = valid and valid_quality

    # Print report
    validator.print_report()

    # Save report
    validator.save_report(args.output)

    # Exit code
    sys.exit(0 if valid else 1)


if __name__ == '__main__':
    main()
