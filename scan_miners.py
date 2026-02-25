r"""
scan_miners.py
==============
Escanea la red 192.168.1.0/24 y muestra el estado de todos los miners.
Configurado para 12 Antminers (root/root) + 1 Volcminer (root/ltc@dog)

Uso:
    .venv\Scripts\python scan_miners.py
"""

import asyncio
from pyasic import get_miner, settings
from pyasic.network import MinerNetwork
from pyasic.data import MinerData

# ─── Credenciales ─────────────────────────────────────────────────────────────
settings.update("default_antminer_web_password", "root")
settings.update("default_antminer_ssh_password", "root")
settings.update("default_bosminer_web_password", "root")
settings.update("default_bosminer_ssh_password", "root")
settings.update("default_goldshell_web_password", "ltc@dog")


def fmt_hashrate(data: MinerData) -> str:
    """Formatea el hashrate a TH/s independientemente de la unidad interna."""
    hr = data.hashrate
    if hr is None:
        return "N/A"
    # hr es un objeto AlgoHashRate con atributos .rate y .unit
    try:
        rate = float(hr.rate)
        unit = str(hr.unit).upper()
        # Convertir todo a TH/s
        conversions = {
            "H/S": rate / 1e12,
            "KH/S": rate / 1e9,
            "MH/S": rate / 1e6,
            "GH/S": rate / 1e3,
            "TH/S": rate,
            "PH/S": rate * 1e3,
        }
        ths = conversions.get(unit, rate)
        return f"{ths:.2f} TH/s"
    except Exception:
        return str(hr)


# ─── Escaneo y reporte ────────────────────────────────────────────────────────
async def main():
    print("=" * 75)
    print("  🔍  Escaneando red 192.168.1.0/24 — buscando miners...")
    print("=" * 75)

    network = MinerNetwork.from_subnet("192.168.1.125/24")
    miners = await network.scan()

    if not miners:
        print("\n❌ No se encontraron miners. Comprueba la red y las IPs.")
        return

    print(f"\n✅ {len(miners)} miners encontrados. Obteniendo datos...\n")

    # Obtener datos de todos en paralelo
    all_data: list[MinerData] = await asyncio.gather(
        *[miner.get_data() for miner in miners],
        return_exceptions=True
    )

    # ─── Cabecera de tabla ────────────────────────────────────────────────────
    print(f"{'IP':<18} {'MODELO':<18} {'HASHRATE':>14} {'TEMP':>8} {'UPTIME':>8} {'ESTADO'}")
    print("-" * 75)

    total_ths = 0.0
    errors = []

    for data in all_data:
        if isinstance(data, Exception):
            errors.append(str(data))
            continue

        # Calcular TH/s para el total
        try:
            hr = data.hashrate
            rate = float(hr.rate)
            unit = str(hr.unit).upper()
            conversions = {"H/S": 1e-12, "KH/S": 1e-9, "MH/S": 1e-6,
                           "GH/S": 1e-3, "TH/S": 1.0, "PH/S": 1e3}
            total_ths += rate * conversions.get(unit, 1.0)
        except Exception:
            pass

        temp = f"{data.temperature_avg:.1f}°C" if data.temperature_avg else "N/A"

        uptime_h = "N/A"
        if data.uptime:
            h = data.uptime // 3600
            uptime_h = f"{h}h"

        estado = "🟢 Minando" if data.is_mining else "🔴 Parado"
        modelo = data.model or "Desconocido"
        hr_str = fmt_hashrate(data)

        print(
            f"{str(data.ip):<18} "
            f"{modelo:<18} "
            f"{hr_str:>14} "
            f"{temp:>8} "
            f"{uptime_h:>8} "
            f"{estado}"
        )

    print("-" * 75)
    n_ok = len([d for d in all_data if not isinstance(d, Exception)])
    print(f"  {n_ok} miners activos  |  HASHRATE TOTAL: {total_ths:.2f} TH/s")

    if errors:
        print(f"\n⚠️  {len(errors)} miners dieron error:")
        for e in errors:
            print(f"  - {e}")

    print("\n✅ Escaneo completado.")


if __name__ == "__main__":
    asyncio.run(main())
