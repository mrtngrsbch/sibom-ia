# Plan de Experimento: Kiro como Analista

## Objetivo

Usar Kiro como "analista junior" para entender el proyecto, pero mantener `.agents/` como fuente de verdad.

## FASE 1: Dejar que Kiro analice (sin tocar nada)

```bash
# 1. Instalar Kiro si no lo tenés
# 2. Abrir Kiro en este proyecto

# 3. PRIMERO: Spec Mode - Análisis técnico
Prompt: "Analiza la arquitectura técnica de este proyecto Python CLI.
         ¿Qué hace? ¿Cómo está estructurado?
         ¿Cuáles son los componentes principales?
         NO modifiques código, solo genera specs técnicas."

# 4. DESPUÉS: Vibe Mode - Análisis de estilo
Prompt: "Analiza el estilo y convenciones de este proyecto.
         ¿Patrones de código? ¿Estilo de documentación?
         ¿Filosofía de diseño? ¿Preferencias técnicas?
         Genera steering guidelines sin modificar código."
```

**Resultado esperado:**
- `.kiro/` carpeta creada con su análisis
- Dos conjuntos de archivos: specs (técnicas) y steering (estilo)
- Entenderás qué estructura propone Kiro en ambos aspectos

**Por qué ambos modos:**
- **Spec Mode** → Captura arquitectura, APIs, componentes (= `.agents/specs/`)
- **Vibe Mode** → Captura reglas, estilo, convenciones (= `.agents/steering/`)

## FASE 2: Revisión humana (tú)

1. **Leer `.kiro/specs/`**
   - ¿Entendió bien el proyecto?
   - ¿Qué faltó?
   - ¿Qué sobró?

2. **Leer `.kiro/steering/`**
   - ¿Reglas útiles?
   - ¿Algo demasiado genérico?

3. **Leer `.kiro/hooks/`**
   - ¿Automatizaciones prácticas?
   - ¿Algo irrelevante?

## FASE 3: Extracción inteligente → `.agents/`

```bash
# Copiar/mejorar ideas buenas de .kiro/ a .agents/

# Ejemplo:
.kiro/specs/project-overview.md  →  .agents/specs/01-proyecto.md
.kiro/steering/python-style.md   →  .agents/steering/codigo-python.md
.kiro/hooks/test-automation.md   →  .agents/hooks/testing.md
```

**Regla de oro:**
- Solo copiar lo que sea BUENO y RELEVANTE
- Mejorarlo mientras se copia
- No aceptar nada ciegamente

## FASE 4: Crear sincronizador

Una vez que `.agents/` tenga contenido real:

```python
# .agents/hooks/sync_to_kiro.py
"""
Sincroniza .agents/ (fuente de verdad) → .kiro/ (vista UI)

- Lee archivos en .agents/
- Convierte a formato Kiro si es necesario
- Actualiza .kiro/ sin modificar .agents/
"""
```

## FASE 5: Workflow continuo

```
1. Editás .agents/specs/ (fuente de verdad)
2. Ejecutás hook: sync_to_kiro
3. Abrís Kiro → ves specs actualizados en su UI linda
4. Kiro te ayuda a visualizar, NO a mandar
```

---

## ¿Por qué este orden?

1. **Primero entendés** qué propone Kiro
2. **Después decidís** qué tiene sentido
3. **Finalmente automatizás** la sincronización

Es lo contrario de "dejar que Kiro mande".
Es "usar Kiro como herramienta, no como dueño".

---

## Resultado final

```
.agents/          ← Vos editás esto (fuente de verdad)
.kiro/            ← Sincronizado automáticamente (vista UI)
.claude/          ← Lee .agents/ (implementador)
.factory/droids/  ← Ejecuta .agents/hooks (executor)
.obsidian/        ← Lee .agents/specs (visor humano)
```

**Todas las herramientas sirven a la arquitectura, no al revés.**
