  # Códigos de Partidos ARBA - Provincia de Buenos Aires

## 📋 Formato del Número de Partida

### Estructura General

```
Ejemplo completo: 002-004606-0
                  │   │      │
                  │   │      └─ Dígito verificador (1 dígito)
                  │   └──────── Partida individual (6 dígitos)
                  └──────────── Código del partido/municipio (3 dígitos)
```

### Componentes

| Componente | Longitud | Descripción | Ejemplo |
|------------|----------|-------------|---------|
| **Código de Partido** | 3 dígitos | Identifica el municipio/partido | `002` = Alberti |
| **Partida Individual** | 6 dígitos | Número único del inmueble en el partido | `004606` |
| **Dígito Verificador** | 1 dígito | Control de validación (calculado por ARBA) | `0` |

### Formatos Aceptados

La partida inmobiliaria puede escribirse de varias formas:

```
✅ 002004606      (9 dígitos sin separadores)
✅ 002-004606-0   (con guiones y dígito verificador)
✅ 0020046060     (10 dígitos continuos)
✅ 002-004606     (sin dígito verificador)
```

---

## 📊 Información de Códigos

### Total de Entidades

| Categoría | Cantidad | Rango de Códigos |
|-----------|----------|------------------|
| Partidos/Municipios | 135 | 001-137 (con gaps) |
| Islas del Delta | 8 | 309-399 |
| **TOTAL** | **143** | - |

### Gaps en la Numeración

Los siguientes códigos **NO existen**:
- `048` (sin asignar)
- `112` (sin asignar)

---

## 📝 Notas Importantes

### 1. Validación de Partidas

```python
# Patrón de validación
- Longitud total: 9 o 10 dígitos
- Primeros 3 dígitos: código de partido válido (001-137, 309-399)
- Siguientes 6 dígitos: partida individual (puede contener ceros adelante)
- Último dígito (opcional): verificador calculado por ARBA
```

### 2. Obtención del Dígito Verificador

El dígito verificador NO puede calcularse manualmente. Para obtenerlo:

