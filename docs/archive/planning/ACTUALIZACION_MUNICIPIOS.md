# 🔄 Actualización Automática de Municipios

## 📋 Problema Actual

El sidebar muestra municipios **desactualizados** porque:

1. **Cache de 1 hora** en el índice (demasiado largo para actualizaciones frecuentes)
2. **Polling cada 30 segundos** del frontend, pero depende del cache del backend
3. **Con GitHub Raw**: No detecta cambios hasta que expire el cache

**Resultado**: Los municipios se actualizan hasta **1 hora después** de subir nuevos datos a GitHub.

---

## ✅ Soluciones Implementadas

He implementado **3 soluciones** complementarias. Puedes usar una o combinarlas:

### **Opción 1: Webhook de GitHub** (⭐ RECOMENDADA)

**Actualización instantánea** cuando haces push a GitHub.

### **Opción 2: Cache Reducido**

Cache de **5 minutos** (antes 1 hora) para detectar cambios más rápido.

### **Opción 3: Script Manual**

Script que actualiza datos y fuerza refresh del chatbot.

---

## 🎯 Opción 1: Webhook de GitHub (Instantáneo)

### Cómo Funciona

```
1. Haces git push a sibom-data
   ↓
2. GitHub dispara webhook
   ↓
3. Vercel recibe webhook en /api/webhook/github
   ↓
4. Invalida cache del RAG
   ↓
5. Próxima consulta recarga datos frescos
   ↓
6. Sidebar detecta cambio y actualiza (30s max)
```

**Tiempo total**: **~30-60 segundos** desde push hasta ver nuevos municipios.

---

### Paso 1: Configurar Webhook en GitHub

1. **Ve a tu repo `sibom-data`** en GitHub

2. **Settings → Webhooks → Add webhook**

3. **Configura el webhook**:
   ```
   Payload URL: https://tu-app.vercel.app/api/webhook/github
   Content type: application/json
   Secret: (genera un token aleatorio, guárdalo)
   Which events: Just the push event
   Active: ✓
   ```

4. **Genera un secret seguro**:
   ```bash
   # En tu terminal
   openssl rand -hex 32
   ```
   Ejemplo: `a1b2c3d4e5f6...` (64 caracteres)

5. **Guarda el secret** en Vercel (siguiente paso)

---

### Paso 2: Configurar Secret en Vercel

1. **Ve a Vercel** → Tu proyecto → **Settings** → **Environment Variables**

2. **Agrega variable**:
   ```
   Name: GITHUB_WEBHOOK_SECRET
   Value: (el token que generaste)
   Environments: Production, Preview, Development
   ```

3. **Redeploy** (Settings → Deployments → ••• → Redeploy)

---

### Paso 3: Probar el Webhook

1. **Hacer un cambio en `sibom-data`**:
   ```bash
   cd sibom-data
   echo "test" > test.txt
   git add test.txt
   git commit -m "Test webhook"
   git push
   ```

2. **Verificar en GitHub**:
   - Ve a Settings → Webhooks
   - Click en el webhook
   - Tab "Recent Deliveries"
   - Debe mostrar **200 OK** con respuesta verde

3. **Verificar en Vercel**:
   - Functions → Logs
   - Debe mostrar: `[GitHubWebhook] Push detectado en rama principal - Invalidando cache`

---

### Paso 4: Workflow Completo

Ahora cuando actualices datos:

```bash
# 1. Scraper nuevos boletines
cd python-cli
python sibom_scraper.py --limit 20

# 2. Reindexar
python indexar_boletines.py

# 3. Comprimir (opcional)
python comprimir_boletines.py

# 4. Subir a GitHub
cd ../sibom-data
cp ../python-cli/boletines/*.json.gz ./boletines/
cp ../python-cli/boletines_index.json.gz ./
git add .
git commit -m "Add 20 new bulletins"
git push  # ← Esto dispara el webhook automáticamente
```

**Resultado**:
- GitHub recibe push
- Webhook invalida cache en Vercel
- Próxima consulta recarga datos
- Sidebar detecta cambio en <30s
- **Total: ~1 minuto** ✨

---

## ⚡ Opción 2: Cache Reducido (Sin Webhook)

Si no quieres configurar webhook, simplemente reduce el cache.

### Configuración

He modificado el retriever para que el cache sea configurable.

**En Vercel**, agrega esta variable:

```
Name: INDEX_CACHE_DURATION
Value: 300000  (5 minutos en milisegundos)
Environments: Production
```

**Valores sugeridos**:
- `60000` = 1 minuto (muy frecuente, más requests a GitHub)
- `300000` = 5 minutos (**recomendado sin webhook**)
- `600000` = 10 minutos (balance)
- `3600000` = 1 hora (con webhook activo)

**Redeploy** después de agregar la variable.

---

### Cómo Funciona

```
Polling del Sidebar (cada 30s)
   ↓
Verifica /api/refresh (fecha de última actualización)
   ↓
Si cache expiró (5 min):
   ↓
   Recarga índice desde GitHub
   ↓
   Detecta nuevos municipios
   ↓
   Frontend actualiza sidebar
```

**Tiempo**: **5-6 minutos** máximo desde push hasta ver cambios.

---

## 🔧 Opción 3: Script Manual

Para forzar actualización inmediata sin esperar.

### Uso del Script

