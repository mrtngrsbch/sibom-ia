#!/usr/bin/env python3
"""
Script para calibrar umbrales de clasificación.

Prueba múltiples combinaciones de umbrales y reporta
la que mejor se ajusta a ground truth.

Uso:
    python calibrate_thresholds.py reference_parcels.json
    python calibrate_thresholds.py --partida 002004606 --water 5.2 --wetland 95.0 --veg 0.5 --other 232.1
"""
import sys
import argparse
from pathlib import Path
from itertools import product
import numpy as np
from typing import Dict, Any

# Agregar el módulo sat_analysis al path
script_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(script_dir))

from sat_analysis.services import PixelClassifier, StacService
from sat_analysis.services.stac import get_pixel_area_m2


def calculate_error(
    predicted: Dict[int, float],
    reference: Dict[str, float],
) -> float:
    """
    Calcula el error absoluto medio entre áreas predichas y de referencia.

    Args:
        predicted: Dict con {clase: área en ha}
        reference: Dict con {"water": ha, "wetland": ha, "vegetation": ha, "other": ha}

    Returns:
        Error absoluto medio en hectáreas
    """
    # Mapeo de clases predichas a nombres de referencia
    class_map = {
        1: "water",
        2: "wetland",
        3: "vegetation",
        0: "other",
    }

    errors = []
    for class_id, class_name in class_map.items():
        pred = predicted.get(class_id, 0)
        ref = reference.get(class_name, 0)
        errors.append(abs(pred - ref))

    return sum(errors) / len(errors)


def test_thresholds(
    thresholds: Dict[str, float],
    partida: str,
    stac_service: StacService,
    max_images: int = 1,
) -> Dict[str, Any]:
    """
    Prueba una combinación de umbrales con una partida específica.

    Args:
        thresholds: Dict con umbrales a probar
        partida: Partida catastral a analizar
        stac_service: Instancia de StacService
        max_images: Máximo de imágenes a procesar

    Returns:
        Dict con resultado del análisis
    """
    # Crear clasificador con umbrales personalizados
    classifier = PixelClassifier(
        water_ndwi_threshold=thresholds.get("water_ndwi", 0.15),
        water_mndwi_threshold=thresholds.get("water_mndwi", 0.25),
        wetland_ndvi_threshold=thresholds.get("wetland_ndvi", 0.35),
        wetland_ndmi_threshold=thresholds.get("wetland_ndmi", 0.10),
        wetland_ndwi_threshold=thresholds.get("wetland_ndwi", -0.6),
        vegetation_ndvi_threshold=thresholds.get("vegetation_ndvi", 0.5),
        vegetation_ndmi_threshold=thresholds.get("vegetation_ndmi", 0.2),
    )

    # Buscar imágenes (último año)
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    date_range = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

    try:
        items = stac_service.search_sentinel(
            bbox=[-60.5, -35.5, -60.0, -35.0],  # Área aproximada BA
            date_range=date_range,
            max_clouds=20,
            limit=max_images,
        )

        if not items:
            return {"error": "No se encontraron imágenes"}

        # Procesar primera imagen
        item = items[0]
        bands = stac_service.download_bands(item, bbox=None, geometry=None)
        pixel_area = get_pixel_area_m2(bands.transform, bands.crs)

        # Calcular índices y clasificar
        indices = classifier.calculate_indices(
            b02=bands.b02,
            b03=bands.b03,
            b04=bands.b04,
            b08=bands.b08,
            b11=bands.b11,
            b12=bands.b12,
        )
        result = classifier.classify_with_areas(indices, pixel_area_m2=pixel_area)

        return {
            "success": True,
            "areas": result.areas_hectares,
            "pixels": result.pixel_count,
        }

    except Exception as e:
        return {"error": str(e)}


