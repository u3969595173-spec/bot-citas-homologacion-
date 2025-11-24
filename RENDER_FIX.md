# 🔧 Solución: Error de Playwright en Render

## ❌ Problema
```
BrowserType.launch: Executable doesn't exist at /opt/render/.cache/ms-playwright/chromium_headless_shell-1194/chrome-linux/headless_shell
```

**Causa:** Los navegadores de Playwright no se instalaron durante el build.

---

## ✅ Solución

### Opción 1: Usar `render.yaml` (Recomendado)

1. **Commit el archivo `render.yaml`** que está en la raíz del proyecto
2. En el dashboard de Render, haz clic en tu servicio
3. Ve a **Settings** → **Build & Deploy**
4. Render detectará automáticamente el `render.yaml`
5. Haz un **Manual Deploy** para forzar rebuild

### Opción 2: Configuración Manual en Dashboard

Si no quieres usar `render.yaml`, configura manualmente:

#### 1. En el Dashboard de Render → Tu Servicio → Settings:

**Build Command:**
```bash
./build.sh
```

**Start Command:**
```bash
python main.py
```

#### 2. Asegúrate de que `build.sh` tenga permisos de ejecución:

En tu repositorio local:
```bash
git update-index --chmod=+x build.sh
git commit -m "Make build.sh executable"
git push
```

#### 3. Variables de Entorno Requeridas:

```
TELEGRAM_BOT_TOKEN=8337512957:AAFcmCb8t14oDuwpzKG7-8Bh_S9Jxeyi1Uw
ADMIN_USER_ID=5901833301
DATABASE_URL=(auto-generado por Render PostgreSQL)
```

---

## 🔍 Verificación Post-Deploy

Después del deploy, revisa los logs de build. Deberías ver:

```
🔧 Instalando dependencias del sistema...
🌐 Instalando dependencias para navegador headless...
📦 Instalando dependencias de Python...
🎭 Instalando navegadores de Playwright...
✅ Verificando instalación de Playwright...
✅ Build completado exitosamente
```

Luego, en los logs del runtime, cuando detecte una cita, debería mostrar:

```
🎯 CITAS DISPONIBLES: [{'date': '2025-12-03'}]
🤖 Iniciando auto-llenado para Leandro Eloy Tamayo Reyes
✅ Fecha 2025-12-03 seleccionada
✅ Reserva completada exitosamente
```

---

## 🚀 Pasos Rápidos (Resumen)

1. **Commit y push los cambios:**
   ```bash
   git add build.sh render.yaml
   git commit -m "Fix: Install Playwright browsers in build"
   git push
   ```

2. **En Render Dashboard:**
   - Settings → Build & Deploy
   - Build Command: `./build.sh`
   - Manual Deploy → **Clear build cache & deploy**

3. **Monitorear logs:**
   - Verifica que `playwright install chromium --with-deps` se ejecute
   - Confirma que no haya errores de instalación

---

## 📝 Notas Importantes

- **Plan requerido:** Standard ($7/mes) - El plan Free no tiene suficiente RAM para Playwright
- **Tiempo de build:** ~5-10 minutos (por instalación de Chromium)
- **Espacio en disco:** Chromium ocupa ~300MB
- **Clear build cache:** Si el problema persiste, limpia la caché de build en Render

---

## 🆘 Si Persiste el Error

Si después de estos pasos aún ves el error:

1. **Verifica que `build.sh` se ejecutó completamente** en los logs de build
2. **Revisa que no haya errores de permisos** en los logs
3. **Aumenta el timeout** de Playwright en `auto_fill.py` (línea 16):
   ```python
   self.timeout = 60000  # 60 segundos
   ```
4. **Contacta soporte de Render** si el problema continúa

---

## ✅ Alternativa: Desactivar Auto-Fill Temporalmente

Si necesitas que el bot funcione YA sin auto-fill:

En `main.py`, comenta la sección de auto-fill y solo envía notificación manual:

```python
# Línea ~45 en main.py - Comentar try de auto-fill
# try:
#     result = await auto_fill_appointment(fill_data, first_date)
#     ...
# except Exception as e:
#     ...

# Ir directo a notificación manual (línea ~99)
mensaje = (
    f"🎯 **¡CITA DISPONIBLE!**\n\n"
    f"📅 Fechas: {', '.join(date_strings)}\n\n"
    # ... resto del mensaje
)
```

Esto hará que el bot solo notifique, sin intentar auto-llenar.
