#!/usr/bin/env python3
"""
Propaga .agents/ → .kiro/

Agrega secciones "Agent AI Requirements" a los archivos de .kiro/
basado en las reglas específicas definidas en .agents/.

Uso:
    python .agents/hooks/propagate_to_kiro.py
"""

from pathlib import Path
from datetime import datetime

class AgentsToKiroPropagate:
    """Propaga reglas de .agents/ hacia .kiro/"""

    def __init__(self):
        self.root = Path.cwd()
        self.agents_dir = self.root / '.agents'
        self.kiro_dir = self.root / '.kiro'
        self.valid = False

        # Verificar que ambos directorios existen
        if not self.agents_dir.exists():
            print("❌ ERROR: .agents/ no existe")
            self.valid = False
        elif not self.kiro_dir.exists():
            print("❌ ERROR: .kiro/ no existe")
            print("   Ejecuta primero: python .agents/hooks/sync_from_kiro.py")
            self.valid = False
        else:
            self.valid = True

    def propagate_steering(self):
        """Propaga reglas de .agents/steering/ hacia .kiro/steering/"""
        print("\n🔄 Propagando steering...")

        agents_steering = self.agents_dir / 'steering'
        kiro_steering = self.kiro_dir / 'steering'

        # Archivos específicos de agentes (NO se propagan)
        agent_specific = [
            'claude-specific-rules.md',
            'droid-specific-rules.md',
            'cursor-specific-rules.md',
        ]

        # Buscar archivos de steering en .agents/
        agents_files = [f for f in agents_steering.glob('*.md')
                        if f.name not in agent_specific]

        if not agents_files:
            print("⚠️  No hay archivos para propagar")
            return

        propagated_count = 0

        for agents_file in agents_files:
            # Buscar archivo correspondiente en .kiro/
            kiro_file = kiro_steering / agents_file.name

            if not kiro_file.exists():
                print(f"⚠️  No existe .kiro/steering/{agents_file.name}")
                print(f"   Creando nuevo archivo...")

            # Leer contenido de .agents/
            agents_content = agents_file.read_text(encoding='utf-8')

            # Extraer reglas de agentes (secciones creadas por usuario)
            agent_rules = self._extract_agent_rules(agents_content)

            if not agent_rules:
                print(f"⏭️  {agents_file.name}: No hay reglas nuevas para propagar")
                continue

            # Agregar a .kiro/
            self._add_agent_requirements(kiro_file, agent_rules)
            print(f"✅ {agents_file.name}: {len(agent_rules)} reglas propagadas")
            propagated_count += 1

        print(f"\n📊 Reglas propagadas: {propagated_count} archivos")

    def _extract_agent_rules(self, content):
        """Extrae reglas específicas de agentes del contenido"""
        lines = content.split('\n')
        rules = []
        current_rule = []
        in_agent_section = False

        for line in lines:
            # Detectar secciones específicas de agentes
            if line.startswith('## ') and any(keyword in line.lower() for keyword in
                ['claude', 'droid', 'cursor', 'agente ai', 'agent ai']):
                in_agent_section = True

            if in_agent_section and line.strip():
                current_rule.append(line)

            if in_agent_section and line.startswith('## ') and len(current_rule) > 1:
                rules.append('\n'.join(current_rule))
                current_rule = [line]

        return rules

    def _add_agent_requirements(self, kiro_file, agent_rules):
        """Agrega sección de Agent AI Requirements al archivo de Kiro"""
        # Leer contenido actual
        if kiro_file.exists():
            content = kiro_file.read_text(encoding='utf-8')
        else:
            content = f"# {kiro_file.stem}\n\n"

        # Verificar si ya tiene la sección
        if '## Agent AI Requirements' in content:
            # Actualizar sección existente
            parts = content.split('## Agent AI Requirements')
            content = parts[0]  # Mantener todo antes de la sección

        # Agregar nueva sección
        agent_section = f"""

## Agent AI Requirements

Basado en `.agents/steering/{kiro_file.name}`:

Las siguientes reglas fueron agregadas para agentes AI que trabajan en este proyecto:

{''.join(agent_rules)}

---

**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Fuente:** .agents/steering/{kiro_file.name}
"""

        # Escribir contenido actualizado
        kiro_file.write_text(content + agent_section, encoding='utf-8')

    def create_propagation_log(self):
        """Crea log de propagaciones realizadas"""
        log_content = f"""# Log de Propagaciones

Este archivo registra las veces que .agents/ propagó cambios hacia .kiro/

## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Propagación inicial desde .agents/ hacia .kiro/

---

**Formato del log:**
- Fecha y hora de propagación
- Archivos modificados
- Reglas agregadas

Para ver detalles de cada regla, revisar los archivos en .kiro/steering/
"""

        log_file = self.agents_dir / 'PROPAGATION_LOG.md'
        if not log_file.exists():
            log_file.write_text(log_content, encoding='utf-8')
        else:
            existing = log_file.read_text(encoding='utf-8')
            log_file.write_text(existing + f"\n\n## {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nPropagación ejecutada\n", encoding='utf-8')

        print("📝 Log actualizado")

    def run(self):
        """Ejecuta propagación completa"""
        print("=" * 60)
        print("🔄 Propagando .agents/ → .kiro/")
        print("=" * 60)

        if not self.valid:
            return

        try:
            # Propagar steering
            self.propagate_steering()

            # Crear log
            self.create_propagation_log()

            print("\n" + "=" * 60)
            print("✅ Propagación completada con éxito")
            print("=" * 60)
            print(f"\n📊 Resumen:")
            print(f"   - Reglas de .agents/ propagadas a .kiro/")
            print(f"   - Archivos técnicos actualizados")
            print(f"   - Log de propagación creado")
            print(f"\n💡 Próximo paso:")
            print(f"   Ver cambios en: .kiro/steering/")
            print(f"   Ejecutar: git diff .kiro/")

        except Exception as e:
            print(f"\n❌ ERROR durante propagación: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    propagate = AgentsToKiroPropagate()
    propagate.run()
