# 🌐 Setup Multi-Región (3 Bots en Paralelo)

## 📋 Paso 1: Crear 3 instancias en Render

### Bot 1 - US West (Oregon)
1. Ve a Render Dashboard → "New Web Service"
2. Conecta el mismo repo: `bot-citas-homologacion-`
3. **Name**: `citasbot-us`
4. **Region**: Oregon (US West)
5. **Instance Type**: Professional ($7/mo)
6. **Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=tu_token
   ADMIN_USER_ID=tu_id
   DATABASE_URL=<misma_DB_postgres>
   BOT_INSTANCE_ID=US-WEST
   ```

### Bot 2 - EU West (Frankfurt)
1. Repeat paso anterior
2. **Name**: `citasbot-eu`
3. **Region**: Frankfurt (EU Central)
4. **Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=tu_token
   ADMIN_USER_ID=tu_id
   DATABASE_URL=<misma_DB_postgres>
   BOT_INSTANCE_ID=EU-CENTRAL
   ```

### Bot 3 - Asia (Singapore)
1. Repeat paso anterior
2. **Name**: `citasbot-asia`
3. **Region**: Singapore (Asia)
4. **Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=tu_token
   ADMIN_USER_ID=tu_id
   DATABASE_URL=<misma_DB_postgres>
   BOT_INSTANCE_ID=ASIA-SG
   ```

---

## 📋 Paso 2: Modificar código para multi-instancia

### En `main.py`, añadir identificador:

```python
import os

BOT_INSTANCE_ID = os.getenv('BOT_INSTANCE_ID', 'SINGLE')

# En logging
logger = logging.getLogger(f'bot-{BOT_INSTANCE_ID}')

# En notificaciones al admin
async def cita_disponible_handler(dates):
    logger.warning(f"🎯 [{BOT_INSTANCE_ID}] CITA DISPONIBLE: {dates}")
    # ... resto del código
```

### En `queue_manager.py`, añadir lock distribuido:

```python
def get_next_user(self):
    """Obtener siguiente usuario (con lock distribuido para evitar colisiones)"""
    # Usar SELECT FOR UPDATE para lock a nivel DB
    user_id = db.execute("""
        SELECT user_id FROM queue
        WHERE status = 'waiting'
        ORDER BY position ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    """)
    return user_id
```

---

## 📋 Paso 3: Ventajas del sistema

### ✅ Redundancia
- Si 1 bot falla, otros 2 siguen funcionando
- Si 1 región tiene lag, otras compensan

### ✅ Velocidad
- 15,000 checks/segundo combinados (3x5000)
- 216 horarios probados en paralelo (3x72)
- Siempre hay 1 bot cerca del servidor español

### ✅ Load Balancing
- Telegram distribuye updates entre los 3 bots
- PostgreSQL maneja la sincronización automáticamente

---

## 📊 Costo vs Beneficio

| Setup | Checks/seg | Horarios | Costo/mes | Beneficio |
|-------|------------|----------|-----------|-----------|
| 1 bot | 5,000 | 72 | $7 | ⭐⭐⭐⭐ |
| 3 bots | 15,000 | 216 | $21 | ⭐⭐⭐⭐⭐ |

---

## 🔧 Deploy Rápido

```bash
# En cada instancia de Render, configurar:
1. Mismo repositorio
2. Misma base de datos PostgreSQL
3. Variable BOT_INSTANCE_ID diferente
4. Región geográfica diferente
```

---

## ⚠️ Consideraciones

### PostgreSQL
- Render Free Tier solo permite 1 DB
- Necesitas upgrade a Postgres Starter ($7/mo) para soportar 3 conexiones simultáneas
- **TOTAL**: $21 (3 bots) + $7 (DB) = **$28/mes**

### Telegram API
- 1 solo bot token
- Los 3 bots procesan updates en paralelo (ok según docs de Telegram)

### Rate Limiting
- Con 3 IPs diferentes, es más difícil que te bloqueen
- Si aún así te bloquean, añadir proxies rotativos

---

## 🚀 ¿Vale la pena?

### SI tienes competencia de otros bots muy rápidos → **SÍ**
- 3x velocidad de detección
- 3x cobertura de horarios
- Imposible perder contra otros bots

### SI solo compites con humanos → **NO**
- Con 1 bot a 5000 checks/seg ya eres suficientemente rápido
- Los humanos tardan 1-5 segundos en reaccionar
- $7/mes es suficiente

---

## 📞 Soporte

Si decides implementar multi-región:
1. Crea las 3 instancias en Render
2. Configura DATABASE_URL (mismo para los 3)
3. Deploy automático
4. Verifica en logs que los 3 están activos

**¡Los 3 bots trabajarán juntos como un solo sistema!** 🌐🔥
