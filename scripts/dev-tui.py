#!/usr/bin/env python3
"""
SIBOM Dev TUI - Terminal UI para administrar servicios de desarrollo

Servicios:
- Backend: FastAPI (sat-analysis) en puerto 8001
- Frontend: Next.js (chatbot) en puerto 3000
- Docker: docker-compose services

Uso:
    python scripts/dev-tui.py
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

# Agregar rutas al proyecto
PROJECT_ROOT = Path(__file__).parent.parent


class ServiceStatus(Enum):
    """Estados posibles de un servicio"""
    STOPPED = "stopped"
    RUNNING = "running"
    STARTING = "starting"
    ERROR = "error"


@dataclass
class Service:
    """Representa un servicio del sistema"""
    name: str
    description: str
    port: int
    working_dir: Path
    command: str
    log_file: Path
    pid: Optional[int] = None
    status: ServiceStatus = ServiceStatus.STOPPED

    @property
    def status_symbol(self) -> str:
        symbols = {
            ServiceStatus.RUNNING: "🟢",
            ServiceStatus.STOPPED: "🔴",
            ServiceStatus.STARTING: "🟡",
            ServiceStatus.ERROR: "⚠️ ",
        }
        return symbols.get(self.status, "❓")


@dataclass
class DevState:
    """Estado del entorno de desarrollo"""
    backend: Service = field(init=False)
    frontend: Service = field(init=False)
    services: list[Service] = field(init=False)

    def __post_init__(self):
        logs_dir = PROJECT_ROOT / "logs"
        logs_dir.mkdir(exist_ok=True)

        self.backend = Service(
            name="Backend",
            description="FastAPI (sat-analysis)",
            port=8001,
            working_dir=PROJECT_ROOT / "sat-analysis",
            command="python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001",
            log_file=logs_dir / "backend.log"
        )

        self.frontend = Service(
            name="Frontend",
            description="Next.js (chatbot)",
            port=3000,
            working_dir=PROJECT_ROOT / "chatbot",
            command="pnpm run dev",
            log_file=logs_dir / "frontend.log"
        )

        self.services = [self.backend, self.frontend]


class ServiceManager:
    """Gestor de servicios del entorno de desarrollo"""

    def __init__(self, state: DevState):
        self.state = state
        self.started_pids: set[int] = set()  # PIDs iniciados por este script

    def check_port(self, port: int) -> bool:
        """Verifica si un puerto está en uso"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_pid_on_port(self, port: int) -> Optional[int]:
        """Obtiene el PID que está usando un puerto"""
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split()[0])
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass
        return None

    def get_process_command(self, pid: int) -> str:
        """Obtiene el comando de un proceso"""
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return ""

    def update_status(self, service: Service):
        """Actualiza el estado de un servicio"""
        pid = self.get_pid_on_port(service.port)

        if pid:
            cmd = self.get_process_command(pid)
            keywords = self._get_keywords(service.name)
            if any(kw in cmd.lower() for kw in keywords):
                service.status = ServiceStatus.RUNNING
                service.pid = pid
            else:
                service.status = ServiceStatus.ERROR
                service.pid = None
        else:
            service.status = ServiceStatus.STOPPED
            service.pid = None

    def _get_keywords(self, service_name: str) -> list[str]:
        keywords = {
            "Backend": ["uvicorn", "api.main"],
            "Frontend": ["next", "node", "pnpm"],
        }
        return keywords.get(service_name, [])

    def start_service(self, service: Service) -> tuple[bool, str]:
        """Inicia un servicio"""
        if service.status == ServiceStatus.RUNNING:
            return True, "Servicio ya está corriendo"

        if not service.working_dir.exists():
            return False, f"Directorio no encontrado: {service.working_dir}"

        # Verificar dependencias para backend
        if service.name == "Backend":
            venv_dir = service.working_dir / ".venv"
            if not venv_dir.exists():
                return False, "Virtualenv no encontrado. Ejecuta: cd sat-analysis && uv venv .venv"

        # Verificar dependencias para frontend
        if service.name == "Frontend":
            node_modules = service.working_dir / "node_modules"
            if not node_modules.exists():
                return False, "node_modules no encontrado. Ejecuta: cd chatbot && pnpm install"

        try:
            log_file = open(service.log_file, "a")
            process = subprocess.Popen(
                service.command,
                shell=True,
                cwd=service.working_dir,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if hasattr(os, 'setsid') else None
            )

            time.sleep(2)

            if process.poll() is None:
                self.started_pids.add(process.pid)
                service.pid = process.pid
                service.status = ServiceStatus.RUNNING
                return True, f"Servicio iniciado (PID: {process.pid})"
            else:
                return False, "El servicio terminó inmediatamente. Revisa los logs."

        except Exception as e:
            return False, f"Error: {e}"

    def stop_service(self, service: Service) -> tuple[bool, str]:
        """Detiene un servicio solo si fue iniciado por este script"""
        if service.status == ServiceStatus.STOPPED:
            return True, "Servicio ya está detenido"

        if not service.pid:
            service.pid = self.get_pid_on_port(service.port)

        if not service.pid:
            service.status = ServiceStatus.STOPPED
            return True, "Servicio no encontrado"

        # Solo detener si lo iniciamos nosotros o si el usuario confirma
        try:
            if service.pid in self.started_pids:
                os.killpg(os.getpgid(service.pid), signal.SIGTERM)
                self.started_pids.discard(service.pid)
            else:
                # Preguntar antes de matar un proceso externo
                return False, f"Servicio iniciado externamente (PID: {service.pid}). Usá 'kill {service.pid}' para detenerlo."

            time.sleep(1)

            if not self.get_pid_on_port(service.port):
                service.status = ServiceStatus.STOPPED
                service.pid = None
                return True, "Servicio detenido"
            else:
                return False, "No se pudo detener el servicio"

        except ProcessLookupError:
            service.status = ServiceStatus.STOPPED
            service.pid = None
            return True, "Servicio detenido"
        except Exception as e:
            return False, f"Error: {e}"

    def restart_service(self, service: Service) -> tuple[bool, str]:
        """Reinicia un servicio"""
        if service.pid in self.started_pids:
            self.stop_service(service)
            time.sleep(1)
        return self.start_service(service)

    def get_logs(self, service: Service, lines: int = 30) -> str:
        """Obtiene las últimas líneas del log"""
        if not service.log_file.exists():
            return "Archivo de log no encontrado"

        try:
            result = subprocess.run(
                ["tail", "-n", str(lines), str(service.log_file)],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout
        except Exception:
            return "Error al leer logs"

    def refresh_all(self):
        """Actualiza el estado de todos los servicios"""
        for service in self.state.services:
            self.update_status(service)


class DevTUI:
    """Terminal UI para administración de servicios"""

    def __init__(self):
        self.state = DevState()
        self.manager = ServiceManager(self.state)
        self.running = True

    def clear_screen(self):
        """Limpia la pantalla de forma segura"""
        print("\033[2J\033[H", end="", flush=True)

    def print_header(self):
        """Imprime el encabezado"""
        print("\n" + "=" * 65)
        print("  🚀 SIBOM Dev TUI - Entorno de Desarrollo")
        print("=" * 65)

    def print_services(self):
        """Imprime el estado de los servicios"""
        print("\n  Servicios:")
        print("  " + "-" * 60)

        for i, service in enumerate(self.state.services, 1):
            pid_text = f"PID: {service.pid}" if service.pid else "PID: -"
            print(f"\n  [{i}] {service.status_symbol} {service.name}")
            print(f"      {service.description}")
            print(
                f"      Estado: {service.status.value.upper():<8} | {pid_text} | Puerto: {service.port}")

    def print_menu(self):
        """Imprime el menú"""
        print("\n  " + "-" * 60)
        print("  Comandos:")
        print("    [1-2] Iniciar/Detener servicio  [l] Ver logs")
        print(
            "    [a]   Iniciar todos             [q] Salir (detener los iniciados)")
        print("    [x]   Salir (sin detener)       [r] Refrescar")
        print("  " + "-" * 60)

    def refresh(self):
        """Refresca la pantalla"""
        self.clear_screen()
        self.print_header()
        self.manager.refresh_all()
        self.print_services()
        self.print_menu()
        print(f"\n  Última actualización: {time.strftime('%H:%M:%S')}")

    def get_service_choice(self) -> Optional[Service]:
        """Permite seleccionar un servicio"""
        while True:
            choice = input(
                "\n  Número de servicio (o Enter para cancelar): ").strip()

            if not choice:
                return None

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.state.services):
                    return self.state.services[idx]
            except ValueError:
                pass

            print("  ❌ Opción inválida")

    def toggle_service(self, service: Service):
        """Alterna entre iniciar/detener un servicio"""
        if service.status == ServiceStatus.RUNNING:
            success, msg = self.manager.stop_service(service)
        else:
            success, msg = self.manager.start_service(service)

        print(f"\n  {'✅' if success else '❌'} {msg}")
        time.sleep(1)

    def view_logs(self, service: Optional[Service] = None):
        """Muestra los logs de un servicio"""
        if service is None:
            service = self.get_service_choice()

        if service is None:
            return

        self.clear_screen()
        print(f"\n  📄 Logs de {service.name} ({service.log_file})")
        print("  " + "-" * 60)
        print("  Presiona Ctrl+C para volver\n")

        logs = self.manager.get_logs(service, lines=50)
        if logs:
            # Mostrar logs con páginas
            lines_list = logs.split('\n')
            page_size = 20
            current_page = 0

            while current_page * page_size < len(lines_list):
                self.clear_screen()
                print(
                    f"\n  📄 Logs de {service.name} - Página {current_page + 1}")
                print("  " + "-" * 60)

                start = current_page * page_size
                end = start + page_size
                for line in lines_list[start:end]:
                    print(f"  {line}")

                print("\n  [n] Siguiente | [p] Anterior | [q] Volver")

                choice = input("\n  Opción: ").strip().lower()
                if choice == 'n':
                    current_page += 1
                elif choice == 'p' and current_page > 0:
                    current_page -= 1
                elif choice == 'q':
                    break
        else:
            print("  No hay logs disponibles")
            time.sleep(1)

    def start_all(self):
        """Inicia todos los servicios"""
        print("\n  Iniciando todos los servicios...")
        for service in self.state.services:
            if service.status != ServiceStatus.RUNNING:
                print(f"\n  ▶️  {service.name}...")
                success, msg = self.manager.start_service(service)
                print(f"      {'✅' if success else '❌'} {msg}")
                time.sleep(0.5)
        input("\n  Presiona Enter para continuar...")

    def quit(self, stop_all: bool = True):
        """Sale de la TUI"""
        if stop_all:
            print("\n  Deteniendo servicios iniciados por esta sesión...")
            stopped = 0
            for service in self.state.services:
                if service.pid in self.manager.started_pids:
                    success, msg = self.manager.stop_service(service)
                    if success:
                        stopped += 1

            if stopped > 0:
                print(f"\n  ✅ {stopped} servicio(s) detenido(s)")
            else:
                print("\n  ℹ️  No se detuvo ningún servicio (corriendo externamente)")

        self.running = False

    def run(self):
        """Ejecuta el loop principal"""
        try:
            while self.running:
                self.refresh()

                try:
                    choice = input("\n  Comando: ").strip().lower()
                except EOFError:
                    break

                if choice in ['q', 'quit', 'exit']:
                    self.quit(stop_all=True)

                elif choice in ['x', 'x']:
                    self.quit(stop_all=False)

                elif choice in ['1', '2']:
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.state.services):
                        self.toggle_service(self.state.services[idx])

                elif choice == 'a':
                    self.start_all()

                elif choice == 'l':
                    self.view_logs()

                elif choice == 'r':
                    pass  # Refrescar ocurre en cada loop

                else:
                    print("\n  ❌ Comando no reconocido")
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n  👋 ¡Hasta luego!")
            # Opcional: detener servicios al hacer Ctrl+C
            # self.quit(stop_all=True)

        finally:
            print("\n")


def main():
    """Función principal"""
    tui = DevTUI()
    tui.run()


if __name__ == "__main__":
    main()
