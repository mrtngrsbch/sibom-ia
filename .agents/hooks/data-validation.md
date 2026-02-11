# Hook de Validación de Datos - SIBOM Scraper Assistant

## Configuración del Hook

### Trigger Event
**Evento:** `onFileSave`
**Archivos objetivo:** `python-cli/boletines/*.json`, `python-cli/boletines_index.json`
**Descripción:** Valida automáticamente la integridad y estructura de datos JSON generados por el scraper

### Configuración del Hook
```json
{
  "name": "data-validation",
  "description": "Valida automáticamente archivos JSON generados por el scraper",
  "trigger": {
    "event": "onFileSave",
    "filePattern": "python-cli/boletines/**/*.json"
  },
  "actions": [
    {
      "type": "shellCommand",
      "command": "python validate_data.py --file={{file.path}}",
      "workingDirectory": "python-cli",
      "condition": "file.name.endsWith('.json')"
    },
    {
      "type": "agentMessage",
      "message": "🔍 Validando estructura de datos en {{file.name}}...",
      "condition": "always"
    }
  ],
  "enabled": true
}
```

## Script de Validación de Datos

### Validador Principal
**Ubicación:** `python-cli/validate_data.py`
```python
#!/usr/bin/env python3
"""
Validador de datos JSON para SIBOM Scraper Assistant
Valida estructura, integridad y calidad de datos scrapeados
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
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
    
    def validate_document_file(self, file_path: str) -> bool:
        """Valida un archivo de documento individual"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Estructura esperada del documento
            required_fields = ['id', 'municipality', 'type', 'number', 'title', 'date', 'url', 'status', 'fullText']
            
            for field in required_fields:
                if field not in data:
                    self.errors.append(f"Campo requerido '{field}' faltante")
                    self.stats['missing_fields'] += 1
            
            # Validar contenido
            if 'fullText' in data:
                if not data['fullText'] or not data['fullText'].strip():
                    self.errors.append("El campo 'fullText' está vacío")
                    self.stats['empty_content'] += 1
                else:
                    self._validate_content_quality(data['fullText'])
            
            # Validar metadatos
            if 'extractedLinks' in data:
                self._validate_extracted_links(data['extractedLinks'])
            
            return len(self.errors) == 0
            
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON inválido: {e}")
            return False
        except FileNotFoundError:
            self.errors.append(f"Archivo no encontrado: {file_path}")
            return False
    
    def _validate_date_format(self, date_str: str, index: int):
        """Valida formato de fecha DD/MM/YYYY"""
        date_pattern = r'^\d{2}/\d{2}/\d{4}$'
        if not re.match(date_pattern, date_str):
            self.errors.append(f"Documento {index}: Formato de fecha inválido '{date_str}'. Esperado: DD/MM/YYYY")
        else:
            # Validar que la fecha sea válida
            try:
                day, month, year = map(int, date_str.split('/'))
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
        file_path = Path('python-cli/boletines') / filename
        if not file_path.exists():
            self.warnings.append(f"Documento {index}: Archivo referenciado no existe '{filename}'")
    
    def _validate_content_quality(self, content: str):
        """Valida calidad del contenido extraído"""
        # Contenido muy corto
        if len(content) < 100:
            self.warnings.append("Contenido muy corto (< 100 caracteres)")
        
        # Contenido con mucho HTML residual
        html_tags = re.findall(r'<[^>]+>', content)
        if len(html_tags) > 10:
            self.warnings.append(f"Contenido contiene {len(html_tags)} tags HTML residuales")
        
        # Contenido con caracteres extraños
        weird_chars = re.findall(r'[^\w\s\.,;:()¿?¡!\-\n\r"\'áéíóúñüÁÉÍÓÚÑÜ]', content)
        if len(weird_chars) > 20:
            self.warnings.append(f"Contenido contiene {len(weird_chars)} caracteres extraños")
        
        # Verificar que contiene palabras clave legales
        legal_keywords = ['ordenanza', 'decreto', 'artículo', 'establece', 'dispone', 'municipal']
        found_keywords = sum(1 for keyword in legal_keywords if keyword.lower() in content.lower())
        if found_keywords == 0:
            self.warnings.append("Contenido no contiene palabras clave legales esperadas")
    
    def _validate_extracted_links(self, links: List[str]):
        """Valida enlaces extraídos"""
        if not isinstance(links, list):
            self.errors.append("extractedLinks debe ser un array")
            return
        
        for i, link in enumerate(links):
            if not isinstance(link, str):
                self.errors.append(f"Link {i}: Debe ser string")
            elif not link.startswith(('http://', 'https://', '/')):
                self.warnings.append(f"Link {i}: Formato de URL sospechoso '{link}'")
    
    def print_report(self):
        """Imprime reporte de validación"""
        print("\n" + "="*60)
        print("REPORTE DE VALIDACIÓN DE DATOS")
        print("="*60)
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Total documentos: {self.stats['total_documents']}")
        print(f"  Documentos válidos: {self.stats['valid_documents']}")
        print(f"  Documentos inválidos: {self.stats['invalid_documents']}")
        print(f"  Campos faltantes: {self.stats['missing_fields']}")
        print(f"  Contenido vacío: {self.stats['empty_content']}")
        
        if self.errors:
            print(f"\n❌ ERRORES ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
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
    parser.add_argument('--type', choices=['index', 'document'], help='Tipo de archivo (auto-detectado si no se especifica)')
    
    args = parser.parse_args()
    
    validator = DataValidator()
    
    # Auto-detectar tipo de archivo
    file_path = Path(args.file)
    if args.type:
        file_type = args.type
    elif file_path.name == 'boletines_index.json':
        file_type = 'index'
    elif file_path.parent.name == 'boletines':
        file_type = 'document'
    else:
        print(f"❌ No se pudo determinar el tipo de archivo: {file_path}")
        sys.exit(1)
    
    # Validar según tipo
    if file_type == 'index':
        success = validator.validate_index_file(str(file_path))
    else:
        success = validator.validate_document_file(str(file_path))
    
    # Actualizar estadísticas
    if success:
        validator.stats['valid_documents'] = 1
    else:
        validator.stats['invalid_documents'] = 1
    
    # Imprimir reporte
    validator.print_report()
    
    # Exit code para CI/CD
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## Validaciones Específicas por Tipo de Archivo

### Validación de Índice Principal
**Archivo:** `python-cli/boletines_index.json`
```python
def validate_index_structure(data: List[Dict]) -> bool:
    """Validaciones específicas para el índice principal"""
    
    # 1. Verificar unicidad de IDs
    ids = [doc.get('id') for doc in data if 'id' in doc]
    if len(ids) != len(set(ids)):
        errors.append("IDs duplicados encontrados en el índice")
    
    # 2. Verificar consistencia de municipios
    municipalities = set(doc.get('municipality') for doc in data if 'municipality' in doc)
    expected_municipalities = load_expected_municipalities()
    unexpected = municipalities - expected_municipalities
    if unexpected:
        warnings.append(f"Municipios inesperados: {unexpected}")
    
    # 3. Verificar distribución temporal
    years = []
    for doc in data:
        if 'date' in doc:
            try:
                year = int(doc['date'].split('/')[-1])
                years.append(year)
            except:
                pass
    
    if years:
        year_range = max(years) - min(years)
        if year_range > 20:
            warnings.append(f"Rango temporal muy amplio: {min(years)}-{max(years)}")
    
    return True
