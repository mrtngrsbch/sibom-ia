#!/usr/bin/env python3
"""
Commit Agent - Genera mensajes de commit y alerta sobre cambios pendientes

Uso:
    commit-agent analyze [--debug]
    commit-agent suggest
    commit-agent commit --option {1,2,3}
    commit-agent alerts
    commit-agent stats
    commit-agent monitor [--start|--stop] [--interval MINUTES]
    commit-agent --version
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import json
import re
import os
import time
import signal

# Umbrales de alerta (ajustados para evitar falsos positivos)
THRESHOLDS = {
    'info': {'files': 3, 'lines': 200, 'hours': 2},
    'warning': {'files': 10, 'lines': 1000, 'hours': 6},
    'critical': {'files': 20, 'lines': 2000, 'hours': 12},
    'emergency': {'files': 50, 'lines': 5000, 'hours': 24},
}

# Tipos de commits permitidos
COMMIT_TYPES = ['feat', 'fix', 'docs', 'refactor', 'test', 'chore']

# Scopes permitidos
COMMIT_SCOPES = ['chatbot', 'scraper', 'agents', 'docs', 'ci']

# Directorios y scopes
SCOPE_MAPPING = {
    'chatbot/': 'chatbot',
    'python-cli/': 'scraper',
    '.agents/': 'agents',
}

# Archivos de documentación
DOC_FILES = ['*.md', 'README*', '*.rst']


class CommitAgent:
    """Agente para análisis y generación de commits"""
    
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path.cwd()
        
        self.repo_root = repo_root
        self.config = THRESHOLDS  # Usamos umbrales por defecto
        self.log_dir = self.repo_root / '.agents' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivos de logs
        self.alerts_log = self.log_dir / 'commit-alerts.log'
        self.monitor_log = self.log_dir / 'commit-monitor.log'
        
    def _run_git_command(self, cmd: List[str]) -> str:
        """Ejecuta un comando de git y retorna el output"""
        try:
            result = subprocess.run(
                ['git'] + cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # Timeout de 30s para evitar hangs
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout ejecutando: {' '.join(cmd)}")
            return ""
        except subprocess.CalledProcessError as e:
            # Algunos comandos pueden fallar (ej: diff cuando no hay cambios)
            return ""
    
    def get_git_status(self) -> List[str]:
        """Obtiene lista de archivos modificados (git status --short)"""
        try:
            output = self._run_git_command(['status', '--short'])
            return [line.strip() for line in output.split('\n') if line.strip()]
        except Exception:
            return []
    
    def get_staged_diff(self) -> str:
        """Obtiene diff de archivos staged"""
        try:
            return self._run_git_command(['diff', '--cached', '--stat'])
        except Exception:
            return ""
    
    def get_unstaged_diff(self) -> str:
        """Obtiene diff de archivos unstaged"""
        try:
            return self._run_git_command(['diff', '--stat'])
        except Exception:
            return ""
    
    def get_last_commit_time(self) -> Optional[datetime]:
        """Obtiene timestamp del último commit"""
        try:
            output = self._run_git_command(['log', '-1', '--format=%ct'])
            if output.strip():
                timestamp = int(output.strip())
                return datetime.fromtimestamp(timestamp)
        except (subprocess.CalledProcessError, ValueError):
            pass
        return None
    
    def parse_git_status(self, status_lines: List[str]) -> Dict[str, List[Dict]]:
        """Parsea git status y retorna estructura detallada"""
        files = {
            'staged': [],
            'unstaged': [],
            'untracked': []
        }
        
        for line in status_lines:
            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue
            
            status_char = parts[0][0] if len(parts[0]) > 0 else ''
            filepath = parts[1]
            
            file_info = {
                'status': status_char,
                'path': filepath
            }
            
            if status_char in 'MADRC':
                files['staged'].append(file_info)
            elif status_char in ' MADRC':
                files['unstaged'].append(file_info)
            elif status_char == '?':
                files['untracked'].append(file_info)
        
        return files
    
    def categorize_file(self, filepath: str) -> str:
        """Categoriza un archivo por scope"""
        filepath = str(filepath)
        
        # Check scope mapping
        for dir_path, scope in SCOPE_MAPPING.items():
            if filepath.startswith(dir_path):
                return scope
        
        # Check documentation
        for pattern in DOC_FILES:
            if Path(filepath).match(pattern):
                return 'docs'
        
        # Check CI/CD
        if '.github/' in filepath or '.husky/' in filepath:
            return 'ci'
        
        return None
    
    def categorize_changes(self, files: List[Dict]) -> Dict[str, List[str]]:
        """Categoriza archivos por módulo"""
        categorized = {scope: [] for scope in COMMIT_SCOPES + [None]}
        
        for file_info in files:
            scope = self.categorize_file(file_info['path'])
            categorized[scope].append(file_info['path'])
        
        # Remove empty entries
        return {k: v for k, v in categorized.items() if v}
    
    def count_lines(self, files: List[Dict]) -> Tuple[int, int]:
        """Cuenta líneas añadidas y eliminadas"""
        added = 0
        deleted = 0
        
        for file_info in files:
            filepath = file_info['path']
            full_path = self.repo_root / filepath
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                    added += lines  # Simplificado
            except Exception as e:
                print(f"⚠️  No se pudo leer {filepath}: {e}")
        
        return added, deleted
    
    def check_thresholds(self, num_files: int, num_lines: int, hours_since_commit: float) -> Tuple[str, str]:
        """Verifica umbrales de alerta y retorna (nivel, mensaje)"""
        
        # Check emergency
        if (num_files >= THRESHOLDS['emergency']['files'] or
            num_lines >= THRESHOLDS['emergency']['lines'] or
            hours_since_commit >= THRESHOLDS['emergency']['hours']):
            return 'EMERGENCY', "🚨 ¡EMERGENCY! Demasiados cambios acumulados"
        
        # Check critical
        if (num_files >= THRESHOLDS['critical']['files'] or
            num_lines >= THRESHOLDS['critical']['lines'] or
            hours_since_commit >= THRESHOLDS['critical']['hours']):
            return 'CRITICAL', "🔴 ¡CRITICAL! Muchos cambios acumulados"
        
        # Check warning
        if (num_files >= THRESHOLDS['warning']['files'] or
            num_lines >= THRESHOLDS['warning']['lines'] or
            hours_since_commit >= THRESHOLDS['warning']['hours']):
            return 'WARNING', "⚠️  ¡WARNING! Considerá hacer un commit"
        
        if num_files >= THRESHOLDS['info']['files']:
            return 'INFO', "ℹ️  Hay cambios pendientes"
        
        return 'OK', "✅ Pocos cambios"
    
    def generate_commit_messages(self, changes: Dict, num_files: int, hours_since_commit: float) -> List[Dict]:
        """Genera 3 opciones de mensajes de commit"""
        
        # Determinar scope principal
        primary_scope = self._get_primary_scope(changes)
        
        # Determinar tipo de commit
        commit_type = self._determine_commit_type(changes, num_files, hours_since_commit)
        
        # Generar 3 opciones
        options = []
        
        # Opción 1: General
        options.append(self._generate_message_option(
            1, commit_type, primary_scope, changes, 'general'
        ))
        
        # Opción 2: Técnica
        options.append(self._generate_message_option(
            2, commit_type, primary_scope, changes, 'technical'
        ))
        
        # Opción 3: Alternativa
        options.append(self._generate_message_option(
            3, commit_type, primary_scope, changes, 'alternative'
        ))
        
        return options
    
    def _get_primary_scope(self, changes: Dict) -> Optional[str]:
        """Determina el scope principal basado en cambios"""
        if not changes:
            return None
        
        # Encontrar scope con más archivos
        max_count = 0
        primary_scope = None
        
        for scope, files in changes.items():
            if scope and len(files) > max_count:
                max_count = len(files)
                primary_scope = scope
        
        return primary_scope
    
    def _determine_commit_type(self, changes: Dict, num_files: int, hours_since_commit: float) -> str:
        """Determina el tipo de commit basado en cambios"""
        # Lógica simplificada - podría mejorarse con LLM
        changes_str = str(changes).lower()
        
        if 'test' in changes_str or 'tests/' in changes_str:
            return 'test'
        elif 'fix' in changes_str or 'bug' in changes_str or 'error' in changes_str:
            return 'fix'
        elif 'refactor' in changes_str:
            return 'refactor'
        elif 'readme' in changes_str or '.md' in changes_str:
            return 'docs'
        elif num_files > 10 or hours_since_commit > 8:
            return 'refactor'  # Cambios grandes suelen ser refactor
        else:
            return 'feat'  # Default
    
    def _generate_message_option(self, option_num: int, commit_type: str, scope: Optional[str], 
                                  changes: Dict, style: str) -> Dict:
        """Genera una opción de mensaje de commit"""
        
        scope_str = f"({scope})" if scope else ""
        
        # Generar subject
        if style == 'general':
            subject = f"{commit_type}{scope_str}: update files in {scope or 'multiple modules'}"
        elif style == 'technical':
            subject = f"{commit_type}{scope_str}: improve implementation in {scope or 'various modules'}"
        else:  # alternative
            subject = f"{commit_type}{scope_str}: enhance {scope or 'project'} functionality"
        
        # Generar body
        body_items = []
        for scope_name, files in changes.items():
            if scope_name and files:
                body_items.append(f"- Update {len(files)} file(s) in {scope_name}")
        
        body = "\n".join(body_items) if body_items else ""
        
        return {
            'option': option_num,
            'type': commit_type,
            'scope': scope,
            'subject': subject,
            'body': body
        }
    
    def write_alert(self, level: str, message: str, changes: Dict, stats: Dict):
        """Escribe alerta en log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        alert_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'stats': stats,
            'changes': changes
        }
        
        try:
            with open(self.alerts_log, 'a', encoding='utf-8') as f:
                f.write(f"\n[{timestamp}] {level} - {message}\n")
                f.write(f"  Stats: {stats}\n")
                f.write(f"  Files: {len(changes.get('staged', [])) + len(changes.get('unstaged', []))}\n")
        except Exception as e:
            print(f"⚠️  No se pudo escribir alerta: {e}")
    
    def send_notification(self, level: str, message: str, stats: Dict):
        """Envía notificación nativa de macOS"""
        try:
            total_files = stats.get('total_files', 0)
            time_str = stats.get('time_str', 'N/A')
            
            # Usar display notification en lugar de display dialog (no requiere interacción)
            if level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
                # Notificación con comando accionable
                command = 'python3 .agents/scripts/commit_agent.py suggest'
                script = f'''
                tell application "System Events"
                    display notification "{message} ({total_files} files, {time_str} ago)" with title "Commit Agent" sound name "Basso"
                end tell
                '''
                subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
            else:
                # Notificación simple para INFO
                script = f'''
                tell application "System Events"
                    display notification "{message}" with title "Commit Agent"
                end tell
                '''
                subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
                
            print(f"🔔 Notificación enviada: {message} ({total_files} files)")
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  Notificación timeout (continuando normalmente)")
        except Exception as e:
            print(f"⚠️  No se pudo enviar notificación: {e}")
    
    def analyze(self, debug: bool = False) -> Dict:
        """Analiza cambios actuales y retorna resultado"""
        
        if debug:
            print("[DEBUG] Iniciando análisis...")
        
        # Obtener cambios
        status_lines = self.get_git_status()
        parsed_files = self.parse_git_status(status_lines)
        
        # Contar archivos
        total_files = len(parsed_files['staged']) + len(parsed_files['unstaged'])
        
        # Contar líneas (simplificado)
        lines_added, lines_deleted = self.count_lines(parsed_files['staged'] + parsed_files['unstaged'])
        
        # Tiempo desde último commit
        last_commit_time = self.get_last_commit_time()
        if last_commit_time:
            time_diff = datetime.now() - last_commit_time
            hours_since_commit = time_diff.total_seconds() / 3600
            time_str = self._format_time_diff(time_diff)
        else:
            hours_since_commit = float('inf')
            time_str = "nunca"
        
        # Categorizar cambios
        categorized = self.categorize_changes(parsed_files['staged'] + parsed_files['unstaged'])
        
        # Verificar umbrales
        level, alert_message = self.check_thresholds(total_files, lines_added, hours_since_commit)
        
        # Estadísticas
        stats = {
            'total_files': total_files,
            'lines_added': lines_added,
            'lines_deleted': lines_deleted,
            'hours_since_commit': hours_since_commit,
            'time_str': time_str,
            'directories': list(categorized.keys())
        }
        
        result = {
            'level': level,
            'message': alert_message,
            'stats': stats,
            'changes': parsed_files,
            'categorized': categorized
        }
        
        # Escribir alerta si es WARNING o superior
        if level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
            self.write_alert(level, alert_message, parsed_files, stats)
            self.send_notification(level, alert_message, stats)
        
        return result
    
    def _format_time_diff(self, time_diff: timedelta) -> str:
        """Formatea diferencia de tiempo para humano"""
        total_seconds = int(time_diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def suggest(self) -> List[Dict]:
        """Genera 3 sugerencias de mensajes de commit"""
        
        analysis = self.analyze()
        
        num_files = analysis['stats']['total_files']
        hours_since_commit = analysis['stats']['hours_since_commit']
        changes = analysis['categorized']
        
        return self.generate_commit_messages(changes, num_files, hours_since_commit)
    
    def monitor_loop(self, interval_minutes: int = 30):
        """Loop principal de monitoreo"""
        
        print(f"🔍 Iniciando monitor de commits (PID: {os.getpid()})")
        print(f"✅ Intervalo: {interval_minutes} minutos")
        print(f"✅ Logs: {self.monitor_log}")
        print(f"\nUsá Ctrl+C para detener")
        print("=" * 40)
        
        # Crear archivo de PID
        pid_file = self.log_dir / 'commit-monitor.pid'
        try:
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"⚠️  No se pudo crear archivo de PID: {e}")
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificando cambios...")
                
                # Analizar cambios
                analysis = self.analyze()
                
                # Log
                try:
                    with open(self.monitor_log, 'a', encoding='utf-8') as f:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        f.write(f"\n[{timestamp}] Check completado\n")
                        f.write(f"  Nivel: {analysis['level']}\n")
                        f.write(f"  Archivos: {analysis['stats']['total_files']}\n")
                        f.write(f"  Tiempo: {analysis['stats']['time_str']}\n")
                except Exception as e:
                    print(f"⚠️  No se pudo escribir en log: {e}")
                
                # Si hay WARNING o superior, ya se envió notificación en analyze()
                
                # Esperar
                print(f"⏰ Próxima verificación en {interval_minutes} minutos...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n✅ Monitor detenido por el usuario")
        finally:
            # Limpiar archivo de PID
            if pid_file.exists():
                try:
                    pid_file.unlink()
                except Exception:
                    pass
    
    def stop_monitor(self):
        """Detiene el monitor"""
        pid_file = self.log_dir / 'commit-monitor.pid'
        
        if not pid_file.exists():
            print("❌ Monitor no está corriendo")
            return False
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            pid_file.unlink()
            print(f"✅ Monitor detenido (PID: {pid})")
            return True
        except Exception as e:
            print(f"❌ Error deteniendo monitor: {e}")
            return False