1. Ir a [ARBA - Consulta de Deuda](https://app.arba.gov.ar/LiqPredet/InicioLiquidacion.do?imp=0&Frame=NO&origen=WEB)
2. Ingresar código de partido + partida (sin verificador)
3. El sistema mostrará el número completo con el dígito verificador

### 3. Búsqueda de Partidas

#### Por Dirección (Carto ARBA):
1. Acceder a [Carto ARBA](https://carto.arba.gov.ar/)
2. Buscar por dirección (partido, calle, altura)
3. Seleccionar parcela en el mapa
4. Click en ícono "i" para ver datos catastrales

#### Por Coordenadas (API WFS):
```
Endpoint: https://www.arba.gov.ar/geoserver/wfs
Servicio: WFS 2.0.0
Capa: arba:parcelas
Filtro CQL: partido='002' AND partida='004606'
```

### 4. Inmuebles con Subdivisiones

Para **departamentos, PH o unidades funcionales**:

```
Formato extendido: 002-004606-0-UF-001
                                  │   │
                                  │   └─ Número de unidad funcional
                                  └───── Identificador UF/SP
```

- **UF**: Unidad Funcional (Propiedad Horizontal)
- **SP**: Subparcela (otros casos)

### 5. Partidos Creados Recientemente

Los siguientes partidos fueron creados por leyes posteriores a 1990:

| Código | Partido | Año de Creación | Ley |
|--------|---------|-----------------|-----|
| 130 | Ezeiza | 1994 | 11.550 |
| 131 | San Miguel | 1994 | 11.551 |
| 132 | José C. Paz | 1994 | 11.551 |
| 133 | Malvinas Argentinas | 1994 | 11.551 |
| 134 | Punta Indio | 1994 | - |
| 135 | Hurlingham | 1994 | - |
| 136 | Ituzaingó | 1995 | - |

### 6. Islas del Delta

Las **islas del Río Paraná** tienen códigos especiales (300+):

```
309 - Islas Baradero
314 - Islas Campana
338 - Islas de Zárate
357 - Islas Tigre
387 - Islas Ramallo
396 - Islas San Fernando
398 - Islas de San Nicolás
399 - Islas San Pedro
```

**Nota:** Estas partidas tienen jurisdicción especial y pueden tener normativas distintas.

### 7. Complemento con Ceros

Si la partida tiene menos de 6 dígitos, se completa con ceros adelante:

```
Partida original: 4606
Formato correcto: 004606
Código completo: 002-004606-0
```

### 8. Diferencia con CABA

**NO confundir** con partidas de Ciudad de Buenos Aires (CABA/AGIP):
- ARBA: Provincia de Buenos Aires (códigos 001-399)
- AGIP: Ciudad Autónoma de Buenos Aires (sistema diferente)

### 9. Uso en Trámites

La partida inmobiliaria es requerida para:
- ✅ Inscripción en Ingresos Brutos provincial
- ✅ Consulta de deuda de Impuesto Inmobiliario
- ✅ Transferencias de dominio
- ✅ Solicitud de certificados catastrales
- ✅ Escrituración de inmuebles
- ✅ Informes de dominio

### 10. Actualización de Datos

Los códigos pueden actualizarse por:
- Creación de nuevos partidos (por ley provincial)
- Modificaciones territoriales
- Actualización catastral

**Última actualización de esta lista:** Enero 2026

---

## 🔗 Referencias Oficiales

- **ARBA Oficial:** https://www.arba.gov.ar/
- **Carto ARBA:** https://carto.arba.gov.ar/
- **Listado de Códigos:** https://www.arba.gov.ar/archivos/Publicaciones/codigospartidos.html
- **WFS GeoServer:** https://www.arba.gov.ar/geoserver/wfs
- **Consulta de Deuda:** https://app.arba.gov.ar/LiqPredet/InicioLiquidacion.do

---

## 💻 Ejemplo de Uso en Código

### Python - Validación y Parseo

```python
import json

# Cargar códigos
with open('codigos_partidos_arba.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    PARTIDOS = data['partidos']

def parse_partida(partida_completa: str) -> dict:
    """
    Parsea una partida inmobiliaria ARBA
    
    Args:
        partida_completa: "002004606" o "002-004606-0"
    
    Returns:
        dict con codigo_partido, nombre_partido, partida, verificador
    """
    # Limpiar guiones
    limpia = partida_completa.replace("-", "")
    
    # Validar longitud
    if len(limpia) not in [9, 10]:
        raise ValueError(f"Longitud inválida: {len(limpia)}. Debe ser 9 o 10 dígitos.")
    
    # Extraer componentes
    codigo_partido = limpia[:3]
    partida_individual = limpia[3:9]
    verificador = limpia[9] if len(limpia) == 10 else None
    
    # Validar código de partido
    if codigo_partido not in PARTIDOS:
        raise ValueError(f"Código de partido inválido: {codigo_partido}")
    
    return {
        "codigo_partido": codigo_partido,
        "nombre_partido": PARTIDOS[codigo_partido],
        "partida": partida_individual,
        "verificador": verificador,
        "formato_completo": f"{codigo_partido}-{partida_individual}-{verificador or '?'}"
    }

# Uso
resultado = parse_partida("002004606")
print(resultado)
# {
#   "codigo_partido": "002",
#   "nombre_partido": "Alberti",
#   "partida": "004606",
#   "verificador": None,
#   "formato_completo": "002-004606-?"
# }
```

### JavaScript/TypeScript

```typescript
interface PartidaARBA {
  codigoPartido: string;
  nombrePartido: string;
  partida: string;
  verificador?: string;
}

function parsePartida(partidaCompleta: string): PartidaARBA {
  // Limpiar guiones
  const limpia = partidaCompleta.replace(/-/g, '');
  
  // Validar longitud
  if (![9, 10].includes(limpia.length)) {
    throw new Error(`Longitud inválida: ${limpia.length}`);
  }
  
  // Extraer componentes
  const codigoPartido = limpia.substring(0, 3);
  const partida = limpia.substring(3, 9);
  const verificador = limpia.length === 10 ? limpia[9] : undefined;
  
  // Cargar desde JSON
  const partidos = require('./codigos_partidos_arba.json').partidos;
  
  if (!(codigoPartido in partidos)) {
    throw new Error(`Código de partido inválido: ${codigoPartido}`);
  }
  
  return {
    codigoPartido,
    nombrePartido: partidos[codigoPartido],
    partida,
    verificador
  };
}
```

---

## 📞 Soporte

Para consultas sobre partidas inmobiliarias:
- **Tel:** 0800-321-ARBA (2722)
- **Email:** consultas@arba.gob.ar
- **Atención presencial:** Oficinas ARBA en cada partido

---

**Documento generado:** 26 de enero de 2025  
**Fuente:** ARBA - Agencia de Recaudación Provincia de Buenos Aires
