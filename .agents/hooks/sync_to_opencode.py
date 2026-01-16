#!/usr/bin/env python3
"""
Sincroniza definiciones de agentes desde .agents/ a .opencode/

Este script es un BACKUP para cuando OpenCode no soporta auto-reload.
En condiciones normales, OpenCode lee .agents/ automáticamente.

Uso:
    python .agents/hooks/sync_to_opencode.py
    python .agents/hooks/sync_to_opencode.py --dry-run
"""

import json
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Colores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def log_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def log_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def load_agent_definition(agent_file: Path) -> Dict[str, Any]:
    """Carga definición de agente desde YAML"""
    try:
        with open(agent_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log_error(f"Error leyendo {agent_file.name}: {e}")
        return None

def convert_to_opencode_format(agent_def: Dict[str, Any], source_path: str) -> Dict[str, Any]:
    """Convierte definición de agente a formato OpenCode"""
    return {
        "name": agent_def.get("name", "unknown"),
        "source": source_path,
        "runtime": agent_def.get("runtime", {}).get("language", "python"),
        "version": agent_def.get("version", "1.0.0"),
        "tools": agent_def.get("tools", []),
        "autoReload": True,  # Habilitar auto-reload si OpenCode lo soporta
        "metadata": {
            "description": agent_def.get("description", ""),
            "author": agent_def.get("metadata", {}).get("author", "unknown"),
            "tags": agent_def.get("metadata", {}).get("tags", [])
        }
    }

def sync_agents(dry_run: bool = False) -> bool:
    """
    Sincroniza agentes de .agents/ a .opencode/
    
    Returns:
        True si la sincronización fue exitosa
    """
    log_info("Iniciando sincronización .agents/ → .opencode/")
    
    # Rutas
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / ".agents" / "agents"
    opencode_dir = project_root / ".opencode"
    opencode_config = opencode_dir / "agents.json"
    
    # Verificar que .agents/agents/ existe
    if not agents_dir.exists():
        log_error(f"Directorio {agents_dir} no existe")
        return False
    
    # Crear .opencode/ si no existe
    if not opencode_dir.exists():
        if dry_run:
            log_info(f"[DRY-RUN] Crearía directorio {opencode_dir}")
        else:
            opencode_dir.mkdir(parents=True, exist_ok=True)
            log_success(f"Creado directorio {opencode_dir}")
    
    # Leer todos los agentes de .agents/agents/
    agent_files = list(agents_dir.glob("*.yaml")) + list(agents_dir.glob("*.yml"))
    
    # Filtrar README.md
    agent_files = [f for f in agent_files if f.stem.lower() != "readme"]
    
    if not agent_files:
        log_warning("No se encontraron archivos de agentes en .agents/agents/")
        return True
    
    log_info(f"Encontrados {len(agent_files)} agentes")
    
    # Procesar cada agente
    agents_config = []
    for agent_file in agent_files:
        log_info(f"Procesando {agent_file.name}...")
        
        agent_def = load_agent_definition(agent_file)
        if not agent_def:
            continue
        
        # Convertir a formato OpenCode
        source_path = f"../.agents/agents/{agent_file.name}"
        opencode_agent = convert_to_opencode_format(agent_def, source_path)
        agents_config.append(opencode_agent)
        
        log_success(f"  ✓ {agent_def.get('name', 'unknown')} v{agent_def.get('version', '1.0.0')}")
    
    # Crear configuración final
    final_config = {
        "agents": agents_config,
        "metadata": {
            "syncedAt": datetime.utcnow().isoformat() + "Z",
            "syncedFrom": ".agents/agents/",
            "totalAgents": len(agents_config)
        }
    }
    
    # Escribir a .opencode/agents.json
    if dry_run:
        log_info("[DRY-RUN] Configuración que se escribiría:")
        print(json.dumps(final_config, indent=2))
    else:
        try:
            with open(opencode_config, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, indent=2, ensure_ascii=False)
            log_success(f"Escrito {opencode_config}")
        except Exception as e:
            log_error(f"Error escribiendo {opencode_config}: {e}")
            return False
    
    # Resumen
    print()
    log_success(f"Sincronizados {len(agents_config)} agentes a .opencode/")
    
    if not dry_run:
        log_info("OpenCode detectará los cambios automáticamente")
        log_info("Si no, reinicia OpenCode o ejecuta: opencode reload")
    
    return True

def main():
    """Punto de entrada principal"""
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if dry_run:
        log_warning("Modo DRY-RUN: no se escribirán archivos")
        print()
    
    success = sync_agents(dry_run=dry_run)
    
    if not success:
        log_error("Sincronización falló")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