def print_analysis_result(analysis: Dict):
    """Imprime resultado de análisis de forma legible"""
    
    level = analysis['level']
    message = analysis['message']
    stats = analysis['stats']
    changes = analysis['changes']
    categorized = analysis['categorized']
    
    # Header
    print(f"\n{message}")
    if level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
        print("=" * (len(message)))
    
    # Stats
    print(f"\n📊 Estadísticas:")
    print(f"  Archivos: {stats['total_files']}")
    print(f"  Líneas: +{stats['lines_added']}, -{stats['lines_deleted']}")
    print(f"  Tiempo desde último commit: {stats['time_str']}")
    
    # Categorías
    if categorized:
        print(f"\n🎯 Cambios por módulo:")
        for scope, files in categorized.items():
            print(f"  • {scope or 'general':12} ({len(files):2} archivos)")
    
    # Archivos detallados
    if level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
        print(f"\n📁 Archivos modificados:")
        for file_info in changes['staged'] + changes['unstaged']:
            status_icon = '✓' if file_info in changes['staged'] else '•'
            print(f"  {status_icon} {file_info['path']}")
    
    # Sugerencias accionables
    if level in ['WARNING', 'CRITICAL', 'EMERGENCY']:
        print(f"\n💡 ¿Qué hacer?")
        print(f"   1. Ver opciones de commit:")
        print(f"      python3 .agents/scripts/commit_agent.py suggest")
        print(f"")
        print(f"   2. O commitear manualmente con el mensaje que quieras:")
        print(f"      git add <archivos>")
        print(f"      git commit -m 'tipo(scope): descripción'")
        print(f"")
        print(f"   3. Ver ayuda del formato:")
        print(f"      cat .agents/steering/git-workflow.md")
        print(f"")
        print(f"   Ejemplo de commit correcto:")
        print(f"      git commit -m 'feat(scraper): add arg parser for cities'")


