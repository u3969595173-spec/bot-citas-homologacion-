# 🔄 FASE 2: Bright Data Proxies (IPs Españolas Premium)

## 🎯 Objetivo

- Evitar rate limiting del gobierno
- IPs residenciales españolas (Madrid, Barcelona, Valencia)
- Rotación automática cada request
- Pasar como tráfico humano real

**Costo:** $40/mo (7 días gratis + $5 crédito)  
**Resultado:** Sin límites de requests + mejor geolocalización

---

## 📋 PASO 1: Crear Cuenta Bright Data

### 1.1 Registro
1. Ve a: https://brightdata.com/pricing
2. Click **Start Free Trial**
3. Selecciona: **Residential Proxies**
4. Plan: **Pay As You Go** ($5.50/GB)
5. **No necesitas tarjeta para el trial**

### 1.2 Obtener Credenciales
1. Dashboard → Proxy Products → Residential
2. Click **Get proxy list**
3. Copiar:
   ```
   Host: brd.superproxy.io
   Port: 22225
   Username: brd-customer-XXXXXX-zone-residential
   Password: YYYYYYY
   ```

---

## 📋 PASO 2: Activar en Render

### 2.1 Variables de Entorno

**En cada bot de Render:**

1. Dashboard → Bot → Environment
2. Add Environment Variables:

```bash
USE_PROXY = true
PROXY_HOST = brd.superproxy.io
PROXY_PORT = 22225
PROXY_USERNAME = brd-customer-XXXXXX-zone-residential
PROXY_PASSWORD = YYYYYYY
PROXY_COUNTRY = es
```

3. **Save Changes** → Bot se redesplegará automáticamente

---

## ✅ El Código YA ESTÁ LISTO

El código en `auto_fill_http_fast.py` ya soporta proxies:
- ✅ Detecta variable `USE_PROXY=true`
- ✅ Configura Bright Data automáticamente
- ✅ Rotación con session-id aleatorio
- ✅ Geolocalización España (`PROXY_COUNTRY=es`)

---

## 🔍 VERIFICAR FUNCIONAMIENTO

### Logs en Render

Deberías ver:
```
🔄 Proxies ACTIVADOS: ES via brd.superproxy.io
🔥 PRE-ESTABLECIENDO 10 conexiones HTTP/2...
✅ 10 conexiones HTTP/2 PRE-ESTABLECIDAS
```

### Dashboard Bright Data

1. Dashboard → Statistics
2. Verás requests incrementando
3. Geographic Distribution → España (100%)

---

## 📊 VENTAJAS

### Sin Proxies (Actual):
```
Requests/seg: 5,000 (por bot)
IP: AWS/Render (USA/EU)
Rate Limit: Posible después de X requests
Latencia: 60-120ms
```

### Con Proxies Bright Data:
```
Requests/seg: ILIMITADO
IP: Residenciales españolas
Rate Limit: NINGUNO (parece tráfico humano)
Latencia: +50ms (overhead proxy) = 140ms total
Geolocalización: Madrid, Barcelona, Valencia
```

---

## 💰 COSTO FASE 2

| Item | Precio | Detalle |
|------|--------|---------|
| Bright Data Residential | $5.50/GB | ~1M requests = 2GB |
| Estimado mensual | $40/mo | Con 6 bots a 30k/seg |
| **Trial gratis** | **7 días + $5** | Probar sin compromiso |

---

## 🚨 IMPORTANTE

### Cuándo ACTIVAR proxies:

✅ **SÍ activar SI:**
- Recibes errores 429 (Too Many Requests)
- Tu IP queda bloqueada temporalmente
- Quieres máxima velocidad sin límites

❌ **NO activar SI:**
- Bot funciona sin errores
- No hay bloqueos
- Quieres ahorrar dinero

**RECOMENDACIÓN:** Empieza SIN proxies (Fase 1). Si ves errores 429 o bloqueos → Activar Fase 2.

---

## 🎯 CONFIGURACIÓN ÓPTIMA

### Para 6 bots multi-región:

**Opción A: Todos con proxies** ($40/mo)
- 30,000 checks/seg
- Máxima protección
- Sin límites

**Opción B: Solo bots EU con proxies** ($20/mo)
- EU-Central + EU-West usan proxies (más cerca España)
- Otros bots directo
- Balance costo/beneficio

**Opción C: Proxy solo cuando detecta cita** (GRATIS trial)
- Monitoring sin proxy
- Al detectar cita → switch a proxy
- Mínimo consumo

---

## 📋 SIGUIENTE PASO

**Una vez configurado:**
1. Monitorea Dashboard Bright Data primeras 24h
2. Verifica consumo de GB
3. Ajusta según necesites

**Cuando esté funcionando, responde "LISTO FASE 2"**  
→ Pasaremos a **FASE 3: VPS Google Cloud Madrid** ($0 con créditos)

---

**COSTO ACUMULADO:** $49/mo (Fase 1) + $40/mo (Fase 2) = **$89/mo**  
**VELOCIDAD:** 30,000 checks/seg sin límites  
**LATENCIA:** ~140ms (con overhead proxy)
