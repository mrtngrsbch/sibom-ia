# Hook de Deployment Automático - SIBOM Scraper Assistant

## Configuración del Hook

### Trigger Event
**Evento:** `onGitPush`
**Branches objetivo:** `main`, `production`
**Descripción:** Despliega automáticamente la aplicación cuando se hace push a branches principales

### Configuración del Hook
```json
{
  "name": "auto-deployment",
  "description": "Despliega automáticamente en Vercel cuando se hace push a main",
  "trigger": {
    "event": "onGitPush",
    "branches": ["main", "production"],
    "paths": ["chatbot/**/*", "python-cli/**/*", ".env.example"]
  },
  "actions": [
    {
      "type": "shellCommand",
      "command": "npm run build",
      "workingDirectory": "chatbot",
      "condition": "branch === 'main'"
    },
    {
      "type": "shellCommand",
      "command": "npm run test:ci",
      "workingDirectory": "chatbot", 
      "condition": "branch === 'main'"
    },
    {
      "type": "shellCommand",
      "command": "vercel --prod",
      "workingDirectory": "chatbot",
      "condition": "branch === 'main' && previousSteps.success"
    },
    {
      "type": "agentMessage",
      "message": "🚀 Iniciando deployment a producción...",
      "condition": "branch === 'main'"
    }
  ],
  "enabled": true
}
```

## Estrategia de Deployment

### 1. Frontend Next.js - Vercel

#### Configuración de Vercel
**Ubicación:** `chatbot/vercel.json`
```json
{
  "version": 2,
  "name": "sibom-chatbot",
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "env": {
    "OPENROUTER_API_KEY": "@openrouter-api-key",
    "LLM_MODEL_PRIMARY": "@llm-model-primary",
    "LLM_MODEL_ECONOMIC": "@llm-model-economic",
    "GITHUB_DATA_REPO": "@github-data-repo",
    "GITHUB_DATA_BRANCH": "@github-data-branch",
    "GITHUB_USE_GZIP": "@github-use-gzip"
  },
  "functions": {
    "chatbot/src/app/api/chat/route.ts": {
      "maxDuration": 60
    }
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Access-Control-Allow-Origin",
          "value": "*"
        },
        {
          "key": "Access-Control-Allow-Methods",
          "value": "GET, POST, PUT, DELETE, OPTIONS"
        },
        {
          "key": "Access-Control-Allow-Headers",
          "value": "Content-Type, Authorization"
        }
      ]
    }
  ]
}
```

#### Script de Build Optimizado
**Ubicación:** `chatbot/package.json`
```json
{
  "scripts": {
    "build": "next build",
    "build:analyze": "ANALYZE=true next build",
    "build:production": "NODE_ENV=production next build",
    "test:ci": "vitest run --coverage --reporter=json",
    "lint:ci": "next lint --max-warnings 0",
    "type-check": "tsc --noEmit",
    "deploy:preview": "vercel",
    "deploy:production": "vercel --prod"
  }
}
```

### 2. Backend Python - GitHub Actions + Docker

#### Dockerfile para Python CLI
**Ubicación:** `python-cli/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorio para datos
RUN mkdir -p boletines

# Exponer puerto para health checks
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando por defecto
CMD ["python", "sibom_scraper.py", "--server"]
```

#### Docker Compose para Desarrollo
**Ubicación:** `docker-compose.yml`
```yaml
version: '3.8'

services:
  chatbot:
    build:
      context: ./chatbot
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./chatbot:/app
      - /app/node_modules
    depends_on:
      - scraper

  scraper:
    build:
      context: ./python-cli
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./python-cli:/app
      - ./data:/app/boletines
    command: python sibom_scraper.py --server --host 0.0.0.0

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - chatbot
      - scraper
```

## Pipeline de CI/CD

### GitHub Actions Workflow
**Ubicación:** `.github/workflows/deploy.yml`
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'chatbot/**'
      - 'python-cli/**'
      - '.github/workflows/**'

env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: chatbot/package-lock.json

      - name: Install dependencies
        run: |
          cd chatbot
          npm ci

      - name: Type check
        run: |
          cd chatbot
          npm run type-check

      - name: Lint
        run: |
          cd chatbot
          npm run lint:ci

      - name: Run tests
        run: |
          cd chatbot
          npm run test:ci

      - name: Build
        run: |
          cd chatbot
          npm run build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-build
          path: chatbot/.next

  test-backend:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd python-cli
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd python-cli
          python -m pytest tests/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: python-cli/coverage.xml
          flags: backend

  deploy-frontend:
    needs: [test-frontend, test-backend]
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install Vercel CLI
        run: npm install --global vercel@latest

      - name: Pull Vercel Environment Information
        run: |
          cd chatbot
          vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project Artifacts
        run: |
          cd chatbot
          vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy Project Artifacts to Vercel
        run: |
          cd chatbot
          vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}

  deploy-backend:
    needs: [test-frontend, test-backend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./python-cli
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/sibom-scraper:latest
            ${{ secrets.DOCKER_USERNAME }}/sibom-scraper:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Deploy to production server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            docker pull ${{ secrets.DOCKER_USERNAME }}/sibom-scraper:latest
            docker stop sibom-scraper || true
            docker rm sibom-scraper || true
            docker run -d \
              --name sibom-scraper \
              --restart unless-stopped \
              -p 8000:8000 \
              -e OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }} \
              -v /data/sibom:/app/boletines \
              ${{ secrets.DOCKER_USERNAME }}/sibom-scraper:latest

  notify-deployment:
    needs: [deploy-frontend, deploy-backend]
    runs-on: ubuntu-latest
    if: always()
    steps:
      - name: Notify success
        if: needs.deploy-frontend.result == 'success' && needs.deploy-backend.result == 'success'
        run: |
          echo "🚀 Deployment successful!"
          # Aquí se puede agregar notificación a Slack, Discord, etc.

      - name: Notify failure
        if: needs.deploy-frontend.result == 'failure' || needs.deploy-backend.result == 'failure'
        run: |
          echo "❌ Deployment failed!"
          # Aquí se puede agregar notificación de error
