#!/usr/bin/env python3
"""
Script simple para ejecutar refactoring con GLM-4.7.
Solo copia el prompt y lo envía a la API.
"""

import os
import sys
from pathlib import Path

def load_api_key():
    """
    Carga API key desde .env (busca en múltiples ubicaciones).
    Procesa en orden: 1) .env en carpeta refactor/, 2) .env en raíz, 3) variable de entorno
    """
    try:
        from dotenv import load_dotenv
        
        # Intentar cargar desde .env en la carpeta refactor/
        base_dir = Path(__file__).parent
        env_file_refactor = base_dir / ".env"
        env_file_root = base_dir.parent / ".env"
        
        if env_file_refactor.exists():
            load_dotenv(env_file_refactor)
        elif env_file_root.exists():
            load_dotenv(env_file_root)
        else:
            load_dotenv()  # Busca en cwd
            
    except ImportError:
        pass
    
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: No se encontró API key")
        print("Crea un archivo .env en una de estas ubicaciones:")
        print(f"  1. {Path(__file__).parent / '.env'} (preferido)")
        print(f"  2. {Path(__file__).parent.parent / '.env'}")
        sys.exit(1)
    
    return api_key

def send_to_glm(prompt: str, api_key: str, base_dir: Path) -> str:
    """
    Envía prompt a GLM-4.7 y muestra respuesta.
    
    Args:
        prompt: El prompt a enviar
        api_key: La API key
        base_dir: Directorio base para guardar output
        
    Returns:
        str: La respuesta de GLM-4.7
    """
    try:
        # Intentar con openai primero (más común)
        from openai import OpenAI
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        print("🔄 Enviando a GLM-4.7...")
        response = client.chat.completions.create(
            model="z-ai/glm-4.7-64b-1m-fix",
            messages=[
                {"role": "system", "content": "You are a Python refactoring specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            top_p=0.95
        )
        
        result = response.choices[0].message.content
        print("\n" + "="*80)
        print("✅ RESPUESTA DE GLM-4.7:")
        print("="*80 + "\n")
        print(result)
        print("\n" + "="*80)
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nAsegúrate de tener:")
        print("1. pip install openai")
        print("2. API key válida en .env")
        print("3. Conexión a internet")
        sys.exit(1)

def main():
    # Configurar rutas relativas a la carpeta refactor/
    base_dir = Path(__file__).parent
    prompt_file = base_dir / "GLM_REFACTOR_PROMPT.md"
    
    # Verificar que el prompt existe
    if not prompt_file.exists():
        print("❌ ERROR: No se encuentra GLM_REFACTOR_PROMPT.md")
        print(f"Buscando en: {prompt_file.absolute()}")
        sys.exit(1)
    
    # Cargar prompt
    prompt = prompt_file.read_text()
    
    # Mostrar resumen
    print("="*80)
    print("🚀 REFACTORING CON GLM-4.7")
    print("="*80)
    print(f"📄 Archivo: {prompt_file.absolute()}")
    print(f"📊 Tamaño: {len(prompt)} caracteres")
    print(f"🎯 Modelo: z-ai/glm-4.7-64b-1m-fix")
    print("="*80 + "\n")
    
    # Cargar API key (busca en diferentes ubicaciones)
    api_key = load_api_key()
    print("✅ API key cargada\n")
    
    # Confirmar
    print("¿Deseas enviar este prompt ahora? (y/n): ", end="")
    confirm = input().strip().lower()
    if confirm != 'y':
        print("🛑 Operación cancelada")
        sys.exit(0)
    
    # Enviar
    result = send_to_glm(prompt, api_key)
    
    # Guardar resultado
    output_file = base_dir / "refactor_output.txt"
    output_file.write_text(result)
    print(f"\n📄 Resultado guardado en: {output_file.absolute()}")

if __name__ == "__main__":
    main()
