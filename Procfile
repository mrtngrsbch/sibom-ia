# Procfile para Overmind - Gestión de servicios de desarrollo
# Uso: overmind start

backend: cd sat-analysis && source venv/bin/activate && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
# Especificamos PORT=3000 explícitamente porque overmind por defecto asigna 5000 + step
frontend: cd chatbot && PORT=3000 pnpm run dev
