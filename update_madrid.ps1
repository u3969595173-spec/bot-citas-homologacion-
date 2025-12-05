$gcloudCmd = Get-Command gcloud -ErrorAction SilentlyContinue
if (-not $gcloudCmd) {
    $env:Path += ";C:\Users\leand\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin"
}

Write-Host "Actualizando bot de Madrid..."
gcloud compute ssh citasbot-madrid --zone=europe-southwest1-a --command="cd CitasBot && pkill -f 'python3 main.py' ; git pull origin main && python3 main.py > bot.log 2>&1 & sleep 2 && tail -20 bot.log"
