#!/usr/bin/env python3
"""
comprimir_boletines.py

Script para comprimir archivos JSON de boletines con gzip.
Esto reduce el tamaño de ~533 MB a ~100 MB (80% ahorro).

Uso:
    python comprimir_boletines.py [--keep-original]

Opciones:
    --keep-original    Mantener archivos originales (crea .json.gz)
                      Sin esta opción, reemplaza .json por .json.gz

Autor: Kilo Code
Fecha: 2026-01-01
"""

import gzip
import json
import os
import sys
from pathlib import Path
from tqdm import tqdm

# Configuración
BOLETINES_DIR = Path(__file__).parent / "boletines"
INDEX_FILE = Path(__file__).parent / "boletines_index.json"


def comprimir_archivo(archivo: Path, mantener_original: bool = False):
    """Comprime un archivo JSON con gzip"""
    try:
        # Leer contenido
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()

        # Crear archivo comprimido
        archivo_gz = archivo.with_suffix('.json.gz')
        with gzip.open(archivo_gz, 'wt', encoding='utf-8', compresslevel=9) as f:
            f.write(contenido)

        # Eliminar original si se especifica
        if not mantener_original:
            archivo.unlink()
            print(f"✓ Comprimido: {archivo.name} → {archivo_gz.name} (eliminado original)")
        else:
            print(f"✓ Comprimido: {archivo.name} → {archivo_gz.name} (conservado original)")

        return True
    except Exception as e:
        print(f"✗ Error comprimiendo {archivo.name}: {e}")
        return False


def comprimir_indice(mantener_original: bool = False):
    """Comprime el archivo de índice"""
    if not INDEX_FILE.exists():
        print(f"⚠️  Índice no encontrado: {INDEX_FILE}")
        return False

    try:
        # Leer y minificar JSON
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Escribir minificado y comprimido
        archivo_gz = INDEX_FILE.with_suffix('.json.gz')
        with gzip.open(archivo_gz, 'wt', encoding='utf-8', compresslevel=9) as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

        if not mantener_original:
            INDEX_FILE.unlink()
            print(f"✓ Índice comprimido: {INDEX_FILE.name} → {archivo_gz.name} (eliminado original)")
        else:
            print(f"✓ Índice comprimido: {INDEX_FILE.name} → {archivo_gz.name} (conservado original)")

        return True
    except Exception as e:
        print(f"✗ Error comprimiendo índice: {e}")
        return False


def obtener_tamano_directorio(directorio: Path) -> int:
    """Obtiene el tamaño total de un directorio en bytes"""
    total = 0
    for archivo in directorio.glob('**/*'):
        if archivo.is_file():
            total += archivo.stat().st_size
    return total


def formato_tamano(bytes: int) -> str:
    """Formatea bytes en formato legible"""
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unidad}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def main():
    # Verificar argumentos
    mantener_original = '--keep-original' in sys.argv

    print("=" * 60)
    print("🗜️  COMPRESOR DE BOLETINES - Gzip")
    print("=" * 60)
    print()

    if not BOLETINES_DIR.exists():
        print(f"❌ Error: No se encontró el directorio {BOLETINES_DIR}")
        sys.exit(1)

    # Obtener tamaño inicial
    print("📊 Calculando tamaño inicial...")
    tamano_inicial = obtener_tamano_directorio(BOLETINES_DIR.parent)
    print(f"   Tamaño actual: {formato_tamano(tamano_inicial)}")
    print()

    # Obtener lista de archivos JSON
    archivos_json = list(BOLETINES_DIR.glob('*.json'))
    total_archivos = len(archivos_json)

    if total_archivos == 0:
        print("⚠️  No se encontraron archivos .json en el directorio")
        print(f"   Directorio: {BOLETINES_DIR}")
        sys.exit(0)

    print(f"📁 Encontrados {total_archivos} archivos JSON")
    print(f"   Modo: {'Conservar originales' if mantener_original else 'Reemplazar originales'}")
    print()

    # Confirmar acción si se van a eliminar originales
    if not mantener_original:
        print("⚠️  ADVERTENCIA: Se eliminarán los archivos .json originales")
        respuesta = input("   ¿Continuar? (s/N): ").strip().lower()
        if respuesta != 's':
            print("❌ Operación cancelada")
            sys.exit(0)
        print()

    # Comprimir archivos
    print("🗜️  Comprimiendo archivos...")
    exitosos = 0
    fallidos = 0

    for archivo in tqdm(archivos_json, desc="Progreso"):
        if comprimir_archivo(archivo, mantener_original):
            exitosos += 1
        else:
            fallidos += 1

    print()
    print("─" * 60)

    # Comprimir índice
    print("🗜️  Comprimiendo índice...")
    if comprimir_indice(mantener_original):
        print("✓ Índice comprimido exitosamente")
    else:
        print("✗ Error comprimiendo índice")

    print()
    print("─" * 60)

    # Obtener tamaño final
    print("📊 Calculando tamaño final...")
    tamano_final = obtener_tamano_directorio(BOLETINES_DIR.parent)
    ahorro = tamano_inicial - tamano_final
    porcentaje_ahorro = (ahorro / tamano_inicial) * 100 if tamano_inicial > 0 else 0

    print()
    print("=" * 60)
    print("📈 RESUMEN")
    print("=" * 60)
    print(f"✅ Archivos comprimidos: {exitosos}")
    print(f"❌ Fallos: {fallidos}")
    print()
    print(f"💾 Tamaño inicial:  {formato_tamano(tamano_inicial)}")
    print(f"💾 Tamaño final:    {formato_tamano(tamano_final)}")
    print(f"📉 Ahorro:          {formato_tamano(ahorro)} ({porcentaje_ahorro:.1f}%)")
    print()

    if not mantener_original:
        print("🚀 Archivos listos para subir a GitHub!")
        print("   Siguiente paso:")
        print("   1. Crear repositorio público en GitHub")
        print("   2. git add boletines/*.gz boletines_index.json.gz")
        print("   3. git commit -m 'Add compressed bulletins data'")
        print("   4. git push")
    else:
        print("📦 Archivos .gz creados (originales conservados)")
        print("   Puedes borrar los .json manualmente si lo deseas")

    print("=" * 60)


if __name__ == "__main__":
    main()
