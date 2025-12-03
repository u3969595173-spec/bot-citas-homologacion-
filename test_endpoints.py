#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para encontrar el endpoint correcto de POST appointments
"""

import asyncio
import httpx
import ssl
import json
from config import BRANCH_ID, SERVICE_ID, CUSTOM_SLOT_LENGTH

# Configurar SSL con legacy renegotiation
ssl_context = ssl.create_default_context()
ssl_context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

BASE_URL = "https://citaprevia.ciencia.gob.es/qmaticwebbooking"

# Lista de endpoints posibles para probar
ENDPOINTS_TO_TEST = [
    # Variaciones con /rest/schedule
    "/rest/schedule/appointments",
    "/rest/schedule/appointment",
    "/rest/schedule/reserve",
    "/rest/schedule/book",
    "/rest/schedule/booking",
    
    # Variaciones con /rest solamente
    "/rest/appointments",
    "/rest/appointment",
    "/rest/reserve",
    "/rest/book",
    "/rest/booking",
    
    # Con branch ID
    f"/rest/schedule/branches/{BRANCH_ID}/appointments",
    f"/rest/schedule/branches/{BRANCH_ID}/reserve",
    f"/rest/schedule/branches/{BRANCH_ID}/book",
    
    # Otros patrones comunes
    "/rest/api/appointments",
    "/rest/v1/appointments",
    "/rest/schedule/services/appointments",
]

# Payload de prueba (datos ficticios)
TEST_PAYLOAD = {
    "services": [{"publicId": SERVICE_ID}],
    "branch": {"publicId": BRANCH_ID},
    "customer": {
        "firstName": "Test",
        "lastName": "User",
        "email": "test@example.com",
        "phone": "+34600000000",
        "identificationNumber": "12345678Z"
    },
    "start": "2025-12-18T13:50",
    "customSlotLength": CUSTOM_SLOT_LENGTH
}

async def test_endpoint(client: httpx.AsyncClient, endpoint: str) -> dict:
    """Probar un endpoint específico"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = await client.post(
            url,
            json=TEST_PAYLOAD,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=5.0
        )
        
        status = response.status_code
        result = {
            "endpoint": endpoint,
            "status": status,
            "success": status < 400,
            "response": response.text[:200] if status != 404 else "Not Found"
        }
        
        # Mostrar resultado inmediatamente
        if status != 404:
            print(f"✅ {endpoint} → {status}")
            if status < 400:
                print(f"   RESPUESTA: {response.text[:500]}")
        else:
            print(f"❌ {endpoint} → 404")
            
        return result
        
    except Exception as e:
        print(f"⚠️  {endpoint} → ERROR: {str(e)[:100]}")
        return {
            "endpoint": endpoint,
            "status": "error",
            "success": False,
            "response": str(e)
        }

async def main():
    """Probar todos los endpoints"""
    print("🔍 Probando endpoints posibles para POST appointments...\n")
    
    async with httpx.AsyncClient(
        verify=ssl_context,
        http2=True,
        timeout=10.0
    ) as client:
        
        results = []
        for endpoint in ENDPOINTS_TO_TEST:
            result = await test_endpoint(client, endpoint)
            results.append(result)
            await asyncio.sleep(0.1)  # Pequeño delay entre requests
        
        # Resumen
        print("\n" + "="*60)
        print("📊 RESUMEN DE RESULTADOS")
        print("="*60)
        
        successful = [r for r in results if r.get("success")]
        if successful:
            print("\n✅ ENDPOINTS QUE FUNCIONAN:")
            for r in successful:
                print(f"   • {r['endpoint']} → {r['status']}")
        else:
            print("\n❌ NINGÚN ENDPOINT FUNCIONÓ")
            print("\n💡 SIGUIENTE PASO:")
            print("   1. Abre DevTools en el navegador (F12)")
            print("   2. Ve a la pestaña Network → Fetch/XHR")
            print("   3. Intenta hacer una reserva en la web oficial")
            print("   4. Copia el endpoint POST que aparezca")

if __name__ == "__main__":
    asyncio.run(main())
