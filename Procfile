# Procfile para Overmind - Gestión de servicios de desarrollo
# Uso: overmind start

backend: cd sat-analysis && source venv/bin/activate && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8001
frontend: cd chatbot && npm run dev
