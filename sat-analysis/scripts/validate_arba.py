#!/usr/bin/env python3
"""
Script de validación de WFS ARBA

Prueba la conexión con el servicio WFS de ARBA para obtener
la geometría de una parcela por su partida catastral.
"""
import requests
import json

# Partida catastral de prueba (puedes cambiarla)
# Formato: 8 dígitos (ej: 002004606)
PARTIDA_PRUEBA = "002004606"

def main():
    print(f"🔍 Consultando partida {PARTIDA_PRUEBA}...")

    url = "https://geo.arba.gov.ar/geoserver/idera/wfs"

    # Parámetros del request WFS
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeName': 'idera:Parcela',
        'outputFormat': 'application/json',
        'CQL_FILTER': f"pda='{PARTIDA_PRUEBA}'"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"📡 Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"❌ Respuesta no es JSON válido")
                print(f"   Respuesta (primeros 500 chars): {response.text[:500]}")
                return

            if data.get('features'):
                feature = data['features'][0]
                props = feature.get('properties', {})
                print(f"\n✅ Partida encontrada!")
                print(f"   PDA: {props.get('pda')}")
                print(f"   CCA: {props.get('cca')}")
                area_m2 = float(props.get('ara1', 0))
                print(f"   Área (ARA1): {area_m2:,.2f} m² = {area_m2/10000:.2f} ha")
                print(f"   Tipo: {props.get('tpa')}")

                # Extraer CRS
                crs = data.get('crs', {})
                crs_name = ""
                if isinstance(crs, dict):
                    crs_props = crs.get('properties', {})
                    crs_name = crs_props.get('name', '')
                print(f"   CRS: {crs_name}")

                # Extraer bbox (coordenadas UTM de ARBA)
                utm_bbox = data.get('bbox', [])
                if utm_bbox:
                    print(f"   BBOX (UTM): {utm_bbox}")

                # Convertir bbox UTM a lat/long para Planetary Computer
                if utm_bbox and "5347" in crs_name:
                    from pyproj import Transformer
                    transformer = Transformer.from_crs("EPSG:5347", "EPSG:4326", always_xy=True)
                    # bbox UTM: [min_x, min_y, max_x, max_y]
                    min_lon, min_lat = transformer.transform(utm_bbox[0], utm_bbox[1])
                    max_lon, max_lat = transformer.transform(utm_bbox[2], utm_bbox[3])
                    latlon_bbox = [min_lon, min_lat, max_lon, max_lat]
                    print(f"   BBOX (WGS84): [{latlon_bbox[0]:.6f}, {latlon_bbox[1]:.6f}, {latlon_bbox[2]:.6f}, {latlon_bbox[3]:.6f}]")
                    print(f"   Centro: [{(min_lon+max_lon)/2:.6f}, {(min_lat+max_lat)/2:.6f}]")

                # Guardar GeoJSON completo si se desea
                output_file = f"parcela_{PARTIDA_PRUEBA}.geojson"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n💾 GeoJSON guardado en: {output_file}")

            else:
                print("\n⚠️ Partida no encontrada (response vacío)")
                print("   Verifica que la partida sea correcta")

        elif response.status_code == 404:
            print("\n❌ Recurso no encontrado (404)")
            print("   El endpoint WFS puede haber cambiado")

        else:
            print(f"\n❌ Error HTTP {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")

    except requests.Timeout:
        print("❌ Timeout: El servidor tardó demasiado en responder")

    except Exception as e:
        print(f"❌ Excepción: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
