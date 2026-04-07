#!/usr/bin/env python3
"""
Script de Inicialización - Arquitectura .agents/

Este script crea la estructura base de .agents/ en cualquier proyecto.

Uso:
    python setup_agents.py [--project-type TYPE] [--with-kiro]

Opciones:
    --project-type TYPE    Tipo de proyecto (fullstack, backend, frontend, data-science)
    --with-kiro            Incluir scripts de sincronización con Kiro
"""

import argparse
from pathlib import Path
from datetime import datetime
import sys


class AgentsSetup:
    """Configura estructura .agents/ en un proyecto"""

    def __init__(self, project_type: str = "fullstack", with_kiro: bool = False):
        self.project_type = project_type
        self.with_kiro = with_kiro
        self.root = Path.cwd()
        self.agents_dir = self.root / '.agents'

        # Estructura base
        self.structure = {
            'specs': self._get_specs_structure(),
            'steering': self._get_steering_structure(),
            'hooks': [],
            'workflows': []
        }

    def _get_specs_structure(self):
        """Retorna archivos de specs según tipo de proyecto"""
        specs_map = {
            'fullstack': [
                '01-system-overview.md',
                '02-backend-architecture.md',
                '03-frontend-architecture.md',
                '04-integration.md',
            ],
            'backend': [
                '01-api-architecture.md',
                '02-database-schema.md',
                '03-auth-strategy.md',
                '04-deployment.md',
            ],
            'frontend': [
                '01-component-architecture.md',
                '02-state-management.md',
                '03-routing-strategy.md',
                '04-styling-guide.md',
            ],
            'data-science': [
                '01-project-overview.md',
                '02-data-pipeline.md',
                '03-model-architecture.md',
                '04-experiment-tracking.md',
            ]
        }
        return specs_map.get(self.project_type, specs_map['fullstack'])

    def _get_steering_structure(self):
        """Retorna archivos de steering según tipo de proyecto"""
        steering_map = {
            'fullstack': [
                'backend-patterns.md',
                'frontend-patterns.md',
                'api-contracts.md',
                'testing-patterns.md',
            ],
            'backend': [
                'api-patterns.md',
                'database-patterns.md',
                'auth-patterns.md',
                'error-handling.md',
            ],
            'frontend': [
                'react-patterns.md',
                'state-management-patterns.md',
                'styling-patterns.md',
                'performance-patterns.md',
            ],
            'data-science': [
                'data-patterns.md',
                'model-patterns.md',
                'experiment-patterns.md',
                'visualization-patterns.md',
            ]
        }
        return steering_map.get(self.project_type, steering_map['fullstack'])

    def create_structure(self):
        """Crea estructura de directorios"""
        print("\n📁 Creando estructura de directorios...")

        for folder in ['specs', 'steering', 'hooks', 'workflows']:
            folder_path = self.agents_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ {folder}/")

    def create_readme(self):
        """Crea README.md en .agents/"""
        readme_content = f"""# .agents/ - Arquitectura de Agentes AI

Esta carpeta contiene la arquitectura de proyecto agnóstica a herramientas.

## 📁 Estructura

```
.agents/
├── specs/       ← Arquitectura del proyecto (READ-ONLY)
├── steering/    ← Reglas para agentes AI (EDITABLE)
├── hooks/       ← Scripts de sincronización
└── workflows/   ← Procedimientos multi-paso
```

## 🔄 Configurar Herramientas

### Claude Code

Crear `.claude/CLAUDE.md`:

```markdown
# CLAUDE.md

## Antes de trabajar

1. LEER: `.agents/specs/` para entender arquitectura
2. RESPETAR: `.agents/steering/` como reglas OBLIGATORIAS
3. CONSULTAR: Documentación técnica si necesitas detalles
```

### Droid/Factory

Configurar `.factory/config.yml`:

```yaml
agents_context:
  read_first:
    - .agents/specs/
    - .agents/steering/
```

## 📚 Documentación

- **[Guía de Implementación](IMPLEMENTATION_GUIDE.md)**
- **[Mejores Prácticas](BEST_PRACTICES.md)**

---

**Creado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Tipo de proyecto:** {self.project_type}
"""

        readme_path = self.agents_dir / 'README.md'
        readme_path.write_text(readme_content, encoding='utf-8')
        print("   ✅ README.md")

    def create_template_files(self):
        """Crea archivos de plantilla"""
        print("\n📝 Creando archivos de plantilla...")

        # Crear archivos de specs con plantillas
        for spec_file in self.structure['specs']:
            spec_path = self.agents_dir / 'specs' / spec_file
            spec_content = self._get_spec_template(spec_file)
            spec_path.write_text(spec_content, encoding='utf-8')
            print(f"   ✅ specs/{spec_file}")

        # Crear archivos de steering con plantillas
        for steering_file in self.structure['steering']:
            steering_path = self.agents_dir / 'steering' / steering_file
            steering_content = self._get_steering_template(steering_file)
            steering_path.write_text(steering_content, encoding='utf-8')
            print(f"   ✅ steering/{steering_file}")

        # Crear .gitkeep en hooks y workflows
        (self.agents_dir / 'hooks' / '.gitkeep').write_text('')
        (self.agents_dir / 'workflows' / '.gitkeep').write_text('')
        print("   ✅ hooks/.gitkeep")
        print("   ✅ workflows/.gitkeep")

    def _get_spec_template(self, filename: str) -> str:
        """Genera plantilla para archivo de spec"""
        title = filename.replace('-', ' ').replace('.md', '').title()

        return f"""# {title}

## ⚠️ ARCHIVO DE PLANTILLA

Este archivo debe ser personalizado para tu proyecto.

## Descripción

[Agregar descripción de este componente del sistema]

## Arquitectura

```mermaid
graph TD
    A[Componente] --> B[Dependencia 1]
    A --> C[Dependencia 2]
```

## Tecnologías

- **Tecnología 1**: Versión X.Y
- **Tecnología 2**: Versión Z.W

## Funcionalidades Principales

1. **Funcionalidad 1**: Descripción
2. **Funcionalidad 2**: Descripción
3. **Funcionalidad 3**: Descripción

## Puntos de Integración

- Con componente X: [describir]
- Con componente Y: [describir]

## Para Más Detalles

Ver documentación técnica en `docs/technical/` (si existe).

---

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _get_steering_template(self, filename: str) -> str:
        """Genera plantilla para archivo de steering"""
        title = filename.replace('-', ' ').replace('.md', '').title()

        return f"""# {title}

