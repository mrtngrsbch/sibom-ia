# Quickstart - Arquitectura .agents/

## Setup en 5 Minutos

---

## Opción 1: Script Automático (Recomendado) ⚡

```bash
# 1. Copiar el script a tu proyecto
cp /path/to/sibom-scraper-assistant/.agents/hooks/setup_agents.py tu-proyecto/

# 2. Ejecutar en tu proyecto
cd tu-proyecto
python setup_agents.py

# 3. Listo! ✅
```

**Opciones disponibles:**

```bash
# Proyecto backend-only
python setup_agents.py --project-type backend

# Proyecto frontend-only
python setup_agents.py --project-type frontend

# Proyecto data science
python setup_agents.py --project-type data-science

# Con integración Kiro
python setup_agents.py --with-kiro
```

---

## Opción 2: Manual (3 pasos)

### Paso 1: Crear estructura (30 segundos)

```bash
mkdir -p .agents/{specs,steering,hooks,workflows}
```

### Paso 2: Crear README (1 minuto)

```bash
cat > .agents/README.md << 'EOF'
# .agents/ - Arquitectura de Agentes AI

Esta carpeta contiene reglas para que herramientas AI (Claude, Droid, etc.)
trabajen efectivamente en este proyecto.

## Estructura

- `specs/` - Arquitectura del proyecto
- `steering/` - Reglas de código
- `hooks/` - Automatizaciones
- `workflows/` - Procedimientos

## Configurar Claude Code

Crear `.claude/CLAUDE.md` con:

```markdown
## Antes de trabajar

1. LEER: `.agents/specs/`
2. RESPETAR: `.agents/steering/`
```
EOF
```

### Paso 3: Configurar Claude Code (2 minutos)

```bash
mkdir -p .claude

cat > .claude/CLAUDE.md << 'EOF'
# CLAUDE.md

## Antes de trabajar

1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como reglas OBLIGATORIAS
3. CONSULTAR: Documentación si necesitas detalles

## Reglas Críticas

✅ HACER:
- Leer specs antes de cambiar código
- Seguir patrones de steering
- Usar types/type hints

❌ NO HACER:
- Ignorar patrones establecidos
- Mezclar responsabilidades
- Omitir manejo de errores
EOF
```

### Paso 4: Commit (30 segundos)

```bash
git add .agents/ .claude/
git commit -m "feat: add .agents/ architecture"
```

**¡Listo!** 🎉

---

## Verificar que Funciona

### Test 1: Claude Code lee .agents/

```bash
# En Claude Code, preguntar:
"¿Qué arquitectura tiene este proyecto?"
# Debería leer .agents/specs/ primero
```

### Test 2: Claude Code respeta .agents/

```bash
# En Claude Code, pedir:
"Agrega un endpoint para exportar datos"
# Debería seguir patrones en .agents/steering/
```

---

## Archivos Mínimos Necesarios

```
.tu-proyecto/
├── .agents/
│   ├── README.md                    # Descripción de la carpeta
│   ├── specs/
│   │   └── 01-project-overview.md   # Arquitectura básica
│   └── steering/
│       └── coding-patterns.md       # Reglas de código
└── .claude/
    └── CLAUDE.md                    # Configuración de Claude
```

---

## Personalización Rápida

### Agregar una regla de código

```bash
# Editar steering
vim .agents/steering/coding-patterns.md

# Agregar:
## ✅ HACER
- Usar type hints en todas las funciones
- Escribir tests para nuevo código

## ❌ NO HACER
- Usar globales para configuración
- Omitir manejo de errores
```

### Agregar arquitectura de un componente

```bash
# Crear spec
vim .agents/specs/02-api-architecture.md

# Agregar:
# API Architecture

## Endpoints

- GET /api/users - Listar usuarios
- POST /api/users - Crear usuario

## Tecnologías

- FastAPI 0.104+
- Pydantic v2
```

---

## Troubleshooting Rápido

### Problema: Claude ignora .agents/

**Solución:**
```bash
# Verificar que .claude/CLAUDE.md existe
cat .claude/CLAUDE.md

# Debe mencionar .agents/
```

### Problema: No sé qué escribir en specs/

**Solución:**
```markdown
# Mínimo viable:

## Stack Tecnológico

- Backend: [Tu lenguaje/framework]
- Frontend: [Tu framework]
- DB: [Tu base de datos]

## Estructura

```
project/
├── backend/
├── frontend/
└── shared/
```
```

### Problema: Quiero agregar más herramientas

**Solución:**
```bash
# Para Droid/Factory:
mkdir -p .factory
vim .factory/config.yml

# Agregar:
agents_context:
  read_first:
    - .agents/specs/
    - .agents/steering/
```

---

## ¿Ahora qué?

1. **Personalizar specs** - Describe tu arquitectura real
2. **Agregar reglas** - Documenta patrones de tu equipo
3. **Probar con Claude** - Verifica que funciona
4. **Documentar para tu equipo** - Comparte el conocimiento

## Recursos

- **[Guía Completa](IMPLEMENTATION_GUIDE.md)** - Implementación detallada
- **[Mejores Prácticas](BEST_PRACTICES.md)** - Pro tips
- **[Ejemplos](EXAMPLES.md)** - Proyectos reales

---

**¿Necesitas ayuda?** Revisa la [GUIA_COMPLETA.md](GUIA_COMPLETA.md)

**Tiempo estimado:** 5 minutos
**Dificultad:** Fácil
**Resultado:** Arquitectura .agents/ funcional ✅
