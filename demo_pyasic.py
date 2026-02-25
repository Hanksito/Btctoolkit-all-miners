"""
demo_pyasic.py
==============
Script de demostración de pyasic.
Muestra cómo escanear la red, obtener datos de un miner por IP,
y trabajar con MinerData y MinerConfig.

Uso:
    .venv\Scripts\python demo_pyasic.py
"""

import asyncio
from pyasic import get_miner, settings
from pyasic.network import MinerNetwork
from pyasic.data import MinerData


# ─── Configuración de credenciales ────────────────────────────────────────────
# Cambia estos valores según tu red y contraseñas
MINER_IP = "192.168.1.75"          # IP de un miner específico
NETWORK_SUBNET = "192.168.1.50/24" # Subred a escanear (cambia la IP base)

# Contraseñas por defecto (puedes cambiarlas aquí en lugar de en el miner)
settings.update("default_antminer_web_password", "root")
settings.update("default_whatsminer_rpc_password", "admin")


# ─── 1. Obtener un miner por IP ────────────────────────────────────────────────
async def demo_get_miner_by_ip():
    print("\n=== 1. Obtener miner por IP ===")
    miner = await get_miner(MINER_IP)
    print(f"  Miner encontrado: {miner}")
    print(f"  Tipo: {type(miner).__name__}")
    return miner


# ─── 2. Obtener datos del miner ────────────────────────────────────────────────
async def demo_get_miner_data(miner):
    print("\n=== 2. Datos del miner ===")
    data: MinerData = await miner.get_data()
    print(f"  IP:         {data.ip}")
    print(f"  Modelo:     {data.model}")
    print(f"  Hashrate:   {data.hashrate} TH/s")
    print(f"  Temp avg:   {data.temperature_avg} °C")
    print(f"  Uptime:     {data.uptime} s")
    print(f"  Workers:    {data.expected_hashboards} hashboards")
    # Ver todos los campos disponibles
    print("\n  Todos los campos (como dict):")
    for k, v in data.as_dict().items():
        print(f"    {k}: {v}")
    return data


# ─── 3. Obtener configuración del miner ───────────────────────────────────────
async def demo_get_config(miner):
    print("\n=== 3. Configuración del miner ===")
    config = await miner.get_config()
    print(f"  Config: {config}")
    return config


# ─── 4. Escanear la red completa ─────────────────────────────────────────────
async def demo_scan_network():
    print(f"\n=== 4. Escanear red {NETWORK_SUBNET} ===")
    print("  (puede tardar hasta 30 segundos...)")
    network = MinerNetwork.from_subnet(NETWORK_SUBNET)
    miners = await network.scan()
    print(f"  Miners encontrados: {len(miners)}")
    for m in miners:
        print(f"    - {m.ip}: {type(m).__name__}")
    return miners


# ─── 5. Demo de MinerData: operar con múltiples datos ────────────────────────
async def demo_miner_data_operations():
    print("\n=== 5. Operaciones con MinerData ===")
    # Crear datos de ejemplo (sin miner real)
    d1 = MinerData("192.168.1.1")
    d2 = MinerData("192.168.1.2")
    # Se pueden sumar para agregar y luego dividir para promediar
    datos = [d1, d2]
    promedio = sum(datos, start=MinerData("0.0.0.0")) / len(datos)
    print(f"  Promedio calculado para {len(datos)} miners: {promedio.ip}")
    print(f"  Hashrate promedio: {promedio.hashrate} TH/s")


# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 60)
    print("           DEMO DE pyasic")
    print("=" * 60)

    # Operaciones que no necesitan miner real
    await demo_miner_data_operations()

    # Descomenta las siguientes líneas si tienes miners reales en tu red:
    # miner = await demo_get_miner_by_ip()
    # if miner:
    #     await demo_get_miner_data(miner)
    #     await demo_get_config(miner)
    #
    # await demo_scan_network()

    print("\n✅ Demo completada. Para usar con miners reales, edita MINER_IP y descomenta las funciones.")


if __name__ == "__main__":
    asyncio.run(main())
