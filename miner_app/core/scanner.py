"""
core/scanner.py
Lógica de escaneo y obtención de datos de miners usando pyasic.
Lee contraseñas desde miner_app/config.json automáticamente.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from pyasic import settings as pyasic_settings
from pyasic.network import MinerNetwork
from pyasic.data import MinerData


# ─── Config file ──────────────────────────────────────────────────────────────

def _config_path() -> str:
    """Devuelve la ruta al config.json, funcione desde fuente o desde .exe"""
    if getattr(sys, "frozen", False):
        # Ejecutable PyInstaller
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "miner_app", "config.json")


def load_config() -> dict:
    """Carga el archivo config.json. Si no existe, devuelve valores por defecto."""
    path = _config_path()
    defaults = {
        "passwords": {
            "antminer_web": "root",
            "antminer_ssh": "root",
            "whatsminer_rpc": "admin",
            "bosminer_web": "root",
            "bosminer_ssh": "root",
            "vnish_web": "admin",
            "goldshell_web": "123456789",
            "auradine_web": "admin",
            "epic_web": "letmein",
            "hive_web": "admin",
            "innosilicon_web": "admin",
        },
        "network": {
            "ip_from": "192.168.1.1",
            "ip_to": "192.168.1.254",
            "scan_timeout": 3,
            "monitor_interval_minutes": 5,
        }
    }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Merge con defaults para claves que falten
        for section, values in defaults.items():
            if section not in data:
                data[section] = values
            else:
                for k, v in values.items():
                    data[section].setdefault(k, v)
        return data
    except Exception:
        return defaults


def save_config(config: dict) -> None:
    """Guarda el config.json."""
    path = _config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[config] Error guardando config: {e}")


def configure_passwords_from_config():
    """Aplica las contraseñas del archivo config.json a pyasic.settings."""
    cfg = load_config()
    pw = cfg.get("passwords", {})

    # Mapa: clave del config.json → setting interno de pyasic
    mapping = {
        "antminer_web":    "default_antminer_web_password",
        "antminer_ssh":    "default_antminer_ssh_password",
        "whatsminer_rpc":  "default_whatsminer_rpc_password",
        "bosminer":        "default_bosminer_password",
        "vnish_web":       "default_vnish_web_password",
        "luxos_web":       "default_luxos_web_password",
        "luxos_ssh":       "default_luxos_ssh_password",
        "goldshell_web":   "default_goldshell_web_password",
        "iceriver_web":    "default_iceriver_web_password",
        "epic_web":        "default_epic_web_password",
        "elphapex_web":    "default_elphapex_web_password",
        "innosilicon_web": "default_innosilicon_web_password",
        "hive_web":        "default_hive_web_password",
        "hammer_web":      "default_hammer_web_password",
        "mskminer_web":    "default_mskminer_web_password",
        "auradine_web":    "default_auradine_web_password",
        "bitaxe_web":      "default_bitaxe_web_password",
        "blockminer_web":  "default_blockminer_web_password",
    }

    for config_key, pyasic_key in mapping.items():
        value = pw.get(config_key)
        if value is not None and not config_key.startswith("_"):
            try:
                pyasic_settings.update(pyasic_key, str(value))
            except Exception:
                pass  # Si un setting no existe en esta versión de pyasic, ignorar


def configure_passwords(**overrides):
    """Aplica contraseñas, con posibilidad de overrides puntuales."""
    configure_passwords_from_config()
    for k, v in overrides.items():
        mapping = {
            "antminer_web": "default_antminer_web_password",
            "antminer_ssh": "default_antminer_ssh_password",
            "whatsminer": "default_whatsminer_rpc_password",
            "bosminer": "default_bosminer_web_password",
        }
        key = mapping.get(k)
        if key:
            pyasic_settings.update(key, v)


# ─── Helpers de hashrate ──────────────────────────────────────────────────────

def hashrate_to_ths(data: MinerData) -> float:
    """Convierte el hashrate de cualquier unidad a TH/s para comparaciones."""
    hr = data.hashrate
    if hr is None:
        return 0.0
    try:
        rate = float(hr.rate)
        unit = str(hr.unit).upper()
        factors = {
            "H/S": 1e-12, "KH/S": 1e-9, "MH/S": 1e-6,
            "GH/S": 1e-3, "TH/S": 1.0, "PH/S": 1e3,
        }
        return rate * factors.get(unit, 1.0)
    except Exception:
        return 0.0


def hashrate_display(data: MinerData) -> str:
    """Devuelve el hashrate formateado en la unidad nativa del miner."""
    hr = data.hashrate
    if hr is None:
        return "N/A"
    try:
        rate = float(hr.rate)
        unit = str(hr.unit)
        # Normalizar el sufijo de unidad
        unit_clean = unit.replace("/S", "H/s").replace("/s", "H/s")
        if "gh" in unit.lower():
            unit_clean = "GH/s"
        elif "th" in unit.lower():
            unit_clean = "TH/s"
        elif "mh" in unit.lower():
            unit_clean = "MH/s"
        elif "ph" in unit.lower():
            unit_clean = "PH/s"
        return f"{rate:.2f} {unit_clean}"
    except Exception:
        return str(hr)


# ─── Dataclass de fila ────────────────────────────────────────────────────────

@dataclass
class MinerRow:
    """Fila de datos para mostrar en la tabla de la UI."""
    ip: str
    status: str
    miner_type: str        # Modelo/fabricante
    hashrate_str: str      # Display formateado
    hashrate_ths: float    # Float en TH/s para totales
    temperature: str
    pool1_url: str         # URL de la pool activa
    worker: str            # Username / worker
    # Objetos internos para control
    miner_obj: object = field(repr=False, default=None)
    data_obj: Optional[MinerData] = field(repr=False, default=None)
    # Pools completas
    all_pools: list[dict] = field(repr=False, default_factory=list)


# ─── Escaneo ──────────────────────────────────────────────────────────────────

async def scan_network(subnet: str, progress_cb=None) -> list[MinerRow]:
    """
    Escanea la subred y devuelve lista de MinerRow con datos.
    progress_cb(message: str) se llama con actualizaciones de estado.
    """
    rows: list[MinerRow] = []

    if progress_cb:
        progress_cb(f"Escaneando {subnet}...")

    try:
        network = MinerNetwork.from_subnet(subnet)
        miners = await network.scan()
    except Exception as e:
        if progress_cb:
            progress_cb(f"Error al escanear: {e}")
        return rows

    if not miners:
        if progress_cb:
            progress_cb("No se encontraron miners.")
        return rows

    if progress_cb:
        progress_cb(f"Encontrados {len(miners)} miners. Obteniendo datos...")

    results = await asyncio.gather(
        *[miner.get_data() for miner in miners],
        return_exceptions=True
    )

    for miner, result in zip(miners, results):
        ip = str(getattr(miner, "ip", "?"))

        if isinstance(result, Exception):
            rows.append(MinerRow(
                ip=ip,
                status="Error",
                miner_type=type(miner).__name__,
                hashrate_str="N/A",
                hashrate_ths=0.0,
                temperature="N/A",
                pool1_url="N/A",
                worker="N/A",
                miner_obj=miner,
                data_obj=None,
            ))
            continue

        data: MinerData = result

        # Estado
        try:
            status = "Minando" if data.is_mining else "Parado"
        except Exception:
            status = "OK"

        # Tipo/modelo
        model = getattr(data, "model", None) or type(miner).__name__
        make = getattr(data, "make", None) or ""
        display_type = f"{make} {model}".strip() if make and model else (model or type(miner).__name__)

        # Temperatura
        try:
            temp = f"{data.temperature_avg}°C" if data.temperature_avg is not None else "N/A"
        except Exception:
            temp = "N/A"

        # ── Pools: leer data.pools (list[PoolMetrics]) ───────────────────────
        pool1_url = "N/A"
        worker = "N/A"
        all_pools = []

        try:
            if data.pools:
                for idx, pool in enumerate(data.pools):
                    url_str = str(pool.url) if pool.url else ""
                    user_str = pool.user or ""
                    all_pools.append({
                        "index": idx,
                        "url": url_str,
                        "user": user_str,
                        "active": pool.active,
                        "alive": pool.alive,
                    })

                # Buscar la pool activa primero
                active_pool = next((p for p in all_pools if p.get("active")), None)
                if active_pool is None:
                    active_pool = all_pools[0]  # Si ninguna marcada activa, usar la primera

                pool1_url = active_pool["url"] or "N/A"
                worker = active_pool["user"] or "N/A"
        except Exception:
            pass

        rows.append(MinerRow(
            ip=ip,
            status=status,
            miner_type=display_type,
            hashrate_str=hashrate_display(data),
            hashrate_ths=hashrate_to_ths(data),
            temperature=temp,
            pool1_url=pool1_url,
            worker=worker,
            miner_obj=miner,
            data_obj=data,
            all_pools=all_pools,
        ))

    if progress_cb:
        progress_cb(f"✅ Completado: {len(rows)} miners procesados.")

    return rows


# ─── Control ──────────────────────────────────────────────────────────────────

async def reboot_miners(miners: list) -> dict[str, str]:
    """Reinicia los miners dados. Devuelve {ip: resultado}."""
    results = {}

    async def _reboot(miner):
        ip = str(getattr(miner, "ip", "?"))
        try:
            await miner.reboot()
            results[ip] = "OK"
        except Exception as e:
            results[ip] = f"Error: {e}"

    await asyncio.gather(*[_reboot(m) for m in miners], return_exceptions=True)
    return results


async def send_pool_config(miners: list, pools: list[dict]) -> dict[str, str]:
    """
    Envía configuración de pools a los miners.
    pools: lista de dicts {"url": str, "user": str, "password": str}
    Devuelve {ip: resultado}.
    """
    results = {}

    async def _send(miner):
        ip = str(getattr(miner, "ip", "?"))
        try:
            cfg = await miner.get_config()

            # Intentar actualizar pools directamente en el config de pyasic
            # Cada fabricante implementa su propia conversión en send_config()
            pool_list = [p for p in pools if p.get("url", "").strip()]

            if hasattr(cfg, "mining_mode") and cfg.mining_mode is not None:
                mm = cfg.mining_mode
                if hasattr(mm, "pools"):
                    from pyasic.config.mining import MiningPoolConfig
                    new_pools = []
                    for p in pool_list:
                        try:
                            new_pools.append(MiningPoolConfig(
                                url=p["url"],
                                user=p.get("user", ""),
                                password=p.get("password", "x") or "x",
                            ))
                        except Exception:
                            pass
                    if new_pools:
                        mm.pools = new_pools

            await miner.send_config(cfg)
            results[ip] = "OK"
        except Exception as e:
            results[ip] = f"Error: {e}"

    await asyncio.gather(*[_send(m) for m in miners], return_exceptions=True)
    return results