```bash
cd python-cli

# Opción 1: Actualización completa automática
./actualizar_datos_github.sh

# Opción 2: Con mensaje de commit personalizado
./actualizar_datos_github.sh "Add new bulletins for Campana"
```

### Qué Hace el Script

1. ✅ Reindexar boletines (`indexar_boletines.py`)
2. ✅ Comprimir archivos (opcional, te pregunta)
3. ✅ Copiar a repo `sibom-data`
4. ✅ Commit con estadísticas automáticas
5. ✅ Push a GitHub
6. ✅ Llamar a `/api/refresh` para invalidar cache (si configuras `VERCEL_APP_URL`)

### Configurar URL de Vercel

```bash
# En tu .bashrc o .zshrc
export VERCEL_APP_URL=https://tu-app.vercel.app
```

O temporalmente:

```bash
VERCEL_APP_URL=https://tu-app.vercel.app ./actualizar_datos_github.sh
```

---

## 📊 Comparación de Opciones

| Opción | Tiempo | Setup | Costo Bandwidth | Automático |
|--------|--------|-------|-----------------|------------|
| **Webhook GitHub** | ~30-60s | Medio (15 min) | Mínimo | ✅ Sí |
| **Cache Reducido (5 min)** | ~5-6 min | Fácil (2 min) | Medio | ✅ Sí |
| **Script Manual** | Inmediato | Fácil (5 min) | Mínimo | ⚠️ Manual |

---

## 🎯 Recomendación

### Para Producción (Mejor Opción)

**Webhook + Cache de 1 hora**:
```bash
# En Vercel
GITHUB_WEBHOOK_SECRET=tu-secret-aqui
INDEX_CACHE_DURATION=3600000  # 1 hora
```

**Ventajas**:
- ✅ Actualización instantánea cuando subes datos
- ✅ Mínimo bandwidth (cache largo entre actualizaciones)
- ✅ Completamente automático

---

### Para MVP/Testing

**Cache de 5 minutos** (sin webhook):
```bash
# En Vercel
INDEX_CACHE_DURATION=300000  # 5 min
```

**Ventajas**:
- ✅ Setup simple (solo 1 variable)
- ✅ Actualización aceptable (5-6 min)
- ⚠️ Más bandwidth que webhook

---

### Para Desarrollo Local

**Script manual** cuando necesites:
```bash
./actualizar_datos_github.sh
```

---

## 🧪 Probar que Funciona

### Prueba del Webhook

```bash
# 1. Agrega un municipio fake al índice
cd python-cli
echo '{"id":"test","municipality":"Test City",...}' >> boletines_index.json

# 2. Sube a GitHub
cd ../sibom-data
cp ../python-cli/boletines_index.json ./
git add .
git commit -m "Test: Add fake municipality"
git push

# 3. Espera 30-60 segundos

# 4. Abre tu app en Vercel
# 5. Verifica el sidebar → Debe aparecer "Test City"

# 6. Limpia el test
git revert HEAD
git push
```

---

### Prueba del Cache Reducido

```bash
# 1. Configura INDEX_CACHE_DURATION=60000 (1 min) en Vercel
# 2. Redeploy
# 3. Sube cambio a GitHub
# 4. Espera ~1-2 minutos
# 5. Refresca el chatbot → Debe ver cambios
```

---

## ❓ FAQ

### ¿Puedo combinar webhook + cache reducido?

Sí, pero no tiene sentido. Con webhook, el cache se invalida inmediatamente, así que un cache largo (1h) es mejor para ahorrar bandwidth.

### ¿El webhook funciona en Vercel free tier?

Sí, completamente. Los webhooks solo disparan una función serverless, que está incluida en el plan gratuito.

### ¿Qué pasa si el webhook falla?

El polling del frontend sigue funcionando. En el peor caso, verás los cambios cuando expire el cache (según `INDEX_CACHE_DURATION`).

### ¿Cuántas veces puedo disparar el webhook?

GitHub permite webhooks ilimitados. Vercel permite funciones serverless ilimitadas en free tier.

---

## 📚 Archivos Creados

1. **`/chatbot/src/app/api/webhook/github/route.ts`**
   - Handler del webhook de GitHub
   - Verifica firma de seguridad
   - Invalida cache automáticamente

2. **`/python-cli/actualizar_datos_github.sh`**
   - Script todo-en-uno para actualizar datos
   - Interfaz interactiva
   - Llamada a API de refresh

3. **Modificación en `/chatbot/src/lib/rag/retriever.ts`**
   - Cache configurable via `INDEX_CACHE_DURATION`
   - Permite ajustar sin modificar código

---

## ✅ Checklist de Implementación

### Con Webhook (Recomendado)

- [ ] Generar secret: `openssl rand -hex 32`
- [ ] Configurar webhook en GitHub (sibom-data → Settings → Webhooks)
- [ ] Agregar `GITHUB_WEBHOOK_SECRET` en Vercel
- [ ] Redeploy en Vercel
- [ ] Probar con push de prueba
- [ ] Verificar logs en Vercel y GitHub

### Sin Webhook (Simple)

- [ ] Agregar `INDEX_CACHE_DURATION=300000` en Vercel
- [ ] Redeploy en Vercel
- [ ] Probar subiendo datos a GitHub
- [ ] Esperar 5-6 minutos
- [ ] Verificar actualización en sidebar

---

¡Listo! Ahora tus municipios se mantendrán actualizados automáticamente. 🎉
