#!/usr/bin/env python3
"""
Script de diagnóstico para ver los valores de índices espectrales.

Guarda imágenes PNG de los índices calculados y muestra estadísticas.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from sat_analysis.services import ArbaService, StacService, PixelClassifier

def main():
    partida = "002004606"

    print(f"🔍 Diagnosticando partida {partida}...")

    # 1. Obtener parcela
    arba = ArbaService()
    parcel = arba.get_parcel_geometry(partida)
    if not parcel:
        print("❌ Partida no encontrada")
        return

    print(f"✅ Parcela: {parcel.area_approx_hectares:.1f} ha")
    print(f"   BBOX: {parcel.bbox}")

    # 2. Buscar una imagen reciente
    stac = StacService()
    items = stac.search_sentinel(
        bbox=parcel.bbox,
        date_range="2024-01-01/2026-01-25",
        max_clouds=10,
        limit=1
    )

    if not items:
        print("❌ No se encontraron imágenes")
        return

    item = items[0]
    print(f"✅ Imagen: {item.datetime[:10]}")

    # 3. Descargar bandas
    print("📥 Descargando bandas...")
    bands = stac.download_bands(item, bbox=parcel.bbox)

    # 4. Calcular índices
    print("📊 Calculando índices...")
    classifier = PixelClassifier()
    indices = classifier.calculate_indices(
        b02=bands.b02,
        b03=bands.b03,
        b04=bands.b04,
        b08=bands.b08,
        b11=bands.b11,
    )

    # 5. Estadísticas
    print("\n" + "="*60)
    print("📈 ESTADÍSTICAS DE ÍNDECES")
    print("="*60)

    for name, data in [("NDWI", indices.ndwi), ("MNDWI", indices.mndwi),
                        ("NDVI", indices.ndvi), ("NDMI", indices.ndmi)]:
        print(f"\n{name}:")
        print(f"  Mín: {data.min():.3f}")
        print(f"  Máx: {data.max():.3f}")
        print(f"  Prom: {data.mean():.3f}")
        print(f"  Mediana: {np.median(data):.3f}")

        # Percentiles
        for p in [5, 25, 50, 75, 95, 99]:
            val = np.percentile(data, p)
            print(f"  P{p}: {val:.3f}", end="")
        print()

    # 6. Clasificación
    result = classifier.classify_with_areas(indices, pixel_area_m2=100.0)

    print("\n" + "="*60)
    print("🏷️  CLASIFICACIÓN (sin corrección)")
    print("="*60)
    for label, name in [(0, "Otros"), (1, "Agua"), (2, "Humedal"), (3, "Vegetación")]:
        count = result.pixel_count.get(label, 0)
        area = result.areas_hectares.get(label, 0)
        pct = (count / result.classification.size * 100) if result.classification.size > 0 else 0
        print(f"{name}: {count:,} píxeles = {area:.1f} ha ({pct:.1f}%)")

    # 7. Crear máscara de parcela para visualización
    stac_service = StacService()
    parcel_mask = stac_service.create_parcel_mask(
        shape=bands.b02.shape,
        geometry=parcel.geometry if parcel else None,
        bbox=parcel.bbox if parcel else None,
        image_crs=bands.crs,
        transform=bands.transform
    )

    # 8. Guardar imágenes de índices
    output_dir = "diagnostic_output"
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n💾 Guardando imágenes en {output_dir}/")

    # Extraer fecha de la imagen
    image_date = item.datetime[:10]  # YYYY-MM-DD
    image_date_formatted = image_date.replace("-", "")  # YYYYMMDD

    # Configurar colormap
    cmap_water = plt.cm.RdYlBu_r  # Azul para valores bajos (agua)
    cmap_veg = plt.cm.RdYlGn_r  # Verde para valores altos (vegetación)

    # Guardar cada índice
    indices_to_save = [
        ("NDWI", indices.ndwi, cmap_water, -0.5, 0.5),
        ("MNDWI", indices.mndwi, cmap_water, -0.5, 0.5),
        ("NDVI", indices.ndvi, cmap_veg, -0.2, 0.9),
        ("NDMI", indices.ndmi, cmap_veg, -0.2, 0.6),
        ("Clasificación", result.classification, plt.cm.tab10, None, None),
        ("Máscara", parcel_mask.astype(np.uint8), plt.cm.gray_r, 0, 1),
    ]

    for name, data, cmap, vmin, vmax in indices_to_save:
        fig, ax = plt.subplots(figsize=(10, 8))

        if vmin is not None:
            im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
        else:
            im = ax.imshow(data, cmap=cmap)

        plt.colorbar(im, ax=ax, label=name)
        # Título con formato: ÍNDICE - Partida | Servicio | Fecha
        ax.set_title(f"{name} - {partida} | STAC Planetary Computer | {image_date}", fontsize=10)
        ax.axis('off')

        # Nombre de archivo con fecha
        filename = f"{output_dir}/{name.lower()}_{partida}_{image_date_formatted}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  ✓ {filename}")

    # 9. Análisis de umbrales
    print("\n" + "="*60)
    print("🔍 ANÁLISIS DE UMBRALES")
    print("="*60)

    # Contar píxeles sobre cada umbral
    water_ndwi = (indices.ndwi > 0.2).sum()
    water_mndwi = (indices.mndwi > 0.3).sum()
    water_any = ((indices.ndwi > 0.2) | (indices.mndwi > 0.3)).sum()

    wetland_ndvi = (indices.ndvi > 0.4).sum()
    wetland_ndmi = (indices.ndmi > 0.15).sum()
    wetland_ndwi = (indices.ndwi > -0.1).sum()

    print(f"\nAgua (NDWI > 0.2): {water_ndwi:,} píxeles ({water_ndwi/result.classification.size*100:.2f}%)")
    print(f"Agua (MNDWI > 0.3): {water_mndwi:,} píxeles ({water_mndwi/result.classification.size*100:.2f}%)")
    print(f"Agua (cualquiera): {water_any:,} píxeles ({water_any/result.classification.size*100:.2f}%)")

    print(f"\nHumedal - NDVI > 0.4: {wetland_ndvi:,} píxeles ({wetland_ndvi/result.classification.size*100:.2f}%)")
    print(f"Humedal - NDMI > 0.15: {wetland_ndmi:,} píxeles ({wetland_ndmi/result.classification.size*100:.2f}%)")
    print(f"Humedal - NDWI > -0.1: {wetland_ndwi:,} píxeles ({wetland_ndwi/result.classification.size*100:.2f}%)")

    # Intersección para humedal
    wetland_all = (indices.ndvi > 0.4) & (indices.ndmi > 0.15) & (indices.ndwi > -0.1)
    wetland_not_water = wetland_all & ~((indices.ndwi > 0.2) | (indices.mndwi > 0.3))
    print(f"Humedal (todos, no agua): {wetland_not_water.sum():,} píxeles")

    # Vegetación
    veg_ndvi = (indices.ndvi > 0.5).sum()
    veg_ndmi_low = (indices.ndmi < 0.2).sum()
    veg_all = (indices.ndvi > 0.5) & (indices.ndmi < 0.2)
    veg_not_water = veg_all & ~((indices.ndwi > 0.2) | (indices.mndwi > 0.3))
    print(f"\nVegetación (NDVI > 0.5, NDMI < 0.2, no agua): {veg_not_water.sum():,} píxeles ({veg_not_water.sum()/result.classification.size*100:.2f}%)")

    # 10. Estadísticas de la máscara
    print("\n" + "="*60)
    print("🎭 MÁSCARA DE PARCELA")
    print("="*60)

    pixels_inside = parcel_mask.sum()
    total_pixels = parcel_mask.size
    coverage = pixels_inside / total_pixels * 100

    print(f"\nPíxeles dentro de parcela: {pixels_inside:,}/{total_pixels:,} ({coverage:.1f}%)")
    print(f"Píxeles fuera de parcela: {total_pixels - pixels_inside:,} ({100 - coverage:.1f}%)")

    # Calcular áreas con máscara aplicada
    result_masked = classifier.apply_mask(
        classification=result.classification,
        areas_hectares=result.areas_hectares,
        mask=parcel_mask,
        pixel_area_m2=100.0
    )

    print(f"\nÁreas con máscara aplicada:")
    for label, name in [(0, "Otros"), (1, "Agua"), (2, "Humedal"), (3, "Vegetación")]:
        area = result_masked.areas_hectares.get(label, 0)
        print(f"  {name}: {area:.1f} ha")

    print(f"\n📁 Todas las imágenes guardadas en: {output_dir}/")
    print("   Abre los archivos PNG para ver visualmente los índices.")
    print("   'mascara_*.png' muestra la parcela en blanco sobre el bbox en gris.")

if __name__ == "__main__":
    main()
