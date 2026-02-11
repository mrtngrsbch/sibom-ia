# Menú Interactivo - Mangrullo Scraper

## 🎯 Nueva Funcionalidad: Menú Numérico

Cuando el scraper encuentra un boletín que ya existe, ahora muestra un menú interactivo donde puedes elegir qué hacer ingresando **números (1-3)**.

## 📋 Opciones del Menú

Cuando un archivo ya existe, verás:

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

¿Qué deseas hacer con el boletín 105º?
  1. Saltar y continuar con el siguiente
  2. Sobreescribir este boletín
  3. Cancelar todo el proceso

Elige una opción (1-3) [1]:
```

### Opciones Disponibles

| Opción                 | Tecla     | Descripción                              | Comportamiento                                 |
| ---------------------- | --------- | ---------------------------------------- | ---------------------------------------------- |
| **Saltar y continuar** | 1 o Enter | Mantiene el archivo existente y continúa | ⏭ Marca como "🤖 Creado" y procesa el siguiente |
| **Sobreescribir**      | 2         | Re-procesa el boletín                    | ♻️ Descarga y procesa nuevamente                |
| **Cancelar proceso**   | 3         | Termina todo                             | ✗ Sale del programa completamente              |

## 🎮 Cómo Usar

### Navegación con Teclado

1. **Teclas 1-3**: Seleccionar opción
2. **Enter sin número**: Usa opción por defecto (1)
3. **Ctrl+C**: Cancelar proceso

### Flujo de Trabajo Típico

#### Escenario 1: Proceso Incremental (Recomendado)

```bash
# Primera ejecución: procesar 10 boletines
python sibom_scraper.py --limit 10

# Segunda ejecución: procesar 20 (saltará los primeros 10)
python sibom_scraper.py --limit 20
```

**Cuando encuentre archivos existentes:**
1. Ver el menú
2. Presionar Enter (opción por defecto: "Saltar y continuar")
3. El proceso continúa automáticamente con los nuevos

#### Escenario 2: Re-procesar Boletines con Error

```bash
python sibom_scraper.py --limit 15
```

**Cuando veas un boletín con error:**
1. Ver el menú
2. Presionar ↓ para "Sobreescribir"
3. Presionar Enter
4. El boletín se procesa nuevamente

#### Escenario 3: Modo Automático (Sin Interacción)

Si no quieres ver el menú, usa `--skip-existing`:

```bash
python sibom_scraper.py --limit 50 --skip-existing
```

Esto salta automáticamente todos los archivos existentes sin preguntar.

## 🔧 Casos de Uso

### Caso 1: Proceso Interrumpido

Si el scraper se interrumpió a la mitad:

```bash
# Continuar desde donde quedó
python sibom_scraper.py --limit 100
```

- Archivos completados: Menú aparece → Selecciona "Saltar"
- Archivos faltantes: Se procesan normalmente

### Caso 2: Corregir Errores

Si algunos boletines tienen errores:

```bash
# Re-ejecutar sin --skip-existing
python sibom_scraper.py --limit 20
```

- Boletines correctos: Selecciona "Saltar"
- Boletines con error: Selecciona "Sobreescribir"

### Caso 3: Automatización

Para cron jobs o scripts automatizados:

```bash
# Sin interacción
python sibom_scraper.py --limit 100 --skip-existing --parallel 3
```

## 📊 Comparación: Antes vs Ahora

### ❌ Antes (Versión Anterior)

```
⚠ El archivo Carlos_Tejedor_105.json ya existe
¿Deseas sobreescribir? (s/N): n
[PROCESO SE DETIENE - MAL]
```

**Problema:** Al responder "N", el proceso se detenía completamente.

### ✅ Ahora (Nueva Versión)

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

? ¿Qué deseas hacer con el boletín 105º?
 » Saltar y continuar con el siguiente  ← Enter
   Sobreescribir este boletín
   Cancelar todo el proceso

⏭ Saltando boletín 105º

📰 Procesando boletín: 104º
[PROCESO CONTINÚA - BIEN]
```

**Ventajas:**
- ✅ El proceso continúa automáticamente
- ✅ Interfaz más clara y visual
- ✅ Navegación con flechas (más intuitivo)
- ✅ Opción explícita para cancelar

## 🎨 Ejemplos Visuales

### Ejemplo 1: Saltar y Continuar

```
═══ NIVELES 2 y 3: PROCESANDO 5 BOLETINES ═══

⚠ El archivo Carlos_Tejedor_105.json ya existe

? ¿Qué deseas hacer con el boletín 105º? (Use arrow keys)
 » Saltar y continuar con el siguiente
   Sobreescribir este boletín
   Cancelar todo el proceso

[Presionas Enter]

⏭ Saltando boletín 105º

📰 Procesando boletín: 104º
🔗 Nivel 2: Extrayendo enlaces de contenido...
✓ Encontrados 1 enlaces de contenido
```

### Ejemplo 2: Sobreescribir

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

? ¿Qué deseas hacer con el boletín 105º? (Use arrow keys)
   Saltar y continuar con el siguiente
 » Sobreescribir este boletín
   Cancelar todo el proceso

[Presionas Enter]

♻️ Sobreescribiendo Carlos_Tejedor_105.json...

📰 Procesando boletín: 105º
🔗 Nivel 2: Extrayendo enlaces de contenido...
```

### Ejemplo 3: Cancelar

```
⚠ El archivo Carlos_Tejedor_105.json ya existe

? ¿Qué deseas hacer con el boletín 105º? (Use arrow keys)
   Saltar y continuar con el siguiente
   Sobreescribir este boletín
 » Cancelar todo el proceso

[Presionas Enter]

✗ Proceso cancelado por el usuario
```

## 💡 Tips y Trucos

### Tip 1: Opción por Defecto

La primera opción ("Saltar y continuar") es la más común. Solo presiona Enter para aceptarla rápidamente.

### Tip 2: Teclas Rápidas

- **Enter directo**: Salta el boletín (opción 1)
- **2 + Enter**: Sobrescribe
- **3 + Enter**: Cancela proceso
- **Ctrl+C**: Cancela (en cualquier momento)

### Tip 3: Modo Batch

Para procesar muchos boletines sin interrupciones:

```bash
python sibom_scraper.py --limit 100 --skip-existing
```

### Tip 4: Re-procesar Solo Errores

1. Revisa `boletines/boletines.md`
2. Identifica boletines con "❌ Error"
3. Borra esos archivos JSON manualmente
4. Re-ejecuta el scraper

```bash
# Borrar boletín con error
rm boletines/Carlos_Tejedor_105.json

# Re-procesar
python sibom_scraper.py --limit 110
```

## 🚀 Dependencias

No requiere bibliotecas adicionales. Usa solo `input()` de Python estándar.

## 📝 Notas Técnicas

### Implementación

- Usa `input()` nativo de Python
- Compatible con cualquier terminal
- Sin dependencias externas adicionales

### Flujo de Control

```python
if archivo_existe:
    if skip_existing:
        # Salta automáticamente
        return existing_data
    else:
        # Muestra menú numérico
        choice = input("Elige una opción (1-3) [1]: ").strip() or "1"
        if choice == '1':
            return existing_data
        elif choice == '2':
            # Continúa procesando (sobrescribe)
        else:  # '3' o inválido
            sys.exit(0)
```

---

**Versión:** 2.3
**Fecha:** 2025-12-30
**Nueva característica:** Menú interactivo numérico (mejorado para compatibilidad)
