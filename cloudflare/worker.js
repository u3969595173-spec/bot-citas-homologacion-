// 🌐 Cloudflare Worker - Monitor Ultra-Rápido
// Deploy: wrangler deploy worker.js

// Configuración
const CONFIG = {
  baseUrl: 'https://citaprevia.ciencia.gob.es/qmaticwebbooking/rest/schedule',
  serviceId: 'e97539664874283b583f0ff0b25d1e34f0f14e083d59fb10b2dafb76e4544019',
  branchId: '7c2c5344f7ec051bc265995282e38698f770efab83ed9de0f9378d102f700630',
  customSlotLength: 10,
  checkInterval: 200, // 200ms = 5 checks/segundo por worker
  webhookUrl: '', // URL del bot Python para notificar
};

// 🔥 IP Hardcoded (bypass DNS)
const API_IP = '5.2.28.16';

// Estado en memoria (Durable Object después)
let lastCheck = null;
let checksCount = 0;

// Worker principal
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        checks: checksCount,
        lastCheck: lastCheck,
        edge: request.cf?.colo || 'unknown', // Datacenter actual
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    // Endpoint de monitoring continuo
    if (url.pathname === '/monitor') {
      return handleMonitor(request, env);
    }
    
    // Endpoint para reservar (recibe datos del bot Python)
    if (url.pathname === '/reserve' && request.method === 'POST') {
      const data = await request.json();
      return handleReserve(data, env);
    }
    
    return new Response('CitasBot Edge Worker', { status: 200 });
  },
  
  // Scheduled event (ejecutar cada 200ms)
  async scheduled(event, env, ctx) {
    ctx.waitUntil(checkAvailability(env));
  }
};

// 🔍 Función de monitoring
async function checkAvailability(env) {
  try {
    checksCount++;
    
    // Construir URL de la API
    const url = `${CONFIG.baseUrl}/branches/${CONFIG.branchId}/dates;servicePublicId=${CONFIG.serviceId};customSlotLength=${CONFIG.customSlotLength}`;
    
    // ⚡ Fetch ultra-rápido (edge cerca de España)
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
      },
      // Usar IP directa (bypass DNS)
      cf: {
        resolveOverride: API_IP,
        cacheTtl: 0, // No cachear
      }
    });
    
    if (!response.ok) {
      lastCheck = new Date().toISOString();
      return;
    }
    
    const dates = await response.json();
    lastCheck = new Date().toISOString();
    
    // 🎯 Si hay citas disponibles, notificar al bot Python
    if (dates && dates.length > 0) {
      console.log('🎯 CITA DISPONIBLE:', dates);
      
      // Notificar webhook
      if (CONFIG.webhookUrl) {
        await fetch(CONFIG.webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: 'CITA_DISPONIBLE',
            dates: dates,
            timestamp: new Date().toISOString(),
            edge: 'cloudflare'
          })
        });
      }
    }
    
  } catch (error) {
    console.error('Error checking:', error);
  }
}

// 🚀 Función de reserva (POST desde bot Python)
async function handleReserve(data, env) {
  try {
    const { userData, date, time } = data;
    
    // Construir payload
    const [firstName, ...lastNameParts] = userData.nombre.split(' ');
    const lastName = lastNameParts.join(' ');
    
    const payload = {
      services: [{ publicId: CONFIG.serviceId }],
      branch: { publicId: CONFIG.branchId },
      customer: {
        firstName: firstName,
        lastName: lastName,
        email: userData.email,
        phone: userData.phone,
        identificationNumber: userData.document
      },
      customSlotLength: CONFIG.customSlotLength,
      start: `${date}T${time}`
    };
    
    // POST ultra-rápido desde edge
    const url = `${CONFIG.baseUrl}/appointments`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
      cf: {
        resolveOverride: API_IP,
      }
    });
    
    if (!response.ok) {
      return new Response(JSON.stringify({
        success: false,
        error: `HTTP ${response.status}`
      }), { 
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    const result = await response.json();
    
    return new Response(JSON.stringify({
      success: true,
      confirmation: result.publicId,
      data: result
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Endpoint de monitoring continuo
async function handleMonitor(request, env) {
  // Verificar disponibilidad inmediatamente
  await checkAvailability(env);
  
  return new Response(JSON.stringify({
    checked: true,
    timestamp: new Date().toISOString(),
    checksCount: checksCount
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}
