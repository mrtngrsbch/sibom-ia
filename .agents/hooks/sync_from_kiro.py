#!/usr/bin/env python3
"""
Sincroniza .kiro/ → .agents/

Genera .agents/specs/ como referencias a la documentación técnica completa.
Copia steering/ de .kiro/ a .agents/ (como base editable).

Uso:
    python .agents/hooks/sync_from_kiro.py
"""

import json
from pathlib import Path
from datetime import datetime

class KiroToAgentsSync:
    """Sincroniza documentación de Kiro hacia .agents/"""

    def __init__(self):
        self.root = Path.cwd()
        self.kiro_dir = self.root / '.kiro'
        self.agents_dir = self.root / '.agents'
        self.valid = False

        # Verificar que .kiro/ existe
        if not self.kiro_dir.exists():
            print("❌ ERROR: .kiro/ no existe")
            print("   Ejecuta Kiro primero para generar análisis")
            self.valid = False
        else:
            self.valid = True

    def sync_specs(self):
        """Genera .agents/specs/ como referencias a .kiro/"""
        print("\n🔄 Sincronizando specs...")

        kiro_specs = self.kiro_dir / 'specs'
        agents_specs = self.agents_dir / 'specs'
        agents_specs.mkdir(parents=True, exist_ok=True)

        # Mapeo de archivos de specs
        spec_mappings = [
            ('01-proyecto-overview.md', '01-proyecto-overview.md'),
            ('02-backend-scraper.md', '02-backend-architecture.md'),
            ('03-frontend-chatbot.md', '03-frontend-architecture.md'),
            ('04-integracion.md', '04-integracion.md'),
            ('05-data-pipeline.md', '05-data-pipeline.md'),
            ('06-llm-integration.md', '06-llm-integration.md'),
        ]

        for kiro_file, agents_file in spec_mappings:
            kiro_path = kiro_specs / kiro_file
            agents_path = agents_specs / agents_file

            if not kiro_path.exists():
                print(f"⚠️  No existe: {kiro_file}")
                continue

            # Crear archivo de referencia
            self._create_spec_reference(kiro_path, agents_path)
            print(f"✅ {agents_file}")

        print(f"📊 Specs sincronizadas: {len(spec_mappings)} archivos")

    def _create_spec_reference(self, kiro_path, agents_path):
        """Crea un archivo de referencia en .agents/specs/"""

        # Leer título y resumen del archivo de Kiro
        content = kiro_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Extraer título
        title = kiro_path.stem.replace('-', ' ').replace('_', ' ').title()

        # Extraer primeras secciones importantes
        summary_lines = []
        in_summary = False
        for i, line in enumerate(lines):
            if line.startswith('## '):
                in_summary = True
            if in_summary and line.strip():
                summary_lines.append(line)
            if len(summary_lines) > 20:  # Máximo 20 líneas de resumen
                break

        summary = '\n'.join(summary_lines[:15])  # Primeras 15 líneas

        # Crear contenido de referencia
        reference_content = f"""# {title}

## ⚠️ ARCHIVO AUTO-GENERADO

**Este archivo es una REFERENCIA a la documentación técnica completa.**

NO EDITAR ESTE ARCHIVO DIRECTAMENTE.

Para cambios, editar: `{kiro_path.relative_to(self.root)}`

Luego ejecutar: `python .agents/hooks/sync_from_kiro.py`

---

## 📋 Resumen

{summary}


## 🔗 Documentación Técnica Completa

**Ver archivo completo:** `{kiro_path.relative_to(self.root)}`

**Ubicación:** `.kiro/specs/{kiro_path.name}`

**Contenido detallado:**
- Análisis técnico profundo
- Ejemplos de código real
- Diagramas y arquitectura
- Patrones y decisiones de diseño


## 🤖 Para Agentes AI

Cuando trabajéis en este proyecto:

1. **LEER** el archivo completo en `.kiro/` para entender el contexto
2. **APLICAR** patrones de `.agents/steering/`
3. **CONSULTAR** este archivo solo como referencia rápida

---

**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Fuente:** Análisis de Kiro
"""

        # Escribir archivo
        agents_path.write_text(reference_content, encoding='utf-8')

    def sync_steering(self):
        """Copia steering/ de .kiro/ como base editable"""
        print("\n🔄 Sincronizando steering...")

        kiro_steering = self.kiro_dir / 'steering'
        agents_steering = self.agents_dir / 'steering'
        agents_steering.mkdir(parents=True, exist_ok=True)

        if not kiro_steering.exists():
            print(f"⚠️  No existe: .kiro/steering/")
            return

        # Copiar archivos de steering
        steering_files = list(kiro_steering.glob('*.md'))
        if not steering_files:
            print(f"⚠️  No hay archivos .md en .kiro/steering/")
            return

        for kiro_file in steering_files:
            agents_file = agents_steering / kiro_file.name

            # Leer contenido de Kiro
            content = kiro_file.read_text(encoding='utf-8')

            # Agregar header para .agents/
            header = f"""# {kiro_file.stem}

## ⚠️ BASE EDITABLE

Este archivo fue copiado desde: `.kiro/steering/{kiro_file.name}`

**Puedes EDITAR este archivo** para agregar reglas específicas para agentes AI.

Para regenerar desde .kiro/:
```bash
python .agents/hooks/sync_from_kiro.py
```

---

"""

            # Escribir con header
            agents_file.write_text(header + content, encoding='utf-8')
            print(f"✅ {kiro_file.name}")

        print(f"📊 Steering sincronizado: {len(steering_files)} archivos")

    def sync_hooks(self):
        """Copia hooks/ de .kiro/ si existen"""
        print("\n🔄 Sincronizando hooks...")

        kiro_hooks = self.kiro_dir / 'hooks'
        agents_hooks = self.agents_dir / 'hooks'
        agents_hooks.mkdir(parents=True, exist_ok=True)

        if not kiro_hooks.exists():
            print(f"⚠️  No existe: .kiro/hooks/")
            return

        # Copiar hooks de Kiro
        hook_files = list(kiro_hooks.glob('*.md'))
        if not hook_files:
            print(f"⚠️  No hay archivos .md en .kiro/hooks/")
            return

        for kiro_file in hook_files:
            agents_file = agents_hooks / kiro_file.name

            # Copiar tal cual
            content = kiro_file.read_text(encoding='utf-8')
            agents_file.write_text(content, encoding='utf-8')
            print(f"✅ {kiro_file.name}")

        print(f"📊 Hooks sincronizados: {len(hook_files)} archivos")

    def create_index(self):
        """Crea índice en .agents/"""
        print("\n📝 Creando índice...")

        readme_content = """# .agents/ - Arquitectura de Agentes AI

Esta carpeta contiene la arquitectura de proyecto agnóstica a herramientas.

## Estructura

```
.agents/
├── specs/           ← Referencias a .kiro/specs/ (READ-ONLY)
├── steering/        ← Reglas para agentes AI (EDITABLE)
├── hooks/           ← Scripts de sincronización
└── workflows/       ← Procedimientos multi-paso
```

## Fuentes de Verdad

- **`.kiro/`**: Documentación técnica completa (análisis de Kiro)
- **`.agents/`**: Reglas operativas para agentes AI

## Sincronización

```bash
# Después de que Kiro analice el proyecto
python .agents/hooks/sync_from_kiro.py

# Para agregar reglas específicas para agentes
# 1. Editar .agents/steering/
# 2. Ejecutar: python .agents/hooks/propagate_to_kiro.py
```

## Documentación

- **[Guía Completa](GUIA_COMPLETA.md)** - Manual completo del sistema
- **[Plan de Coexistencia](PLAN_COEXISTENCIA.md)** - Estrategia de arquitectura
- **[Análisis de Sincronización](ANALISIS_SINCRONIZACION.md)** - Detalles técnicos

---

**Última sincronización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        (self.agents_dir / 'README.md').write_text(readme_content, encoding='utf-8')
        print("✅ README.md creado en .agents/")

    def run(self):
        """Ejecuta sincronización completa"""
        print("=" * 60)
        print("🔄 Sincronizando .kiro/ → .agents/")
        print("=" * 60)

        if not self.valid:
            return

        try:
            # Sincronizar cada sección
            self.sync_specs()
            self.sync_steering()
            self.sync_hooks()
            self.create_index()

            print("\n" + "=" * 60)
            print("✅ Sincronización completada con éxito")
            print("=" * 60)
            print(f"\n📊 Resumen:")
            print(f"   - Specs generadas como referencias")
            print(f"   - Steering copiado como base editable")
            print(f"   - Hooks sincronizados")
            print(f"   - README actualizado")
            print(f"\n💡 Próximo paso:")
            print(f"   Editar .agents/steering/ para agregar reglas específicas")
            print(f"   Ver: .agents/GUIA_COMPLETA.md para más información")

        except Exception as e:
            print(f"\n❌ ERROR durante sincronización: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    sync = KiroToAgentsSync()
    sync.run()
