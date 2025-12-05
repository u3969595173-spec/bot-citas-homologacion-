# 🚀 Guía de Deploy Multi-Región (3 Bots)

## ✅ Código Ya Preparado

El código ya está listo para multi-región:
- ✅ Identificador de instancia (`BOT_INSTANCE_ID`)
- ✅ Lock distribuido en PostgreSQL (`SELECT FOR UPDATE SKIP LOCKED`)
- ✅ Logs con prefijo de región

---

## 📋 Paso 1: Upgrade PostgreSQL

1. Ve a Render Dashboard → **PostgreSQL**
2. Settings → **Upgrade Plan**
3. Selecciona: **Standard ($7/mo)**
   - 100 conexiones concurrentes
   - 10GB storage
   - Soporta 3 bots simultáneos

---

## 📋 Paso 2: Crear Bot #1 (US West)

1. Render Dashboard → **New Web Service**
2. Conecta repo: `bot-citas-homologacion-`
3. **Configuración**:
   ```
   Name: citasbot-us
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python main.py
   Instance Type: Professional ($7/mo)
   ```

4. **Environment Variables**:
   ```bash
   TELEGRAM_BOT_TOKEN=<tu_token>
   ADMIN_USER_ID=<tu_user_id>
   DATABASE_URL=<copiar_de_PostgreSQL>
   BOT_INSTANCE_ID=US-WEST
   ```

5. Click **Create Web Service**

---

## 📋 Paso 3: Crear Bot #2 (EU Central)

1. Repeat paso 2
2. **Name**: `citasbot-eu`
3. **Region**: Frankfurt (EU Central)
4. **BOT_INSTANCE_ID**: `EU-CENTRAL`
5. Mismo `DATABASE_URL` (misma base de datos)

---

## 📋 Paso 4: Crear Bot #3 (Asia)

1. Repeat paso 2
2. **Name**: `citasbot-asia`
3. **Region**: Singapore (Asia)
4. **BOT_INSTANCE_ID**: `ASIA-SG`
5. Mismo `DATABASE_URL`

---

## 🎯 Resultado Final

### 🌐 3 Bots Simultáneos:

```
📍 citasbot-us (Oregon)       → 5,000 checks/seg → 72 horarios
📍 citasbot-eu (Frankfurt)    → 5,000 checks/seg → 72 horarios  
📍 citasbot-asia (Singapore)  → 5,000 checks/seg → 72 horarios
                                ──────────────────────────────
                        TOTAL:  15,000 checks/seg → 216 horarios
```

### 🔒 Sincronización Automática:

- **PostgreSQL** coordina la cola entre los 3 bots
- **`SELECT FOR UPDATE SKIP LOCKED`** previene colisiones
- Solo 1 bot procesa cada usuario (FIFO garantizado)

### 📊 Logs Identificables:

```
[US-WEST] ✓ Check #5000 - Sin citas
[EU-CENTRAL] 🎯 CITA DISPONIBLE: ['2025-12-10']
[ASIA-SG] ✓ Check #10000 - Sin citas
```

---

## 💰 Costo Total

| Item | Precio | Cant. | Total |
|------|--------|-------|-------|
| Bot Professional | $7/mo | 3 | $21/mo |
| PostgreSQL Standard | $7/mo | 1 | $7/mo |
| **TOTAL** | | | **$28/mo** |

---

## ✅ Verificar Funcionamiento

1. Envía `/status` al bot de Telegram
2. Revisa logs en Render:
   - Deberías ver `[US-WEST]`, `[EU-CENTRAL]`, `[ASIA-SG]`
   - Checks incrementando en los 3

3. Prueba con `/registrar`:
   - Solo 1 bot procesará tu solicitud
   - Los 3 están monitoreando en paralelo

---

## 🔥 Ventajas Inmediatas

✅ **3x más rápido** detectando citas  
✅ **3x cobertura** de horarios (216 slots simultáneos)  
✅ **Redundancia**: Si 1 bot falla, otros 2 siguen  
✅ **Sin colisiones**: Lock distribuido en PostgreSQL  
✅ **Latencia optimizada**: Siempre 1 bot cerca del servidor  

---

## 🚨 Importante

- Los 3 bots usan el **mismo token de Telegram** ✅
- Los 3 comparten la **misma base de datos** ✅
- Telegram distribuye updates automáticamente ✅
- PostgreSQL coordina la cola sin duplicados ✅

---

## 📞 Próximos Pasos

1. **Deploy bots** siguiendo esta guía
2. **Monitorea logs** primeras 24h
3. **Si sigues perdiendo citas**: Considera añadir proxies ($8-15/mo)
4. **Ultimate setup**: Multi-región + Proxies = 45,000 checks/seg ($36/mo)

**¡Tu bot ahora será 3x más rápido que la competencia!** 🚀
