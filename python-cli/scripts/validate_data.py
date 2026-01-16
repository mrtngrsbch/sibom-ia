#!/usr/bin/env python3
"""
Validador de datos JSON para SIBOM Scraper Assistant
Valida estructura, integridad y calidad de datos scrapeados

Uso:
    python validate_data.py --file=boletines/Adolfo_Alsina_1.json
    python validate_data.py --file=boletines_index.json --type=index
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class DataValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_documents': 0,
            'valid_documents': 0,
            'invalid_documents': 0,
            'missing_fields': 0,
            'empty_content': 0
        }

    def validate_index_file(self, file_path: str) -> bool:
        """Valida el archivo de índice principal"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                self.errors.append("El índice debe ser un array de documentos")
                return False

            self.stats['total_documents'] = len(data)

            for i, doc in enumerate(data):
                self._validate_index_entry(doc, i)

            return len(self.errors) == 0

        except json.JSONDecodeError as e:
            self.errors.append(f"JSON inválido: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {file_path}")
            return False

    def _validate_index_entry(self, doc: Dict[str, Any], index: int):
        """Valida una entrada individual del índice"""
        required_fields = ['id', 'municipality', 'type', 'number', 'title', 'date', 'url', 'status', 'filename']

        for field in required_fields:
            if field not in doc:
                self.errors.append(f"Documento {index}: Campo requerido '{field}' faltante")
                self.stats['missing_fields'] += 1
            elif not doc[field] or (isinstance(doc[field], str) and not doc[field].strip()):
                self.warnings.append(f"Documento {index}: Campo '{field}' está vacío")

        # Validaciones específicas
        if 'date' in doc:
            self._validate_date_format(doc['date'], index)

        if 'type' in doc:
            self._validate_document_type(doc['type'], index)

        if 'url' in doc:
            self._validate_url_format(doc['url'], index)

        if 'filename' in doc:
            self._validate_filename(doc['filename'], index)

    def validate_bulletin_file(self, file_path: str) -> bool:
        """Valida un archivo de boletín individual"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Estructura esperada del boletín
            required_fields = ['municipio', 'numero_boletin', 'fecha_boletin', 'boletin_url', 'status']

            for field in required_fields:
                if field not in data:
                    self.errors.append(f"Campo requerido '{field}' faltante")
                    self.stats['missing_fields'] += 1

            # Validar lista de normas
            if 'normas' in data:
                if not isinstance(data['normas'], list):
                    self.errors.append("El campo 'normas' debe ser un array")
                else:
                    for i, norma in enumerate(data['normas']):
                        self._validate_norma_entry(norma, i)

            return len(self.errors) == 0

        except json.JSONDecodeError as e:
            self.errors.append(f"JSON inválido: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {file_path}")
            return False

    def _validate_norma_entry(self, norma: Dict[str, Any], index: int):
        """Valida una entrada individual de norma"""
        required_fields = ['id', 'tipo', 'numero', 'titulo', 'fecha', 'municipio', 'url', 'contenido']

        for field in required_fields:
            if field not in norma:
                self.warnings.append(f"Norma {index}: Campo '{field}' faltante")

        # Validar contenido
        if 'contenido' in norma:
            content = norma['contenido']
            if not content or not content.strip():
                self.warnings.append(f"Norma {index}: Contenido vacío")
            elif len(content) < 100:
                self.warnings.append(f"Norma {index}: Contenido muy corto ({len(content)} caracteres)")

    def _validate_date_format(self, date_str: str, index: int):
        """Valida formato de fecha DD/MM/YYYY"""
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, date_str):
            self.warnings.append(f"Documento {index}: Formato de fecha inválido '{date_str}'. Esperado: DD/MM/YYYY")
        else:
            try:
                day, month, year = map(int, date_str.split('/'))
                from datetime import datetime
                datetime(year, month, day)

                # Validar rango razonable
                if year < 2010 or year > 2030:
                    self.warnings.append(f"Documento {index}: Año {year} fuera del rango esperado (2010-2030)")

            except ValueError:
                self.errors.append(f"Documento {index}: Fecha inválida '{date_str}'")

    def _validate_document_type(self, doc_type: str, index: int):
        """Valida tipo de documento"""
        valid_types = ['ordenanza', 'decreto', 'boletin', 'resolucion', 'disposicion', 'convenio', 'licitacion']
        if doc_type.lower() not in valid_types:
            self.warnings.append(f"Documento {index}: Tipo '{doc_type}' no reconocido. Tipos válidos: {valid_types}")

    def _validate_url_format(self, url: str, index: int):
        """Valida formato de URL"""
        if not url.startswith(('http://', 'https://', '/')):
            self.errors.append(f"Documento {index}: URL inválida '{url}'")

        # Validar que sea URL de SIBOM
        if url.startswith('http') and 'sibom.slyt.gba.gob.ar' not in url:
            self.warnings.append(f"Documento {index}: URL no es de SIBOM '{url}'")

    def _validate_filename(self, filename: str, index: int):
        """Valida nombre de archivo"""
        if not filename.endswith('.json'):
            self.errors.append(f"Documento {index}: Filename debe terminar en .json '{filename}'")

        # Validar que el archivo existe
        file_path = Path('boletines') / filename
        if not file_path.exists():
            self.warnings.append(f"Documento {index}: Archivo referenciado no existe '{filename}'")

    def print_report(self, file_path: str = ""):
        """Imprime reporte de validación"""
        print("\n" + "="*60)
        print("REPORTE DE VALIDACIÓN DE DATOS")
        if file_path:
            print(f"Archivo: {file_path}")
        print("="*60)

        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Total documentos: {self.stats['total_documents']}")
        print(f"  Documentos válidos: {self.stats['valid_documents']}")
        print(f"  Documentos inválidos: {self.stats['invalid_documents']}")
        print(f"  Campos faltantes: {self.stats['missing_fields']}")
        print(f"  Contenido vacío: {self.stats['empty_content']}")

        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for error in self.errors[:20]:  # Limit to first 20 errors
                print(f"  • {error}")
            if len(self.errors) > 20:
                print(f"  ... y {len(self.errors) - 20} errores más")

        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings[:20]:  # Limit to first 20 warnings
                print(f"  • {warning}")
            if len(self.warnings) > 20:
                print(f"  ... y {len(self.warnings) - 20} advertencias más")

        if not self.errors and not self.warnings:
            print("\n✅ VALIDACIÓN EXITOSA - No se encontraron problemas")
        elif not self.errors:
            print("\n✅ VALIDACIÓN EXITOSA - Solo advertencias menores")
        else:
            print("\n❌ VALIDACIÓN FALLIDA - Se encontraron errores críticos")

        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Validador de datos JSON para SIBOM')
    parser.add_argument('--file', required=True, help='Archivo JSON a validar')
    parser.add_argument('--type', choices=['index', 'bulletin'], help='Tipo de archivo (auto-detectado si no se especifica)')

    args = parser.parse_args()

    validator = DataValidator()

    # Auto-detectar tipo de archivo
    file_path = Path(args.file)
    if args.type:
        file_type = args.type
    elif file_path.name == 'boletines_index.json':
        file_type = 'index'
    elif file_path.parent.name == 'boletines':
        file_type = 'bulletin'
    else:
        print(f"❌ No se pudo determinar el tipo de archivo: {file_path}")
        sys.exit(1)

    # Validar según tipo
    if file_type == 'index':
        success = validator.validate_index_file(str(file_path))
    else:
        success = validator.validate_bulletin_file(str(file_path))

    # Actualizar estadísticas
    if success:
        validator.stats['valid_documents'] = 1
    else:
        validator.stats['invalid_documents'] = 1

    # Imprimir reporte
    validator.print_report(str(file_path))

    # Exit code para CI/CD
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
