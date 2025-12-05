#!/bin/bash
# 🚀 Script de Deploy Automático - Google Cloud Madrid
# Ejecutar: bash deploy_gcloud.sh

set -e  # Exit on error

echo "🚀 DEPLOY BOT EN GOOGLE CLOUD MADRID"
echo "======================================"
echo ""

# Variables
PROJECT_ID="citasbot-project"
INSTANCE_NAME="citasbot-madrid"
ZONE="europe-southwest1-a"  # Madrid
MACHINE_TYPE="e2-medium"  # 2 vCPU, 4GB RAM
DISK_SIZE="20GB"

echo "📋 Configuración:"
echo "  - Proyecto: $PROJECT_ID"
echo "  - Instancia: $INSTANCE_NAME"
echo "  - Zona: $ZONE (Madrid)"
echo "  - Tipo: $MACHINE_TYPE"
echo ""

# 1. Crear instancia
echo "1️⃣ Creando VM en Madrid..."
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20241119,mode=rw,size=$DISK_SIZE,type=pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=app=citasbot,env=production \
    --reservation-affinity=any

echo "✅ VM creada"
echo ""

# 2. Esperar a que arranque
echo "2️⃣ Esperando a que VM esté lista..."
sleep 30

# 3. Obtener IP externa
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "📍 IP Externa: $EXTERNAL_IP"
echo ""

# 4. Copiar archivos del bot
echo "3️⃣ Copiando código del bot..."
gcloud compute scp --recurse --zone=$ZONE \
    --project=$PROJECT_ID \
    ../CitasBot $INSTANCE_NAME:~/

echo "✅ Código copiado"
echo ""

# 5. Instalar dependencias y configurar
echo "4️⃣ Instalando dependencias..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    sudo apt-get update && \
    sudo apt-get install -y python3-pip python3-venv && \
    cd ~/CitasBot && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt
"

echo "✅ Dependencias instaladas"
echo ""

# 6. Configurar variables de entorno
echo "5️⃣ Configurando variables de entorno..."
read -p "TELEGRAM_BOT_TOKEN: " BOT_TOKEN
read -p "ADMIN_USER_ID: " ADMIN_ID
read -p "DATABASE_URL: " DB_URL

gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    cat > ~/CitasBot/.env << EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
ADMIN_USER_ID=$ADMIN_ID
DATABASE_URL=$DB_URL
BOT_INSTANCE_ID=GCLOUD-MADRID
USE_PROXY=false
EOF
"

echo "✅ Variables configuradas"
echo ""

# 7. Crear servicio systemd
echo "6️⃣ Creando servicio systemd..."
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    sudo tee /etc/systemd/system/citasbot.service > /dev/null << EOF
[Unit]
Description=CitasBot Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/CitasBot
Environment=PATH=/home/$USER/CitasBot/venv/bin
ExecStart=/home/$USER/CitasBot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload && \
    sudo systemctl enable citasbot && \
    sudo systemctl start citasbot
"

echo "✅ Servicio creado y arrancado"
echo ""

# 8. Verificar estado
echo "7️⃣ Verificando estado..."
sleep 5
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    sudo systemctl status citasbot --no-pager
"

echo ""
echo "🎉 DEPLOY COMPLETADO"
echo "===================="
echo ""
echo "📍 IP: $EXTERNAL_IP"
echo "🌍 Región: Madrid (europe-southwest1)"
echo "⚡ Latencia esperada: <10ms a España"
echo ""
echo "📋 Comandos útiles:"
echo "  Ver logs:    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE -- sudo journalctl -u citasbot -f"
echo "  Reiniciar:   gcloud compute ssh $INSTANCE_NAME --zone=$ZONE -- sudo systemctl restart citasbot"
echo "  Detener:     gcloud compute ssh $INSTANCE_NAME --zone=$ZONE -- sudo systemctl stop citasbot"
echo "  SSH directo: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
echo ""