```

### Validación de Documentos Individuales
**Archivos:** `python-cli/boletines/*.json`
```python
def validate_document_content(data: Dict) -> bool:
    """Validaciones específicas para documentos individuales"""
    
    # 1. Validar estructura del contenido
    if 'fullText' in data:
        content = data['fullText']
        
        # Verificar que tiene estructura de documento legal
        legal_patterns = [
            r'ORDENANZA\s+N[°º]?\s*\d+',
            r'DECRETO\s+N[°º]?\s*\d+',
            r'ARTÍCULO\s+\d+',
            r'VISTO\s+Y\s+CONSIDERANDO',
            r'POR\s+TANTO'
        ]
        
        found_patterns = sum(1 for pattern in legal_patterns if re.search(pattern, content, re.IGNORECASE))
        if found_patterns == 0:
            warnings.append("Contenido no parece ser un documento legal válido")
    
    # 2. Validar metadatos vs contenido
    if 'number' in data and 'fullText' in data:
        number = data['number']
        content = data['fullText']
        
        # Verificar que el número aparece en el contenido
        number_patterns = [
            rf'N[°º]?\s*{re.escape(number)}',
            rf'NÚMERO\s+{re.escape(number)}',
            rf'{re.escape(number)}/\d{{4}}'
        ]
        
        found_number = any(re.search(pattern, content, re.IGNORECASE) for pattern in number_patterns)
        if not found_number:
            warnings.append(f"Número '{number}' no encontrado en el contenido")
    
    return True
```

## Configuración Avanzada del Hook

### Validación Incremental
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "python validate_data.py --file={{file.path}} --incremental",
      "condition": "file.path.includes('/boletines/') && file.size < 1000000",
      "description": "Validación rápida para archivos pequeños"
    },
    {
      "type": "shellCommand",
      "command": "python validate_data.py --file={{file.path}} --full --async",
      "condition": "file.path.includes('/boletines/') && file.size >= 1000000",
      "description": "Validación completa asíncrona para archivos grandes"
    }
  ]
}
```

### Validación por Lotes
```json
{
  "actions": [
    {
      "type": "shellCommand",
      "command": "python validate_batch.py --directory=boletines --changed-only",
      "condition": "file.name === 'boletines_index.json'",
      "description": "Validar todos los documentos cuando cambia el índice"
    }
  ]
}
```

### Notificaciones Inteligentes
```json
{
  "actions": [
    {
      "type": "agentMessage",
      "message": "✅ Datos válidos en {{file.name}} - {{stats.total_documents}} documentos procesados",
      "condition": "exitCode === 0 && stats.total_documents > 0"
    },
    {
      "type": "agentMessage", 
      "message": "⚠️ Datos válidos pero con {{stats.warnings}} advertencias en {{file.name}}",
      "condition": "exitCode === 0 && stats.warnings > 0"
    },
    {
      "type": "agentMessage",
      "message": "❌ Errores de validación en {{file.name}}: {{stats.errors}} errores críticos",
      "condition": "exitCode !== 0"
    }
  ]
}
```

## Scripts de Validación Complementarios

### Validador de Integridad Referencial
**Ubicación:** `python-cli/validate_references.py`
```python
#!/usr/bin/env python3
"""
Valida integridad referencial entre índice y archivos de documentos
"""

import json
from pathlib import Path

def validate_references():
    """Valida que todos los archivos referenciados en el índice existan"""
    
    # Cargar índice
    with open('boletines_index.json', 'r') as f:
        index = json.load(f)
    
    errors = []
    warnings = []
    
    for doc in index:
        if 'filename' not in doc:
            errors.append(f"Documento {doc.get('id', 'unknown')} sin filename")
            continue
        
        filename = doc['filename']
        file_path = Path('boletines') / filename
        
        if not file_path.exists():
            errors.append(f"Archivo referenciado no existe: {filename}")
        else:
            # Validar que el contenido del archivo coincide con el índice
            try:
                with open(file_path, 'r') as f:
                    file_data = json.load(f)
                
                # Verificar campos clave
                for field in ['id', 'municipality', 'type', 'number']:
                    if doc.get(field) != file_data.get(field):
                        warnings.append(f"Inconsistencia en {filename}: {field} difiere entre índice y archivo")
                        
            except Exception as e:
                errors.append(f"Error leyendo {filename}: {e}")
    
    # Verificar archivos huérfanos
    boletines_dir = Path('boletines')
    if boletines_dir.exists():
        index_files = set(doc.get('filename') for doc in index if 'filename' in doc)
        actual_files = set(f.name for f in boletines_dir.glob('*.json'))
        
        orphaned = actual_files - index_files
        if orphaned:
            warnings.append(f"Archivos huérfanos (no en índice): {orphaned}")
    
    return len(errors) == 0, errors, warnings

if __name__ == '__main__':
    success, errors, warnings = validate_references()
    
    if errors:
        print("❌ ERRORES DE INTEGRIDAD REFERENCIAL:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print("⚠️ ADVERTENCIAS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if success and not warnings:
        print("✅ Integridad referencial válida")
    
    exit(0 if success else 1)
```

### Validador de Calidad de Datos
**Ubicación:** `python-cli/validate_quality.py`
```python
#!/usr/bin/env python3
"""
Valida calidad de datos extraídos (completitud, consistencia, etc.)
"""

import json
import re
from collections import Counter
from pathlib import Path

def analyze_data_quality():
    """Analiza calidad general de los datos"""
    
    with open('boletines_index.json', 'r') as f:
        index = json.load(f)
    
    stats = {
        'total_documents': len(index),
        'municipalities': Counter(),
        'document_types': Counter(),
        'years': Counter(),
        'content_lengths': [],
        'empty_content': 0,
        'missing_dates': 0,
        'invalid_urls': 0
    }
    
    for doc in index:
        # Estadísticas por municipio
        if 'municipality' in doc:
            stats['municipalities'][doc['municipality']] += 1
        
        # Estadísticas por tipo
        if 'type' in doc:
            stats['document_types'][doc['type']] += 1
        
        # Estadísticas por año
        if 'date' in doc:
            try:
                year = doc['date'].split('/')[-1]
                stats['years'][year] += 1
            except:
                stats['missing_dates'] += 1
        else:
            stats['missing_dates'] += 1
        
        # Validar URL
        if 'url' in doc:
            if not doc['url'].startswith(('http', '/')):
                stats['invalid_urls'] += 1
        
        # Analizar contenido si existe el archivo
        if 'filename' in doc:
            file_path = Path('boletines') / doc['filename']
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        file_data = json.load(f)
                    
                    if 'fullText' in file_data:
                        content_length = len(file_data['fullText'])
                        stats['content_lengths'].append(content_length)
                        
                        if content_length < 100:
                            stats['empty_content'] += 1
                except:
                    pass
    
    return stats

def print_quality_report(stats):
    """Imprime reporte de calidad"""
    print("\n" + "="*60)
    print("REPORTE DE CALIDAD DE DATOS")
    print("="*60)
    
    print(f"\n📊 ESTADÍSTICAS GENERALES:")
    print(f"  Total documentos: {stats['total_documents']}")
    print(f"  Municipios únicos: {len(stats['municipalities'])}")
    print(f"  Tipos de documento: {len(stats['document_types'])}")
    print(f"  Años cubiertos: {len(stats['years'])}")
    
    print(f"\n🏛️ TOP 5 MUNICIPIOS:")
    for municipality, count in stats['municipalities'].most_common(5):
        percentage = (count / stats['total_documents']) * 100
        print(f"  {municipality}: {count} docs ({percentage:.1f}%)")
    
    print(f"\n📋 TIPOS DE DOCUMENTO:")
    for doc_type, count in stats['document_types'].most_common():
        percentage = (count / stats['total_documents']) * 100
        print(f"  {doc_type}: {count} docs ({percentage:.1f}%)")
    
    print(f"\n📅 DISTRIBUCIÓN TEMPORAL:")
    for year, count in sorted(stats['years'].items()):
        percentage = (count / stats['total_documents']) * 100
        print(f"  {year}: {count} docs ({percentage:.1f}%)")
    
    if stats['content_lengths']:
        avg_length = sum(stats['content_lengths']) / len(stats['content_lengths'])
        print(f"\n📄 CALIDAD DE CONTENIDO:")
        print(f"  Longitud promedio: {avg_length:.0f} caracteres")
        print(f"  Contenido vacío: {stats['empty_content']} docs")
        print(f"  Documentos con contenido: {len(stats['content_lengths'])} docs")
    
    print(f"\n⚠️ PROBLEMAS DETECTADOS:")
    print(f"  Fechas faltantes: {stats['missing_dates']}")
    print(f"  URLs inválidas: {stats['invalid_urls']}")
    print(f"  Contenido vacío: {stats['empty_content']}")
    
    # Calcular score de calidad
    total_issues = stats['missing_dates'] + stats['invalid_urls'] + stats['empty_content']
    quality_score = max(0, 100 - (total_issues / stats['total_documents'] * 100))
    
    print(f"\n🎯 SCORE DE CALIDAD: {quality_score:.1f}/100")
    
    if quality_score >= 90:
        print("✅ Excelente calidad de datos")
    elif quality_score >= 75:
        print("✅ Buena calidad de datos")
    elif quality_score >= 60:
        print("⚠️ Calidad de datos aceptable")
    else:
        print("❌ Calidad de datos necesita mejoras")

if __name__ == '__main__':
    stats = analyze_data_quality()
    print_quality_report(stats)
```

## Integración con CI/CD

### GitHub Actions para Validación
```yaml
# .github/workflows/data-validation.yml
name: Data Validation
on:
  push:
    paths:
      - 'python-cli/boletines/**/*.json'
      - 'python-cli/boletines_index.json'

