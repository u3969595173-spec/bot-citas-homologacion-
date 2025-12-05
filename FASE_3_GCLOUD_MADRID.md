# ☁️ FASE 3: Google Cloud VPS Madrid (Latencia <10ms)

## 🎯 Objetivo

- VPS físico en Madrid, España
- Latencia <10ms al servidor del gobierno
- $300 crédito gratis (90 días)
- 10,000+ checks/segundo adicionales
- Control total del servidor

**Costo:** $0 primeros 90 días (luego ~$20/mo)  
**Resultado:** 40,000 checks/seg total (30k Render + 10k Madrid)

---

## 📋 PASO 1: Crear Cuenta Google Cloud

### 1.1 Registro ($300 Gratis)

1. Ve a: https://cloud.google.com/free
2. Click **Start Free**
3. Necesitas:
   - Cuenta Google
   - Tarjeta de crédito (NO se cobra durante trial)
   - Verificación de identidad

4. Activa **$300 crédito** válido 90 días

### 1.2 Crear Proyecto

1. Console → Select Project → **New Project**
2. Nombre: `citasbot-project`
3. Click **Create**

---

## 📋 PASO 2: Instalar Google Cloud CLI (tu PC)

### Windows (PowerShell):

```powershell
# Descargar installer
Invoke-WebRequest https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe -OutFile gcloud-installer.exe

# Ejecutar
.\gcloud-installer.exe

# Inicializar (después de instalar)
gcloud init
```

### Configurar:

```bash
# Login
gcloud auth login

# Seleccionar proyecto
gcloud config set project citasbot-project

# Verificar
gcloud config list
```

---

## 📋 PASO 3: Deploy Automático

### 3.1 Usar Script (RECOMENDADO)

```bash
# En tu terminal (Git Bash o WSL)
cd C:/CitasBot
bash deploy_gcloud.sh
```

**El script hace:**
1. Crea VM en Madrid (europe-southwest1)
2. Instala Python + dependencias
3. Configura variables de entorno
4. Crea servicio systemd
5. Inicia bot automáticamente

### 3.2 Te pedirá:

```
TELEGRAM_BOT_TOKEN: <pegar_tu_token>
ADMIN_USER_ID: <tu_user_id>
DATABASE_URL: <copiar_de_render_postgresql>
```

---

## 📋 PASO 4: Deploy Manual (Alternativa)

### 4.1 Crear VM

```bash
gcloud compute instances create citasbot-madrid \
    --zone=europe-southwest1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --labels=app=citasbot
```

### 4.2 Conectar SSH

```bash
gcloud compute ssh citasbot-madrid --zone=europe-southwest1-a
```

### 4.3 Instalar Dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python
sudo apt install -y python3-pip python3-venv git

# Clonar repo
git clone https://github.com/u3969595173-spec/bot-citas-homologacion-.git CitasBot
cd CitasBot

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4.4 Configurar Variables

```bash
# Crear archivo .env
nano .env
```

```bash
TELEGRAM_BOT_TOKEN=tu_token
ADMIN_USER_ID=tu_user_id
DATABASE_URL=postgresql://...
BOT_INSTANCE_ID=GCLOUD-MADRID
USE_PROXY=false
```

### 4.5 Crear Servicio

```bash
sudo nano /etc/systemd/system/citasbot.service
```

```ini
[Unit]
Description=CitasBot Telegram Bot
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/home/tu_usuario/CitasBot
Environment=PATH=/home/tu_usuario/CitasBot/venv/bin
ExecStart=/home/tu_usuario/CitasBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4.6 Iniciar Servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable citasbot
sudo systemctl start citasbot

# Ver logs
sudo journalctl -u citasbot -f
```

---

## ✅ VERIFICAR FUNCIONAMIENTO

### 1. Logs del Servicio

```bash
sudo journalctl -u citasbot -f
```

Deberías ver:
```
🔥 PRE-ESTABLECIENDO 10 conexiones HTTP/2...
✅ 10 conexiones HTTP/2 PRE-ESTABLECIDAS
[GCLOUD-MADRID] ✓ Check #5000 - Sin citas disponibles
```

### 2. Test de Latencia