```

## Configuración de Entornos

### Variables de Entorno por Ambiente

#### Desarrollo (.env.local)
```bash
# Desarrollo local
NODE_ENV=development
OPENROUTER_API_KEY=sk-or-v1-dev-key
LLM_MODEL_PRIMARY=google/gemini-2.0-flash-exp
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=
GITHUB_DATA_BRANCH=main
GITHUB_USE_GZIP=false
INDEX_CACHE_DURATION=60000
```

#### Staging (.env.staging)
```bash
# Staging/Preview
NODE_ENV=production
OPENROUTER_API_KEY=sk-or-v1-staging-key
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=usuario/sibom-data
GITHUB_DATA_BRANCH=staging
GITHUB_USE_GZIP=true
INDEX_CACHE_DURATION=300000
```

#### Producción (Vercel Environment Variables)
```bash
# Producción
NODE_ENV=production
OPENROUTER_API_KEY=sk-or-v1-prod-key
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=usuario/sibom-data-prod
GITHUB_DATA_BRANCH=main
GITHUB_USE_GZIP=true
INDEX_CACHE_DURATION=3600000
```

## Estrategias de Deployment

### 1. Blue-Green Deployment
```yaml
# .github/workflows/blue-green-deploy.yml
name: Blue-Green Deployment

on:
  push:
    branches: [main]

jobs:
  deploy-blue:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Blue environment
        run: |
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }} \
            --env DEPLOYMENT_COLOR=blue

      - name: Health check Blue
        run: |
          curl -f https://blue.sibom-chat.vercel.app/api/health

      - name: Switch traffic to Blue
        if: success()
        run: |
          # Cambiar DNS o load balancer a Blue
          echo "Traffic switched to Blue"
```

### 2. Canary Deployment
```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deployment

on:
  push:
    branches: [main]

jobs:
  deploy-canary:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Canary (10% traffic)
        run: |
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }} \
            --env CANARY_PERCENTAGE=10

      - name: Monitor Canary metrics
        run: |
          # Monitorear métricas por 10 minutos
          sleep 600
          python scripts/check_canary_metrics.py

      - name: Promote to 100% if healthy
        if: success()
        run: |
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }} \
            --env CANARY_PERCENTAGE=100
```

### 3. Rollback Automático
```yaml
# .github/workflows/rollback.yml
name: Automatic Rollback

on:
  workflow_run:
    workflows: ["Deploy to Production"]
    types: [completed]

jobs:
  health-check:
    runs-on: ubuntu-latest
    if: github.event.workflow_run.conclusion == 'success'
    steps:
      - name: Wait for deployment to stabilize
        run: sleep 120

      - name: Health check
        id: health
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" https://sibom-chat.vercel.app/api/health)
          if [ $response -ne 200 ]; then
            echo "health=failed" >> $GITHUB_OUTPUT
          else
            echo "health=passed" >> $GITHUB_OUTPUT
          fi

      - name: Rollback if unhealthy
        if: steps.health.outputs.health == 'failed'
        run: |
          # Obtener deployment anterior
          PREV_DEPLOYMENT=$(vercel ls --token=${{ secrets.VERCEL_TOKEN }} | grep READY | head -2 | tail -1 | awk '{print $1}')
          
          # Promover deployment anterior
          vercel promote $PREV_DEPLOYMENT --token=${{ secrets.VERCEL_TOKEN }}
          
          echo "🔄 Rollback ejecutado automáticamente"
```

## Monitoreo Post-Deployment

### Health Checks
**Ubicación:** `chatbot/src/app/api/health/route.ts`
```typescript
export async function GET() {
  try {
    // Verificar conexión a OpenRouter
    const openRouterHealth = await fetch('https://openrouter.ai/api/v1/models', {
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
      },
    });

    if (!openRouterHealth.ok) {
      throw new Error('OpenRouter not accessible');
    }

    // Verificar sistema RAG
    const { getDatabaseStats } = await import('@/lib/rag/retriever');
    const stats = await getDatabaseStats();

    if (stats.totalDocuments === 0) {
      throw new Error('No documents in database');
    }

    return Response.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || 'unknown',
      services: {
        openRouter: 'healthy',
        database: 'healthy',
        documentsCount: stats.totalDocuments,
      },
    });
  } catch (error) {
    return Response.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 503 }
    );
  }
}
```

### Métricas de Deployment
```python
# scripts/deployment_metrics.py
import requests
import time
from datetime import datetime

