#!/usr/bin/env python3
"""
Script para regenerar normativas_index_minimal.json desde archivos V2
Extrae las URLs individuales de cada norma desde los archivos JSON V2
"""

import json
from pathlib import Path
from datetime import datetime
from normativas_extractor import Normativa, save_minimal_index

def main():
    boletines_dir = Path("boletines")

    if not boletines_dir.exists():
        print(f"❌ Error: Directorio {boletines_dir} no existe")
        return

    normativas = []
    archivos_procesados = 0
    archivos_v2 = 0

    print("🔍 Buscando archivos V2 en boletines/...")

    for archivo in sorted(boletines_dir.glob("*.json")):
        # Saltar archivos especiales
        if archivo.name.startswith('.progress_') or archivo.name.startswith('Test_'):
            continue

        archivos_procesados += 1

        try:
            with archivo.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # Verificar si es formato V2 (tiene array 'normas')
            if 'normas' not in data:
                print(f"  ⏭️  {archivo.name} - Formato V1 (sin normas[]), saltando...")
                continue

            archivos_v2 += 1
            municipio = data.get('municipio', '')
            boletin_url = data.get('boletin_url', '')

            # Extraer todas las normas del archivo
            for norma in data.get('normas', []):
                # Extraer año del número o de la fecha
                year = ''
                numero = norma.get('numero', '')
                if '/' in numero:
                    year = numero.split('/')[-1]
                    # Normalizar año de 2 dígitos (25 -> 2025)
                    if len(year) == 2:
                        year = f"20{year}"
                elif norma.get('fecha'):
                    parts = norma['fecha'].split('/')
                    if len(parts) == 3:
                        year = parts[2]

                # Crear objeto Normativa
                normativa = Normativa(
                    id=norma['id'],
                    municipality=municipio,
                    type=norma['tipo'],
                    number=numero,
                    year=year,
                    date=norma.get('fecha', ''),
                    title=norma.get('titulo', ''),
                    content=norma.get('contenido', ''),
                    source_bulletin=archivo.stem,
                    source_bulletin_url=boletin_url,
                    norma_url=norma['url'],  # ✨ URL individual de V2
                    doc_index=0,
                    status='vigente',
                    extracted_at=datetime.now().isoformat()
                )
                normativas.append(normativa)

            print(f"  ✅ {archivo.name} - {len(data['normas'])} normas extraídas")

        except Exception as e:
            print(f"  ❌ {archivo.name} - Error: {e}")

    print(f"\n📊 Resumen:")
    print(f"  Archivos procesados: {archivos_procesados}")
    print(f"  Archivos V2: {archivos_v2}")
    print(f"  Total normativas: {len(normativas)}")

    if normativas:
        # Guardar índice minimal
        output_path = Path("normativas_index_minimal.json")
        save_minimal_index(normativas, output_path)

        print(f"\n🎉 ¡Índice regenerado exitosamente!")
        print(f"\nVerificación de URLs:")
        print(f"  Primera norma: {normativas[0].norma_url}")
        print(f"  Última norma: {normativas[-1].norma_url}")
    else:
        print(f"\n⚠️  No se encontraron normativas para indexar")

if __name__ == '__main__':
    main()
