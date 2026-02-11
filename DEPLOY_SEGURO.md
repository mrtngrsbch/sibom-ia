# Guía de Despliegue Seguro - Hostinger VPS

## Enfoque Recomendado: Usar Docker Manager de Hostinger

En lugar de scripts automáticos, usá la interfaz web de Hostinger que es más segura.

---

## PASO 1: Clonar repositorio en el VPS

Conectate por SSH al VPS:
```bash
ssh root@89.116.49.63
```

Luego ejecutá:
```bash
cd ~
git clone https://github.com/mrtngrsbch/sibom-scraper-assistant.git
cd sibom-scraper-assistant
```

---

## PASO 2: Crear archivo .env

```bash
cp .env.example .env  # si existe, sino:
nano .env
```

Pegá tus variables:
```env
NODE_ENV=production
OPENROUTER_API_KEY=sk-or-v1-TU_KEY_REAL
LLM_MODEL_PRIMARY=google/gemini-3-flash-preview
LLM_MODEL_ECONOMIC=google/gemini-2.0-flash-lite-001
SAT_API_URL=http://sat-analysis:8001
USE_NORMATIVAS_INDEX=true
USE_SQLITE=true
```

Guardá: `Ctrl+X`, `Y`, `Enter`

---

## PASO 3: Crear contenedores en Docker Manager

### Opción A: Usando Hostinger Docker Manager (Recomendado)

1. **Entrá a Hostinger hPanel** → **Docker** → **Docker Manager**
2. **Click en "Create Project"**
3. **Nombre**: `mangrullo-chatbot`
4. **Elegí "Compose"** si está disponible, o creá los contenedores individualmente:

#### Contenedor 1: chatbot
- **Image**: `Dejá esto vacío` (vamos a build desde GitHub)
- **Nombre**: `chatbot`
- **Puertos**: `3000:3000`
- **Environment Variables**:
  ```
  NODE_ENV=production
  SAT_API_URL=http://sat-analysis:8001
  OPENROUTER_API_KEY=TU_KEY
  ```

#### Contenedor 2: sat-analysis
- **Image**: `Dejá esto vacío`
- **Nombre**: `sat-analysis`
- **Puertos**: `8001:8001`
- **Volumes**:
  - `sat-data:/app/data`
  - `sat-cache:/app/cache`

#### Contenedor 3: nginx
- **Image**: `nginx:alpine`
- **Nombre**: `nginx`
- **Puertos**: `80:80`, `443:443`
- **Volumes**:
  - Mount: `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`

### Opción B: Deploy automático desde GitHub (si está disponible)

Hostinger puede hacer deploy directo desde GitHub. Configurá:
- **Repository**: `https://github.com/mrtngrsbch/sibom-scraper-assistant.git`
- **Branch**: `main`
- **Root Path**: `/chatbot` para el frontend

---

## PASO 4: Configurar SSL en Hostinger

Hostinger tiene Let's Encrypt integrado:

1. **hPanel** → **SSL** → **Let's Encrypt**
2. **Seleccioná dominio**: `mangrullo.microagencia.com`
3. **Click en "Obtener Certificado"**
4. Hostinger configura automáticamente nginx

---

## PASO 5: Verificar

```bash
# Ver contenedores corriendo
docker ps

# Ver logs
docker logs sibom-chatbot
docker logs sibom-sat-analysis

# Verificar respuesta
curl http://localhost:3000/api/health
curl http://localhost:8001/api/health
```

---

## Troubleshooting

### Si un contenedor no inicia
```bash
docker logs sibom-chatbot
docker logs sibom-sat-analysis
```

### Si hay problemas de red entre contenedores
```bash
# Verificar que están en la misma red
docker network inspect sibom-scraper-assistant_sibom-network
```

### Si SSL no funciona
Usá el proxy SSL de Hostinger en lugar de configurarlo manualmente en nginx.

---

## Comandos útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar un contenedor
docker restart sibom-chatbot

# Actualizar código (después de git pull)
docker-compose up -d --build

# Detener todo
docker-compose down
```