def grid_search(
    reference_parcels: Dict[str, Dict[str, float]],
    stac_service: StacService,
    step: float = 0.05,
) -> Dict[str, Any]:
    """
    Realiza búsqueda de grid sobre umbrales para encontrar mejor combinación.

    Args:
        reference_parcels: Dict con {partida: {water, wetland, vegetation, other}}
        stac_service: Instancia de StacService
        step: Paso para iterar umbrales

    Returns:
        Dict con mejores umbrales y errores
    """
    # Rangos de búsqueda
    water_ndwi_range = np.arange(0.05, 0.30, step)
    wetland_ndvi_range = np.arange(0.25, 0.50, step)

    best_thresholds = None
    best_error = float('inf')
    results = []

    total = len(water_ndwi_range) * len(wetland_ndvi_range) * len(reference_parcels)
    current = 0

    for water_ndwi, wetland_ndvi in product(water_ndwi_range, wetland_ndvi_range):
        thresholds = {
            "water_ndwi": round(water_ndwi, 2),
            "wetland_ndvi": round(wetland_ndvi, 2),
        }

        total_error = 0
        valid = True

        for partida, reference in reference_parcels.items():
            current += 1
            progress = (current / total) * 100
            print(f"\rPROCESANDO: {progress:.1f}% ({current}/{total})", end="")

            result = test_thresholds(thresholds, partida, stac_service)

            if "error" in result:
                valid = False
                break

            error = calculate_error(result["areas"], reference)
            total_error += error

        if valid:
            avg_error = total_error / len(reference_parcels)
            results.append({
                "thresholds": thresholds,
                "error": avg_error,
            })

            if avg_error < best_error:
                best_error = avg_error
                best_thresholds = thresholds

    print()  # Nueva línea después de progress bar

    # Ordenar resultados por error
    results.sort(key=lambda x: x["error"])

    return {
        "best": best_thresholds,
        "best_error": best_error,
        "top5": results[:5],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Calibrar umbrales de clasificación para detección de humedales"
    )
    parser.add_argument(
        "reference",
        help="Archivo JSON con partidas de referencia o modo interactivo",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.05,
        help="Paso para iterar umbrales (default: 0.05)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Modo rápido: probar solo algunos umbrales",
    )
    parser.add_argument(
        "--partida",
        help="Partida individual para probar (requiere --water, --wetland, etc)",
    )
    parser.add_argument("--water", type=float, help="Área de agua de referencia (ha)")
    parser.add_argument("--wetland", type=float, help="Área de humedal de referencia (ha)")
    parser.add_argument("--vegetation", type=float, help="Área de vegetación de referencia (ha)")
    parser.add_argument("--other", type=float, help="Área de otros de referencia (ha)")

    args = parser.parse_args()

    # Modo de prueba individual
    if args.partida and args.water is not None:
        reference = {
            args.partida: {
                "water": args.water,
                "wetland": args.wetland or 0,
                "vegetation": args.vegetation or 0,
                "other": args.other or 0,
            }
        }

        stac = StacService()

        # Probar umbrales actuales
        current_thresholds = {
            "water_ndwi": 0.15,
            "wetland_ndvi": 0.35,
        }

        print(f"# Prueba de umbrales para partida {args.partida}")
        print(f"# Referencia: Agua={args.water}ha, Humedal={args.wetland or 0}ha")
        print()

        result = test_thresholds(current_thresholds, args.partida, stac)

        if "error" in result:
            print(f"ERROR: {result['error']}")
            return 1

        print(f"# Umbrales actuales: water_ndwi={current_thresholds['water_ndwi']}, wetland_ndvi={current_thresholds['wetland_ndvi']}")
        print(f"# Resultado:")
        for class_id, area in result["areas"].items():
            class_names = {0: "Otros", 1: "Agua", 2: "Humedal", 3: "Vegetación"}
            print(f"   {class_names[class_id]}: {area:.1f} ha")

        error = calculate_error(result["areas"], reference[args.partida])
        print(f"# Error: {error:.1f} ha")

        return 0

    # Modo archivo JSON
    try:
        import json
        with open(args.reference) as f:
            reference_parcels = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Archivo no encontrado: {args.reference}")
        print("\nModo de uso:")
        print("  1. Calibrar con archivo JSON de referencia:")
        print("     python calibrate_thresholds.py reference_parcels.json")
        print("\n  2. Probar partida individual:")
        print("     python calibrate_thresholds.py --partida 002004606 --water 5.2 --wetland 95.0")
        return 1

    print(f"# Calibrando umbrales con {len(reference_parcels)} partidas de referencia")
    print(f"# Paso de búsqueda: {args.step}")
    print()

    stac = StacService()

    results = grid_search(reference_parcels, stac, step=args.step)

    print("# RESULTADOS")
    print("# ==========")
    print()
    print(f"# Mejores umbrales:")
    for k, v in results["best"].items():
        print(f"   {k}: {v}")
    print(f"# Error promedio: {results['best_error']:.1f} ha")
    print()
    print("# Top 5 combinaciones:")
    for i, r in enumerate(results["top5"], 1):
        print(f"   {i}. {r['thresholds']} - Error: {r['error']:.1f} ha")

    return 0


if __name__ == "__main__":
    sys.exit(main())
