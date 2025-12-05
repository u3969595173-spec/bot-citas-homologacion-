# 🚀 FASE 1: Setup 6 Bots Multi-Región (30,000 checks/seg)

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL Standard                       │
│                   (Coordinación central)                     │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐         ┌────▼───┐         ┌────▼───┐
    │  US-W  │         │  US-E  │         │  EU-C  │
    │ Oregon │         │Virginia│         │Frankfurt│
    │5k/sec  │         │5k/sec  │         │5k/sec  │
    └────────┘         └────────┘         └────────┘
        │                   │                   │
    ┌───▼────┐         ┌────▼───┐         ┌────▼───┐
    │ EU-W   │         │ ASIA-S │         │ ASIA-M │
    │ París  │         │Singapore│        │ Mumbai │
    │5k/sec  │         │5k/sec  │         │5k/sec  │
    └────────┘         └────────┘         └────────┘

TOTAL: 30,000 checks/segundo + redundancia
```

---

## ✅ PRE-REQUISITOS (HACER AHORA)

### 1. Upgrade PostgreSQL

**En Render Dashboard:**
1. PostgreSQL → Settings
2. **Upgrade to Standard** ($7/mo)
3. Confirmar upgrade
4. Esperar 2-3 minutos

**¿Por qué?**
- 100 conexiones concurrentes (vs 20 en Free)
- Necesario para 6 bots simultáneos

---

## 🤖 PASO A PASO: CREAR 6 BOTS

### Bot #1: US-WEST (Oregon) - YA EXISTE

**Modificar bot actual:**
1. Dashboard → Tu bot actual
2. Environment → Add Variable:
   ```
   BOT_INSTANCE_ID = US-WEST
   ```
3. Save Changes

---

### Bot #2: US-EAST (Virginia)

1. **New Web Service** → Connect Repository
2. **Configuración:**
   ```
   Name: citasbot-us-east
   Region: Virginia (US East)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
   Instance Type: Professional ($7/mo)
   ```

3. **Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN = <copiar_del_bot_1>
   ADMIN_USER_ID = <copiar_del_bot_1>
   DATABASE_URL = <copiar_del_PostgreSQL>
   BOT_INSTANCE_ID = US-EAST
   ```

4. **Create Web Service**

---

### Bot #3: EU-CENTRAL (Frankfurt)

1. **New Web Service**
2. **Configuración:**
   ```
   Name: citasbot-eu-central
   Region: Frankfurt (EU Central)
   Branch: main
   Instance Type: Professional ($7/mo)
   ```

3. **Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN = <mismo_token>
   ADMIN_USER_ID = <mismo_id>
   DATABASE_URL = <mismo_database_url>
   BOT_INSTANCE_ID = EU-CENTRAL
   ```

---

### Bot #4: EU-WEST (París)

1. **New Web Service**
2. **Configuración:**
   ```
   Name: citasbot-eu-west
   Region: Paris (EU West)
   Branch: main
   Instance Type: Professional ($7/mo)
   ```

3. **Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN = <mismo_token>
   ADMIN_USER_ID = <mismo_id>
   DATABASE_URL = <mismo_database_url>
   BOT_INSTANCE_ID = EU-WEST
   ```

---

### Bot #5: ASIA-SOUTHEAST (Singapore)

1. **New Web Service**
2. **Configuración:**
   ```
   Name: citasbot-asia-se
   Region: Singapore (Asia Southeast)
   Branch: main
   Instance Type: Professional ($7/mo)
   ```

3. **Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN = <mismo_token>
   ADMIN_USER_ID = <mismo_id>
   DATABASE_URL = <mismo_database_url>
   BOT_INSTANCE_ID = ASIA-SOUTHEAST
   ```

---

### Bot #6: ASIA-SOUTH (Mumbai)

1. **New Web Service**
2. **Configuración:**
   ```
   Name: citasbot-asia-south
   Region: Mumbai (Asia South)
   Branch: main
   Instance Type: Professional ($7/mo)
   ```

3. **Environment Variables:**
   ```bash
   TELEGRAM_BOT_TOKEN = <mismo_token>
   ADMIN_USER_ID = <mismo_id>
   DATABASE_URL = <mismo_database_url>
   BOT_INSTANCE_ID = ASIA-SOUTH
   ```

---

## ✅ VERIFICAR FUNCIONAMIENTO

### 1. Revisar Logs en Render

Cada bot debe mostrar:
```
🔥 PRE-ESTABLECIENDO 10 conexiones HTTP/2...
✅ 10 conexiones HTTP/2 PRE-ESTABLECIDAS
✅ 72 payloads PRE-GENERADOS en RAM
🚀 Iniciando Bot de Citas...
[US-WEST] ✓ Check #5000 - Sin citas disponibles
```

### 2. Probar en Telegram

Envía `/status` al bot → Deberías ver:
- 👥 Usuarios activos: X
- Checks incrementando rápidamente

### 3. Verificar PostgreSQL

Dashboard PostgreSQL → Connections:
- Deberías ver ~6 conexiones activas
- Una por cada bot

---

## 📊 RESULTADO ESPERADO

```
Bot          Región        Checks/seg   Horarios   Latencia
──────────────────────────────────────────────────────────────
US-WEST      Oregon        5,000        72         ~90ms
US-EAST      Virginia      5,000        72         ~85ms
EU-CENTRAL   Frankfurt     5,000        72         ~60ms  ⭐
EU-WEST      París         5,000        72         ~65ms
ASIA-SE      Singapore     5,000        72         ~120ms
ASIA-SOUTH   Mumbai        5,000        72         ~110ms
──────────────────────────────────────────────────────────────
TOTAL:                     30,000       432        ~88ms avg
```

**Ventajas:**
- ✅ 3x detección más rápida que antes
- ✅ Siempre 1-2 bots cerca del servidor español
- ✅ Redundancia: Si 1 falla, otros 5 siguen
- ✅ Lock distribuido previene colisiones

---

## 💰 COSTO FASE 1

| Item | Cantidad | Precio | Total |
|------|----------|--------|-------|
| Bots Professional | 6 | $7/mo | $42/mo |
| PostgreSQL Standard | 1 | $7/mo | $7/mo |
| **TOTAL FASE 1** | | | **$49/mo** |

---

## 🚨 PROBLEMAS COMUNES

### Error: "Database connection limit exceeded"
- Solución: Asegurar PostgreSQL Standard ($7/mo)

### Bot no se conecta a PostgreSQL
- Verificar DATABASE_URL es exactamente igual en todos
- Copiar desde PostgreSQL → Internal Database URL

### "Duplicate key in queue"
- Normal: SELECT FOR UPDATE SKIP LOCKED lo previene
- Revisar logs: Solo 1 bot debe procesar cada usuario

---

## 🎯 SIGUIENTE PASO

Una vez los 6 bots estén funcionando:
- Verifica logs durante 5-10 minutos
- Confirma que todos muestran `[REGION] ✓ Check #X`
- Envía "LISTO FASE 1" para pasar a **FASE 2: Proxies Bright Data**

---

**COSTO ACUMULADO:** $49/mo  
**VELOCIDAD:** 30,000 checks/seg (6x más rápido)  
**TIEMPO ESTIMADO:** 15-20 minutos para crear los 6 bots
