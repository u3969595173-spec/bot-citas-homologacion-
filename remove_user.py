"""Script para eliminar usuario de la cola"""
from queue_manager import CitasQueue
import asyncio

async def remove_user():
    queue = CitasQueue()
    user_id_to_remove = 6412728727  # Eloy jesus
    
    if user_id_to_remove in queue.usuarios_activos:
        del queue.usuarios_activos[user_id_to_remove]
        await queue.save_queue()
        print(f" Usuario {user_id_to_remove} eliminado de la cola")
        print(f" Usuarios restantes: {list(queue.usuarios_activos.keys())}")
    else:
        print(f" Usuario {user_id_to_remove} no está en la cola")
        print(f" Usuarios actuales: {list(queue.usuarios_activos.keys())}")

asyncio.run(remove_user())
