# 🔄 Proxies Rotativos - Evitar Rate Limiting

## 🎯 ¿Cuándo usar proxies?

### ✅ Usa proxies SI:
- El gobierno te bloquea la IP por hacer 5000 checks/seg
- Recibes errores 429 (Too Many Requests)
- Tu IP queda baneada temporalmente

### ❌ NO necesitas proxies SI:
- El bot funciona sin bloqueos
- No recibes errores 429
- Las citas se detectan correctamente

---

## 📦 Opción 1: Proxies Gratis Rotativos (INSEGURO)

```python
# auto_fill_http_fast.py
import httpx
from itertools import cycle

FREE_PROXIES = [
    "http://proxy1.com:8080",
    "http://proxy2.com:8080",
    "http://proxy3.com:8080",
    # Lista de https://free-proxy-list.net/
]

class FastHTTPAutoFiller:
    def __init__(self):
        self.proxy_pool = cycle(FREE_PROXIES)
        self.client = None  # Se crea por petición
    
    async def _create_appointment(self, user_data, date, time):
        # Rotar proxy cada petición
        proxy = next(self.proxy_pool)
        
        async with httpx.AsyncClient(
            proxy=proxy,
            timeout=httpx.Timeout(0.4, connect=0.1),
            verify=False
        ) as client:
            response = await client.post(url, json=payload)
            return response.json()
```

**Pros**: Gratis  
**Contras**: Lentos, poco confiables, pueden estar comprometidos

---

## 💰 Opción 2: SmartProxy (RECOMENDADO)

### Paso 1: Crear cuenta
- Web: https://smartproxy.com
- Plan: Residential ($8/mo por 2GB)
- Suficiente para ~1M peticiones

### Paso 2: Obtener credenciales
```
Username: user-XXXXXX
Password: YYYYYY
Proxy: gate.smartproxy.com:7000
```

### Paso 3: Configurar en el bot

```python
# config.py
SMARTPROXY_USER = "user-XXXXXX"
SMARTPROXY_PASS = "YYYYYY"
SMARTPROXY_HOST = "gate.smartproxy.com:7000"

USE_PROXY = True  # Activar/desactivar proxies
```

```python
# auto_fill_http_fast.py
import os

class FastHTTPAutoFiller:
    def __init__(self):
        # Configurar proxy si está activado
        proxy = None
        if os.getenv('USE_PROXY', 'False') == 'True':
            user = os.getenv('SMARTPROXY_USER')
            pwd = os.getenv('SMARTPROXY_PASS')
            host = os.getenv('SMARTPROXY_HOST')
            proxy = f"http://{user}:{pwd}@{host}"
        
        self.client = httpx.AsyncClient(
            proxy=proxy,  # ← SmartProxy rotativo
            timeout=httpx.Timeout(0.4, connect=0.1),
            limits=httpx.Limits(max_connections=200),
            verify=False
        )
```

### Paso 4: Variables de entorno en Render
```
SMARTPROXY_USER=user-XXXXXX
SMARTPROXY_PASS=YYYYYY
SMARTPROXY_HOST=gate.smartproxy.com:7000
USE_PROXY=True
```

**Ventajas**:
- Rotan automáticamente IP cada petición
- IPs residenciales (parecen usuarios reales)
- Confiables y rápidos

---

## 🌐 Opción 3: BrightData (PREMIUM)

Más caro pero más rápido:

```
Plan: Residential Proxies
Precio: $15/mo por 1GB
Ventaja: Más rápido, más países, más confiable
```

Configuración idéntica a SmartProxy.

---

## 📊 Comparativa

| Servicio | Precio/mes | Velocidad | Confiabilidad | Recomendado |
|----------|-----------|-----------|---------------|-------------|
| Gratis | $0 | ⭐ | ⭐ | ❌ NO |
| SmartProxy | $8 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ SÍ |
| BrightData | $15 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 💰 SI $ no problema |

---

## 🎯 ¿Cuál elegir?

### Para tu caso (España):
1. **Primero prueba SIN proxies** → Si funciona, no gastes dinero
2. **Si te bloquean** → SmartProxy ($8/mo)
3. **Si necesitas MÁS velocidad** → Multi-región (3 bots) + SmartProxy

---

## ⚡ Performance con Proxies

| Sin Proxy | Con SmartProxy | Diferencia |
|-----------|----------------|------------|
| 174ms | ~250ms | +76ms |

**Conclusión**: Los proxies añaden latencia (~70ms), pero **evitan bloqueos**.

---

## 🔧 Implementación Rápida

### 1. Registrarse en SmartProxy
https://smartproxy.com → Sign Up → Plan Residential

### 2. Añadir código al bot
```python
# En auto_fill_http_fast.py (línea ~20)
proxy = None
if os.getenv('USE_PROXY') == 'True':
    proxy = f"http://{os.getenv('SMARTPROXY_USER')}:{os.getenv('SMARTPROXY_PASS')}@{os.getenv('SMARTPROXY_HOST')}"

self.client = httpx.AsyncClient(
    proxy=proxy,  # ← Aquí
    ...
)
```

### 3. Variables en Render
```
USE_PROXY=True
SMARTPROXY_USER=tu_user
SMARTPROXY_PASS=tu_pass
SMARTPROXY_HOST=gate.smartproxy.com:7000
```

### 4. Deploy
```bash
git add -A
git commit -m "feat: Soporte para proxies rotativos"
git push origin main
```

---

## 📞 Soporte

**¿Necesitas proxies?**
- Revisa logs en Render
- Si ves errores 429 o bloqueos → Activa proxies
- Si funciona normal → NO necesitas proxies

**Ahorra dinero**: Solo activa proxies si es necesario.

---

**Actualizado**: Dec 4, 2025  
**Costo**: $0-15/mes según necesidad
