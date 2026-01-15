# Plan de Coexistencia: .kiro/ y .agents/

## Objetivo

Preservar TODO el trabajo de Kiro mientras creamos `.agents/` específico para agentes AI.

---

## Paso 1: Renombrar .kiro/ → docs/technical/

### Por qué renombrar:
- Nombre más claro y descriptivo
- No atado a herramienta específica
- Estructura canónica de proyectos

### Comando:
```bash
git mv .kiro docs/technical
```

### Resultado:
```
docs/
└── technical/
    ├── specs/
    │   ├── tasks.md                    ← Plan de implementación
    │   ├── design.md                   ← Documento de diseño
    │   ├── 01-proyecto-overview.md
    │   ├── 02-backend-scraper.md
    │   └── ...
    ├── steering/
    │   ├── python-patterns.md
    │   ├── typescript-patterns.md
    │   └── performance-optimization.md
    ├── hooks/
    └── ANALYSIS_SUMMARY.md
```

**TODO el contenido de Kiro se preserva intacto.**

---

## Paso 2: Crear .agents/ DESDE CERO

### Por qué desde cero:
- `.agents/` tiene propósito diferente (reglas para AI)
- No es "extracción simplificada" de `.kiro/`
- Es contenido ORIGINAL con su propia razón de ser

### Estructura de .agents/:
```
.agents/
├── README.md                    ← "Qué es esta carpeta"
├── specs/                      ← Arquitectura CONCISA
│   ├── 01-proyecto-overview.md     (100-150 líneas)
│   ├── 02-backend-architecture.md  (100-150 líneas)
│   ├── 03-frontend-architecture.md (100-150 líneas)
│   └── 04-integracion.md            (80-100 líneas)
│
├── steering/                   ← REGLAS para agentes
│   ├── python-patterns.md          (Extractos CONCISOS de docs/technical/)
│   ├── typescript-react-patterns.md
│   └── error-handling.md
│
├── hooks/                      ← Automatizaciones
│   ├── sync_from_kiro.py           ← Script de sincronización
│   └── test-validation.md
│
└── workflows/                  ← Procedimientos
    └── deploy-completo.md
```

### Diferencia clave en CONTENIDO:

#### Ejemplo: docs/technical/ (DETALLADO)
```markdown
# Python Engineering Patterns - SIBOM Scraper

## Class-Based Design Pattern

**Observed Pattern:** `python-cli/sibom_scraper.py:25-40`

```python
class SibomScraper:
    def __init__(self, base_url: str, output_dir: str, openrouter_api_key: str):
        self.openrouter_client = OpenAI(...)
        self.rate_limit_delay = 3
```

**Engineering Standards:**
- Single Responsibility: Each class handles one domain
- Dependency Injection: External dependencies via constructor
- [60 líneas más de análisis detallado...]
```

#### Ejemplo: .agents/ (CONCISO)
```markdown
# Python Patterns

## QUÉ hacer

- Usar clases con `__init__` para inyección de dependencias
- Cada clase tiene UNA responsabilidad
- Configurar vía parámetros de constructor

## QUÉ NO hacer

- NUNCA usar globales para configuración
- NO mezclar responsabilidades en una clase

## Referencia

Para detalles profundos, ver: `docs/technical/steering/python-patterns.md`
```

---

## Paso 3: Integración entre ambos

### Flujo de trabajo:

```
1. Ingeniero humano
   ↓ Estudia
   docs/technical/steering/python-patterns.md (600 líneas, código real)
   ↓
   Extrae LO ESENCIAL para agentes

2. Ingeniero escribe
   ↓
   .agents/steering/python-patterns.md (150 líneas, reglas concisas)

3. Agente AI (Claude Code)
   ↓ Lee
   .agents/steering/python-patterns.md
   ↓
   Aplica reglas al escribir código

4. Si necesita detalles
   ↓ Consulta
   docs/technical/steering/python-patterns.md
   ↓
   Comprende implementación específica
```

### Relación:
- `docs/technical/` = **Fuente de verdad técnica** (read-only después de generado)
- `.agents/` = **Reglas operativas** (se mantiene activamente)

---

## Paso 4: Configurar herramientas

### Claude Code

```markdown
# .claude/CLAUDE.md

## Antes de trabajar

1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como reglas OBLIGATORIAS
3. CONSULTAR: `docs/technical/` solo si necesitas detalles de implementación

## Para cambios arquitectónicos

1. Proponer cambio en `.agents/specs/` PRIMERO
2. Esperar aprobación
3. Implementar siguiendo `.agents/steering/`
4. Si agregas patrones nuevos, documentar en `docs/technical/`
```

