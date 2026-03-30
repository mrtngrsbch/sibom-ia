# Pasos a ejecutar

1. Setup inicial del VPS (una sola vez)

```
# Desde tu máquina local, SSH al VPS como root
ssh root@<IP_VPS>

# En el VPS, corre el script de setup
curl -fsSL https://raw.githubusercontent.com/.../scripts/vps-setup.sh | bash
# O bien, copiar el script al VPS y ejecutarlo:
bash scripts/vps-setup.sh
```


2. Configurar tu clave SSH
```
ssh-copy-id deploy@<IP_VPS>
```
3. Crear el .env con tus API keys

```
cp .env.production.example .env
# Editar .env con tus keys reales:
# - OPENROUTER_API_KEY
# - OPENAI_API_KEY
# - (QDRANT_URL ya está configurado para Docker Compose interno)
```

4. Deploy

```
bash scripts/deploy.sh <IP_VPS>
```

El script hace todo automáticamente:

Sincroniza el código (rsync, excluye .git, node_modules, etc.)
Transfiere los índices RAG (~27MB: boletines_index.json, normativas_index.json, normativas_index_minimal.json)
Transfiere el .env
Corre docker compose build --no-cache y docker compose up -d
5. DNS en Cloudflare

```
mangrullo.microagencia.com  →  A  →  <IP_VPS>
```

Cloudflare termina TLS; el VPS solo escucha en HTTP puerto 80.

Logs post-deploy:
```
ssh deploy@<IP_VPS> "cd /opt/mangrullo && docker compose logs -f"
```