```bash
# Desde la VM
ping citaprevia.ciencia.gob.es
```

**Resultado esperado:** 5-15ms (vs 60-120ms desde Render)

### 3. Telegram

Envía `/status` → Deberías ver checks incrementando

---

## 📊 COMPARATIVA LATENCIA

```
Servidor          Ubicación       Ping      Ventaja
──────────────────────────────────────────────────────
Render Oregon     USA West        ~100ms    Base
Render Frankfurt  Alemania        ~60ms     40% mejor
GCloud Madrid     ESPAÑA          ~8ms      92% mejor ⭐
```

---

## 🔧 GESTIÓN DEL SERVIDOR

### Ver Logs en Tiempo Real

```bash
gcloud compute ssh citasbot-madrid --zone=europe-southwest1-a -- sudo journalctl -u citasbot -f
```

### Reiniciar Bot

```bash
gcloud compute ssh citasbot-madrid --zone=europe-southwest1-a -- sudo systemctl restart citasbot
```

### Actualizar Código

```bash
gcloud compute ssh citasbot-madrid --zone=europe-southwest1-a

cd CitasBot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart citasbot
```

### Detener VM (Ahorrar Crédito)

```bash
# Detener (no borra, mantiene IP)
gcloud compute instances stop citasbot-madrid --zone=europe-southwest1-a

# Iniciar de nuevo
gcloud compute instances start citasbot-madrid --zone=europe-southwest1-a
```

### Eliminar VM

```bash
gcloud compute instances delete citasbot-madrid --zone=europe-southwest1-a
```

---

## 💰 COSTO REAL

### Durante Trial (90 días):

```
e2-medium (2 vCPU, 4GB):  ~$25/mo
Disco 20GB SSD:           ~$3/mo
Transferencia:            ~$2/mo
──────────────────────────────────
TOTAL:                    ~$30/mo
CRÉDITO:                  -$300 ($100/mes)
══════════════════════════════════
COSTO REAL:               $0/mo ✨
```

### Después del Trial:

```
OPCIÓN 1: e2-medium       $30/mo  (recomendado)
OPCIÓN 2: e2-small        $15/mo  (básico)
OPCIÓN 3: e2-micro        $8/mo   (mínimo)
```

---

## 🎯 ARQUITECTURA FINAL (Fases 1-3)

```
┌──────────────────────────────────────────────┐
│         PostgreSQL Standard (Render)         │
│           (Coordinación Central)             │
└──────────────────────────────────────────────┘
                    ▲
                    │
    ┌───────────────┼───────────────────┐
    │               │                   │
┌───▼────┐     ┌────▼───┐         ┌────▼───┐
│6 Bots  │     │VPS GCP │         │Proxies │
│Render  │────>│Madrid  │────────>│Bright  │
│30k/sec │     │10k/sec │         │Data    │
└────────┘     └────────┘         └────────┘
   GLOBAL       <10ms ESPAÑA      IPs ESP

TOTAL: 40,000 checks/seg + <10ms latencia
```

---

## 🚨 TROUBLESHOOTING

### Error: "Quota exceeded"
- Solución: Espera 1h o solicita aumento de cuota

### Error: "Permission denied (publickey)"
- Solución: `gcloud compute config-ssh`

### Bot no arranca
```bash
# Ver error exacto
sudo journalctl -u citasbot -n 50 --no-pager

# Verificar permisos
ls -la /home/tu_usuario/CitasBot
```

### PostgreSQL no conecta desde GCloud
- Verificar que DATABASE_URL es accesible públicamente
- Render PostgreSQL debe permitir conexiones externas

---

## 📋 SIGUIENTE PASO

**Una vez Madrid funcione, responde "LISTO FASE 3"**  
→ Pasaremos a **FASE 4: Cloudflare Edge Computing** (código en CDN español)

---

**COSTO ACUMULADO:** 
- Render 6 bots: $49/mo
- Proxies Bright Data: $40/mo  
- GCloud Madrid: $0/mo (trial) → $20/mo después
- **TOTAL: $89/mo** (luego $109/mo)

**VELOCIDAD:** 40,000 checks/seg + <10ms latencia + IPs españolas