### Droid (Factory)

```yaml
# .factory/config.yml
agents:
  context:
    - .agents/specs/          # Leer primero
    - .agents/steering/       # Respetar siempre

  reference_docs:
    - docs/technical/         # Consultar si necesita detalles

  constraints:
    hard:
      - .agents/steering/python-patterns.md
      - .agents/steering/typescript-react-patterns.md
```

---

## Paso 5: Script de sincronización

### Propósito:

Mantener `.agents/` actualizado cuando `docs/technical/` cambia.

### Script: `.agents/hooks/sync_from_docs.py`

```python
"""
Sincroniza docs/technical/ → .agents/

NO es "extracción simplificada".
Es "mantener referencias y extractos concisos".
"""

def sync_steering_file(technical_file, agents_file):
    """
    Lee archivo técnico y genera versión para agentes
    """
    # Leer contenido técnico
    technical_content = technical_file.read_text()

    # Extraer SECCIONES CLAVE (no código detallado)
    essential_sections = extract_sections(technical_content, [
        '## Principles',
        '## Standards',
        '## Requirements',
        '## Patterns'
    ])

    # Simplificar a reglas accionables
    agents_content = simplify_to_rules(essential_sections)

    # Agregar referencia al documento técnico
    agents_content += f"\n\n## Referencia técnica completa\n\n"
    agents_content += f"Ver: `{technical_file.relative_to(root)}`\n"

    # Escribir en .agents/
    agents_file.write_text(agents_content)
```

### Uso:

```bash
# Ejecutar manualmente cuando docs/technical/ cambia
python .agents/hooks/sync_from_docs.py

# O ejecutar automáticamente via hook (pre-commit)
```

---

## Resultado Final

### Estructura del proyecto:

```
sibom-scraper-assistant/
├── docs/
│   ├── technical/             ← Ex .kiro/ (DOCUMENTACIÓN COMPLETA)
│   │   ├── specs/
│   │   │   ├── tasks.md       ← Plan 4 sprints
│   │   │   ├── design.md      ← Doc diseño completo
│   │   │   └── ...
│   │   ├── steering/
│   │   │   ├── python-patterns.md      ← 600 líneas
│   │   │   └── typescript-patterns.md  ← 500 líneas
│   │   └── ANALYSIS_SUMMARY.md
│   │
│   └── user/                 ← Documentación para usuarios
│       ├── tutorials/
│       └── FAQ.md
│
├── .agents/                  ← REGLAS PARA AGENTES AI
│   ├── specs/                ← Arquitectura concisa
│   │   ├── 01-proyecto-overview.md    (100 líneas)
│   │   └── 02-backend-architecture.md (100 líneas)
│   ├── steering/             ← Reglas extraídas de docs/technical/
│   │   ├── python-patterns.md         (150 líneas)
│   │   └── typescript-react-patterns.md (150 líneas)
│   └── hooks/                ← Sincronización
│       └── sync_from_docs.py
│
├── python-cli/               # Backend
├── chatbot/                  # Frontend
└── README.md
```

### Quién lee qué:

| Rol | Lee | Propósito |
|-----|-----|-----------|
| **Ingeniero humano** | `docs/technical/` | Estudiar sistema a fondo |
| **Agente AI** | `.agents/` | Saber QUÉ hacer |
| **Usuario final** | `docs/user/` | Usar el sistema |
| **Agente AI (detalles)** | `docs/technical/` | Comprender implementación |

---

## Beneficios

### 1. Preservación completa
- ✅ TODO el trabajo de Kiro queda intacto
- ✅ Plan de sprints, diseño, patrones - todo accesible
- ✅ Mejor nombre (docs/technical/ vs .kiro/)

### 2. Propósitos claros
- ✅ `.agents/` NO es una "versión simplificada"
- ✅ Es contenido ORIGINAL con su propia razón de ser
- ✅ Dos herramientas, dos propósitos, sin redundancia

### 3. Mantenibilidad
- ✅ `docs/technical/` es READ-ONLY (referencia)
- ✅ `.agents/` se mantiene activamente
- ✅ Script de sincronización mantiene coherencia

### 4. Escalabilidad
- ✅ Fácil agregar nuevas herramientas (solo leen `.agents/`)
- ✅ Fácil actualizar documentación técnica (solo editar `docs/technical/`)
- ✅ Separación de concerns clara

---

## Conclusión

**NO eliminamos `.kiro/` - lo renombramos a `docs/technical/`.**

**NO extraemos contenido - creamos `.agents/` desde cero.**

**Dos carpetas, dos propósitos, sin conflicto.** 🎯