## ⚠️ BASE EDITABLE

Este archivo contiene reglas que los agentes AI DEBEN seguir.

Edita este archivo para agregar reglas específicas de tu proyecto.

## Principios Generales

1. **Principio 1**: [Descripción]
2. **Principio 2**: [Descripción]
3. **Principio 3**: [Descripción]

## ✅ HACER

- [Práctica recomendada 1]
- [Práctica recomendada 2]
- [Práctica recomendada 3]

## ❌ NO HACER

- [Anti-patrón 1]
- [Anti-patrón 2]
- [Anti-patrón 3]

## Ejemplos

```python
# ✅ BUEN ejemplo
def good_example():
    \"\"\"[Descripción de qué hace bueno este ejemplo]\"\"\"
    pass

# ❌ MAL ejemplo
def bad_example():
    \"\"\"[Descripción de qué hace malo este ejemplo]\"\"\"
    pass
```

## Referencias

- Documentación relacionada: [link o archivo]
- Mejores prácticas: [link o archivo]

---

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    def create_gitignore(self):
        """Crea .gitignore si no existe"""
        gitignore_path = self.agents_dir / '.gitignore'
        gitignore_content = """# Archivos generados automáticamente
SYNC_REPORT.md
PROPAGATION_LOG.md

# Logs
*.log

# Archivos temporales
*.tmp
*.bak
"""
        gitignore_path.write_text(gitignore_content, encoding='utf-8')
        print("   ✅ .gitignore")

    def setup_claude(self):
        """Configura Claude Code"""
        claude_dir = self.root / '.claude'
        claude_dir.mkdir(exist_ok=True)

        claude_md_content = """# CLAUDE.md - Instrucciones para Claude Code

Este archivo configura cómo Claude Code debe trabajar en este proyecto.

## 🎯 Antes de Empezar a Trabajar

### 1. LEER - Entender el Proyecto

Antes de modificar CUALQUIER código, debes:

1. **Leer `.agents/specs/`** para entender:
   - Arquitectura general del sistema
   - Stack tecnológico
   - Flujo de datos
   - Patrones arquitectónicos

2. **Identificar componentes relevantes** para la tarea actual

### 2. RESPETAR - Seguir Reglas Obligatorias

**DEBES seguir las reglas en `.agents/steering/`:**

- Patrones de código específicos del proyecto
- Estándares de formato
- Manejo de errores
- Testing

Estas reglas son **OBLIGATORIAS**, no opcionales.

### 3. CONSULTAR - Solo si Necesitas Detalles

Si necesitas detalles profundos de implementación:
- Consulta documentación técnica si existe
- Busca ejemplos de código similares en el proyecto

## ⚠️ REGLAS CRÍTICAS

### ✅ HACER

- **SIEMPRE** leer `.agents/specs/` antes de cambiar código
- **SIEMPRE** seguir patrones en `.agents/steering/`
- **SIEMPRE** mantener separación de responsabilidades
- **SIEMPRE** usar tipos/type hints

### ❌ NO HACER

- **NUNCA** modificar código sin leer specs primero
- **NUNCA** ignorar patrones establecidos
- **NUNCA** mezclar responsabilidades
- **NUNCA** omitir manejo de errores

## 🚀 Flujo de Trabajo

### Para modificar código existente

1. **LEER**: Archivo relevante en `.agents/steering/`
2. **IDENTIFICAR**: Qué patrón seguir
3. **IMPLEMENTAR**: Aplicando los patrones
4. **VERIFICAR**: Que no rompas reglas

### Para agregar nueva funcionalidad

1. **PROPONER**: Primero en `.agents/specs/` si es cambio arquitectónico
2. **ESPERAR**: Aprobación si es necesario
3. **IMPLEMENTAR**: Siguiendo `.agents/steering/`
4. **DOCUMENTAR**: Si agregas patrones nuevos

## 📝 Checklist Antes de Sugerir Commits

Antes de sugerir que el usuario haga commit:

- [ ] Leí `.agents/specs/` relevantes
- [ ] Seguí patrones en `.agents/steering/`
- [ ] No rompí reglas OBLIGATORIAS
- [ ] Mantuve separación de componentes
- [ ] Agregué types/type hints
- [ ] Manejé errores apropiadamente
- [ ] Código es consistente con patrones existentes

---

**Última actualización:** Ver `.agents/README.md` para cambios recientes

**¿Dudas?** Consulta `.agents/README.md`
"""

        claude_md_path = claude_dir / 'CLAUDE.md'
        claude_md_path.write_text(claude_md_content, encoding='utf-8')
        print("   ✅ .claude/CLAUDE.md")

    def print_summary(self):
        """Imprime resumen de la instalación"""
        print("\n" + "=" * 60)
        print("✅ Estructura .agents/ creada exitosamente")
        print("=" * 60)

        print(f"\n📊 Resumen:")
        print(f"   - Tipo de proyecto: {self.project_type}")
        print(f"   - Ubicación: {self.agents_dir}")
        print(f"   - Specs creadas: {len(self.structure['specs'])}")
        print(f"   - Steering creados: {len(self.structure['steering'])}")

        print(f"\n📝 Próximos pasos:")
        print(f"   1. Personalizar archivos en .agents/specs/")
        print(f"   2. Agregar reglas en .agents/steering/")
        print(f"   3. Revisar .claude/CLAUDE.md")
        print(f"   4. Commit: git add .agents/ .claude/")
        print(f"   5. Mensaje: git commit -m 'feat: add .agents/ architecture'")

        if self.with_kiro:
            print(f"\n🔗 Con Kiro:")
            print(f"   - Ejecuta: kiro analyze ./")
            print(f"   - Luego: python .agents/hooks/sync_from_kiro.py")

        print(f"\n📚 Documentación:")
        print(f"   - Ver: .agents/README.md")
        print(f"   - Guía completa: Buscar IMPLEMENTATION_GUIDE.md")

    def run(self):
        """Ejecuta setup completo"""
        print("\n" + "=" * 60)
        print("🚀 Setup de Arquitectura .agents/")
        print("=" * 60)
        print(f"📁 Proyecto: {self.root.name}")
        print(f"📋 Tipo: {self.project_type}")
        print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Crear estructura
            self.create_structure()

            # Crear archivos
            self.create_readme()
            self.create_template_files()
            self.create_gitignore()

            # Configurar Claude Code
            self.setup_claude()

            # Imprimir resumen
            self.print_summary()

            return True

        except Exception as e:
            print(f"\n❌ ERROR durante setup: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Setup de arquitectura .agents/',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:

  # Proyecto full-stack (default)
  python setup_agents.py

  # Proyecto backend-only
  python setup_agents.py --project-type backend

  # Proyecto frontend-only con Kiro
  python setup_agents.py --project-type frontend --with-kiro

  # Proyecto de data science
  python setup_agents.py --project-type data-science

Tipos de proyecto disponibles:
  - fullstack (default)
  - backend
  - frontend
  - data-science
        """
    )

    parser.add_argument(
        '--project-type',
        choices=['fullstack', 'backend', 'frontend', 'data-science'],
        default='fullstack',
        help='Tipo de proyecto (default: fullstack)'
    )

    parser.add_argument(
        '--with-kiro',
        action='store_true',
        help='Incluir integración con Kiro'
    )

    args = parser.parse_args()

    # Ejecutar setup
    setup = AgentsSetup(
        project_type=args.project_type,
        with_kiro=args.with_kiro
    )

    success = setup.run()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