def check_deployment_health():
    """Verifica salud del deployment y métricas clave"""
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'health_status': 'unknown',
        'response_time': 0,
        'api_status': 'unknown',
        'database_status': 'unknown'
    }
    
    try:
        # Health check
        start_time = time.time()
        response = requests.get('https://sibom-chat.vercel.app/api/health', timeout=10)
        metrics['response_time'] = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            metrics['health_status'] = health_data.get('status', 'unknown')
            metrics['api_status'] = health_data.get('services', {}).get('openRouter', 'unknown')
            metrics['database_status'] = health_data.get('services', {}).get('database', 'unknown')
        else:
            metrics['health_status'] = 'unhealthy'
            
    except Exception as e:
        metrics['health_status'] = 'error'
        metrics['error'] = str(e)
    
    return metrics

if __name__ == '__main__':
    metrics = check_deployment_health()
    print(f"Deployment Health: {metrics}")
    
    # Enviar métricas a sistema de monitoreo
    # send_to_monitoring_system(metrics)
```

## Notificaciones y Alertas

### Slack Integration
```python
# scripts/notify_deployment.py
import requests
import os

def notify_slack(message, status='info'):
    """Envía notificación a Slack"""
    
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        return
    
    colors = {
        'success': '#36a64f',
        'warning': '#ff9500', 
        'error': '#ff0000',
        'info': '#0099cc'
    }
    
    payload = {
        'attachments': [{
            'color': colors.get(status, colors['info']),
            'fields': [{
                'title': 'SIBOM Chatbot Deployment',
                'value': message,
                'short': False
            }],
            'footer': 'GitHub Actions',
            'ts': int(time.time())
        }]
    }
    
    requests.post(webhook_url, json=payload)

# Uso en GitHub Actions
if __name__ == '__main__':
    import sys
    status = sys.argv[1] if len(sys.argv) > 1 else 'info'
    message = sys.argv[2] if len(sys.argv) > 2 else 'Deployment completed'
    
    notify_slack(message, status)
```

### Discord Integration
```python
# scripts/notify_discord.py
import requests
import os

def notify_discord(message, status='info'):
    """Envía notificación a Discord"""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        return
    
    colors = {
        'success': 0x00ff00,
        'warning': 0xff9500,
        'error': 0xff0000,
        'info': 0x0099cc
    }
    
    embed = {
        'title': '🚀 SIBOM Chatbot Deployment',
        'description': message,
        'color': colors.get(status, colors['info']),
        'timestamp': datetime.utcnow().isoformat(),
        'footer': {
            'text': 'GitHub Actions'
        }
    }
    
    payload = {'embeds': [embed]}
    requests.post(webhook_url, json=payload)
```

## Configuración de Secrets

### GitHub Secrets Requeridos
```bash
# Vercel
VERCEL_TOKEN=vercel_token_here
VERCEL_ORG_ID=team_id_here
VERCEL_PROJECT_ID=project_id_here

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-production-key

# Docker Hub
DOCKER_USERNAME=username
DOCKER_PASSWORD=password

# Production Server
PROD_HOST=production.server.ip
PROD_USER=deploy_user
PROD_SSH_KEY=private_ssh_key

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### Vercel Environment Variables
```bash
# En Vercel Dashboard > Settings > Environment Variables
OPENROUTER_API_KEY=sk-or-v1-production-key
LLM_MODEL_PRIMARY=anthropic/claude-3.5-sonnet
LLM_MODEL_ECONOMIC=google/gemini-flash-1.5
GITHUB_DATA_REPO=usuario/sibom-data
GITHUB_DATA_BRANCH=main
GITHUB_USE_GZIP=true
INDEX_CACHE_DURATION=3600000
```

## Checklist de Deployment

### Pre-Deployment
- [ ] ✅ Tests pasando en CI/CD
- [ ] ✅ Build exitoso sin warnings
- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ Secrets configurados en GitHub/Vercel
- [ ] ⏳ Health checks implementados
- [ ] ⏳ Rollback strategy definida

### Post-Deployment
- [ ] ✅ Health check automático
- [ ] ✅ Verificación de funcionalidad básica
- [ ] ⏳ Monitoreo de métricas
- [ ] ⏳ Notificaciones configuradas
- [ ] ⏳ Logs de deployment archivados
- [ ] ⏳ Documentación actualizada

### Rollback Plan
- [ ] ⏳ Procedimiento de rollback documentado
- [ ] ⏳ Rollback automático configurado
- [ ] ⏳ Backup de datos críticos
- [ ] ⏳ Plan de comunicación para incidentes
- [ ] ⏳ Escalation procedures definidos