jobs:
  validate-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd python-cli
          pip install -r requirements.txt
      
      - name: Validate data structure
        run: |
          cd python-cli
          python validate_data.py --file=boletines_index.json --type=index
      
      - name: Validate data quality
        run: |
          cd python-cli
          python validate_quality.py
      
      - name: Validate references
        run: |
          cd python-cli
          python validate_references.py
      
      - name: Generate validation report
        if: always()
        run: |
          cd python-cli
          python generate_validation_report.py --output=validation_report.json
      
      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: python-cli/validation_report.json
```

## Métricas y Monitoreo

### Dashboard de Calidad de Datos
```python
# python-cli/generate_dashboard.py
def generate_quality_dashboard():
    """Genera dashboard HTML con métricas de calidad"""
    
    stats = analyze_data_quality()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIBOM Data Quality Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <h1>SIBOM Data Quality Dashboard</h1>
        
        <div class="metrics">
            <div class="metric">
                <h3>Total Documents</h3>
                <span class="value">{stats['total_documents']}</span>
            </div>
            
            <div class="metric">
                <h3>Quality Score</h3>
                <span class="value">{calculate_quality_score(stats):.1f}/100</span>
            </div>
            
            <div class="metric">
                <h3>Municipalities</h3>
                <span class="value">{len(stats['municipalities'])}</span>
            </div>
        </div>
        
        <canvas id="municipalityChart"></canvas>
        <canvas id="yearChart"></canvas>
        
        <script>
            // Gráficos con Chart.js
            // ... código de gráficos
        </script>
    </body>
    </html>
    """
    
    with open('data_quality_dashboard.html', 'w') as f:
        f.write(html)
```

## Checklist de Validación

- [ ] ✅ Hook configurado para archivos JSON
- [ ] ✅ Validador principal implementado
- [ ] ✅ Validaciones específicas por tipo de archivo
- [ ] ✅ Validación de integridad referencial
- [ ] ✅ Análisis de calidad de datos
- [ ] ⏳ Integración con CI/CD
- [ ] ⏳ Dashboard de métricas
- [ ] ⏳ Alertas automáticas para problemas críticos
- [ ] ⏳ Validación de performance (tiempo de carga)
- [ ] ⏳ Validación de consistencia temporal
- [ ] ⏳ Backup y recovery de datos válidos
- [ ] ⏳ Documentación para el equipo