def print_commit_suggestions(options: List[Dict]):
    """Imprime las 3 sugerencias de commit"""
    
    print(f"\n📋 Opciones de mensajes de commit:\n")
    
    for option in options:
        print(f"{option['option']}. {option['subject']}")
        if option['body']:
            for line in option['body'].split('\n'):
                print(f"   {line}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Commit Agent - Genera mensajes de commit y alerta sobre cambios pendientes',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analizar cambios actuales')
    analyze_parser.add_argument('--debug', action='store_true', help='Modo debug')
    
    # Comando suggest
    subparsers.add_parser('suggest', help='Generar 3 opciones de mensajes de commit')
    
    # Comando commit
    commit_parser = subparsers.add_parser('commit', help='Commitear cambios con opción específica')
    commit_parser.add_argument('--option', type=int, choices=[1, 2, 3], required=True,
                              help='Opción de mensaje de commit (1, 2, o 3)')
    
    # Comando alerts
    subparsers.add_parser('alerts', help='Ver alertas recientes')
    
    # Comando stats
    subparsers.add_parser('stats', help='Ver estadísticas de commits')
    
    # Comando monitor
    monitor_parser = subparsers.add_parser('monitor', help='Monitorear cambios en background')
    monitor_parser.add_argument('--start', action='store_true', help='Iniciar monitor')
    monitor_parser.add_argument('--stop', action='store_true', help='Detener monitor')
    monitor_parser.add_argument('--interval', type=int, default=30,
                             help='Intervalo en minutos (default: 30)')
    
    # Versión
    parser.add_argument('--version', action='version', version='Commit Agent v1.0.0')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Inicializar agente
    agent = CommitAgent()
    
    # Ejecutar comando
    if args.command == 'analyze':
        analysis = agent.analyze(debug=args.debug)
        print_analysis_result(analysis)
        
        if analysis['level'] in ['WARNING', 'CRITICAL', 'EMERGENCY']:
            print(f"\n💡 Sugerencia: Ejecutá 'commit-agent suggest' para ver opciones de commit")
    
    elif args.command == 'suggest':
        options = agent.suggest()
        print_commit_suggestions(options)
        
        print(f"Seleccioná una opción (1-3) o 'n' para cancelar:")
    
    elif args.command == 'commit':
        # Implementación de commit con opción
        print(f"📝 Commiteando con opción {args.option}...")
        print("⚠️  Esta funcionalidad requiere implementación adicional")
        print("Por ahora, usá el mensaje sugerido con 'git commit -m \"mensaje\"'")
    
    elif args.command == 'alerts':
        if agent.alerts_log.exists():
            print(f"\n📋 Alertas recientes")
            print("=" * 40)
            print(agent.alerts_log.read_text(encoding='utf-8'))
        else:
            print("ℹ️  No hay alertas registradas")
    
    elif args.command == 'stats':
        print("📊 Estadísticas de commits")
        print("=" * 40)
        print("⚠️  Esta funcionalidad requiere implementación adicional")
        print("Por ahora, usá 'git log --stat' para ver estadísticas")
    
    elif args.command == 'monitor':
        if args.stop:
            agent.stop_monitor()
        else:
            agent.monitor_loop(interval_minutes=args.interval)


if __name__ == '__main__':
    main()
