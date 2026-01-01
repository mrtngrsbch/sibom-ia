import os
import json
import re
from pathlib import Path

def extract_municipality(filename):
    # Formato: Carlos_Tejedor_105.json -> Carlos Tejedor
    parts = filename.replace('.json', '').split('_')
    if len(parts) >= 2:
        # Intentar reconstruir el nombre con espacios
        name = ' '.join(parts[:-1])
        # Añadir espacios antes de mayúsculas si están pegadas (ej: CarlosTejedor -> Carlos Tejedor)
        # Pero en este caso parece que ya vienen con guiones bajos
        return name.replace('_', ' ').strip()
    return 'Desconocido'

def detect_type(content):
    lower = content.lower()
    if 'ordenanza' in lower: return 'ordenanza'
    if 'decreto' in lower: return 'decreto'
    return 'boletin'

def detect_status(content):
    lower = content.lower()
    if 'derogada' in lower or 'derógase' in lower: return 'derogada'
    if 'modificada' in lower or 'modifícase' in lower: return 'modificada'
    return 'vigente'

def indexar():
    boletines_path = Path('boletines')
    if not boletines_path.exists():
        print(f"Error: No se encuentra la carpeta {boletines_path}")
        return

    index = []
    files = list(boletines_path.glob('*.json'))
    
    print(f"Indexando {len(files)} archivos...")

    for file_path in files:
        if file_path.name == 'boletines_index.json':
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer metadatos básicos
            # El contenido completo NO se guarda en el índice
            full_text = data.get('fullText', '')
            
            entry = {
                'id': file_path.name.replace('.json', ''),
                'municipality': extract_municipality(file_path.name),
                'type': data.get('type') or detect_type(full_text),
                'number': data.get('number', '0'),
                'title': data.get('description') or data.get('title', 'Sin título'),
                'date': data.get('date', ''),
                'url': data.get('link') or data.get('url', ''),
                'status': detect_status(full_text),
                'filename': file_path.name
            }
            index.append(entry)
        except Exception as e:
            print(f"Error procesando {file_path.name}: {e}")

    # Guardar el índice
    output_path = Path('boletines_index.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"Índice creado con {len(index)} entradas en {output_path}")

if __name__ == '__main__':
    indexar()
