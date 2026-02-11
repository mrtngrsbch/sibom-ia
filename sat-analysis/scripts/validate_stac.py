#!/usr/bin/env python3
"""
Script de validación de Planetary Computer STAC

Prueba la conexión con Microsoft Planetary Computer y la búsqueda
de imágenes Sentinel-2 L2A sin dependencias del proyecto.

Requiere:
    pip install pystac-client planetary-computer
"""
import pystac_client
import planetary_computer
from datetime import datetime, timedelta

# Coordenadas de prueba (región de Buenos Aires)
# BBOX: [min_lon, min_lat, max_lon, max_lat]
bbox = [-59.5, -35.2, -59.4, -35.1]

def main():
    print("🔍 Conectando a Planetary Computer STAC...")

    try:
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1"
        )
        print("   ✅ Conexión establecida")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return

    # Buscar imágenes de los últimos 60 días
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    print(f"\n📅 Buscando imágenes {start_date.date()} a {end_date.date()}")
    print(f"📍 BBOX: {bbox}")

    try:
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}",
            query={"eo:cloud_cover": {"lt": 20}}
        )

        items = list(search.items())
        print(f"\n✅ Encontradas: {len(items)} imágenes")

        if not items:
            print("⚠️ No se encontraron imágenes. Intenta ampliar el rango de fechas o el área.")
            return

        # Mostrar info de la primera imagen
        item = items[0]
        print(f"\n🛰️ Primera imagen:")
        print(f"   ID: {item.id}")
        print(f"   Fecha: {item.properties['datetime']}")
        print(f"   Nubes: {item.properties.get('eo:cloud_cover', 'N/A')}%")

        # Mostrar bandas disponibles
        bands = [k for k in item.assets.keys() if k.startswith('B') or k in ['visual', 'thumbnail']]
        print(f"   Bandas: {', '.join(bands[:10])}")

        # Probar URL signing (necesario para descargar)
        try:
            signed = planetary_computer.sign(item)
            print(f"   ✅ URL signing funciona (SAS token aplicado)")

            # Mostrar URL de una banda como ejemplo
            b02_asset = signed.assets["B02"]
            print(f"   Ejemplo URL B02: {b02_asset.href[:80]}...")

        except Exception as e:
            print(f"   ⚠️ URL signing falló: {e}")

        # Resumen de todas las imágenes encontradas
        print(f"\n📊 Resumen de imágenes encontradas:")
        for i, item in enumerate(items[:5], 1):
            date = item.properties['datetime'][:10]
            clouds = item.properties.get('eo:cloud_cover', 'N/A')
            print(f"   {i}. {date} - Nubes: {clouds}%")

        if len(items) > 5:
            print(f"   ... y {len(items) - 5} más")

    except Exception as e:
        print(f"❌ Error durante la búsqueda: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
