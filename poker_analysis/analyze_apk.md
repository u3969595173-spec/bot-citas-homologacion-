# Análisis de Seguridad APK - Guía

## Paso 1: Extraer la APK
```bash
# Desde dispositivo Android
adb pull /data/app/com.poker.app/base.apk poker.apk
```

## Paso 2: Decompilación
```bash
# Instalar APKTool (Windows)
# Descargar de: https://ibotpeaches.github.io/Apktool/

# Desempaquetar APK
apktool d poker.apk -o poker_extracted

# Ver estructura:
# - AndroidManifest.xml
# - res/ (recursos)
# - smali/ (código)
```

## Paso 3: Decompilación a Java
```bash
# JADX (más fácil)
# Descargar: https://github.com/skylot/jadx

jadx poker.apk -d poker_decompiled

# Ahora tienes código Java legible en poker_decompiled/
```

## Paso 4: Buscar vulnerabilidades

### A) Verificar si usa HTTPS
```bash
# Buscar en AndroidManifest.xml
grep -i "usesCleartextTraffic" poker_extracted/AndroidManifest.xml

# Si dice "true" → NO usa HTTPS (vulnerable)
```

### B) Buscar URLs hardcodeadas
```bash
# En carpeta decompilada
grep -r "http://" poker_decompiled/
grep -r "ws://" poker_decompiled/  # WebSockets sin SSL
```

### C) Certificate Pinning
```bash
# Buscar en código
grep -r "CertificatePinner" poker_decompiled/
grep -r "TrustManager" poker_decompiled/

# Si NO existe → más fácil interceptar tráfico
```

## Paso 5: Interceptar tráfico (si no hay HTTPS/pinning)

### Opción A: mitmproxy (PC como proxy)
```bash
# Instalar mitmproxy
pip install mitmproxy

# Iniciar proxy
mitmproxy -p 8080

# En Android:
# Settings → WiFi → Modify Network → Manual Proxy
# Host: IP de tu PC
# Port: 8080
```

### Opción B: Packet Capture (app Android)
```
1. Instalar "Packet Capture" desde Play Store
2. Iniciar captura
3. Abrir app de poker
4. Ver requests/responses en tiempo real
```

## Paso 6: Analizar protocolo

### Buscar en tráfico:
- Endpoints API (ej: `/api/game/state`)
- Formato de datos (JSON, protobuf, custom)
- Tokens/autenticación
- **Datos de cartas** (buscar patrones como "cards", "hand", "deck")

### Ejemplo de request vulnerable:
```json
GET /api/game/12345/state
Response:
{
  "pot": 500,
  "players": [
    {"id": 1, "cards": ["As", "Kh"], "stack": 1000},  ← VULNERABLE
    {"id": 2, "cards": ["??", "??"], "stack": 800}    ← Oculto
  ]
}
```

## ⚠️ Señales de vulnerabilidad:

✅ **Fácil de explotar:**
- usesCleartextTraffic="true"
- HTTP sin HTTPS
- Sin certificate pinning
- Cartas visibles en respuesta JSON

❌ **Difícil/imposible:**
- HTTPS con pinning
- Datos encriptados custom
- Cartas solo en servidor
- Obfuscación fuerte (ProGuard/R8)

## Herramientas automáticas:

### MobSF (Mobile Security Framework)
```bash
# Análisis automático completo
docker pull opensecurity/mobile-security-framework-mobsf
docker run -it -p 8000:8000 opensecurity/mobile-security-framework-mobsf

# Subir APK en http://localhost:8000
# Te da reporte completo de vulnerabilidades
```

## Siguiente paso:

Si encuentras que:
1. **Usa HTTP** → Interceptar con mitmproxy
2. **HTTPS sin pinning** → Bypass con Frida
3. **Cartas en respuesta** → Parsear JSON
4. **Todo seguro** → No es posible sin hackear servidor
