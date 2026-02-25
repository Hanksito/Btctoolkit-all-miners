"""
ui/app.py
Ventana principal de Mining Manager.
Usa CustomTkinter para una UI moderna.
"""
from __future__ import annotations

import asyncio
import threading
import time
from typing import Optional

import customtkinter as ctk
from tkinter import ttk, messagebox, StringVar, BooleanVar
import tkinter as tk

from miner_app.core.scanner import (
    MinerRow, scan_network, reboot_miners,
    send_pool_config, configure_passwords,
    configure_passwords_from_config, load_config, save_config,
)

# ─── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DARK_BG = "#1a1a2e"
PANEL_BG = "#16213e"
ACCENT = "#0f3460"
BLUE = "#4cc9f0"
GREEN = "#06d6a0"
RED = "#ef476f"
ORANGE = "#ffd166"
TEXT = "#e2e8f0"
TEXT_DIM = "#94a3b8"

# Columnas de la tabla
COLUMNS = ("ip", "status", "type", "hashrate", "temperature", "pool", "worker")
COL_LABELS = {
    "ip": "IP",
    "status": "STATUS",
    "type": "TYPE / MODEL",
    "hashrate": "HASHRATE",
    "temperature": "TEMP",
    "pool": "POOL",
    "worker": "WORKER",
}
COL_WIDTHS = {
    "ip": 130, "status": 90, "type": 160,
    "hashrate": 120, "temperature": 80, "pool": 200, "worker": 150,
}


class MiningManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⛏  Mining Manager — pyasic")
        self.geometry("1400x820")
        self.minsize(1100, 700)
        self.configure(fg_color=DARK_BG)

        # Estado
        self._rows: list[MinerRow] = []
        self._monitor_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._scan_running = False

        # Diccionario ip → MinerRow (para operaciones de control)
        self._miner_map: dict[str, MinerRow] = {}

        # Cargar config e inicializar IPs y contraseñas
        self._cfg = load_config()
        configure_passwords_from_config()
        self._build_ui()

    # ─────────────────────────── UI ───────────────────────────────────────────

    def _build_ui(self):
        # ── Barra superior ────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=60)
        top.pack(fill="x", side="top", padx=0, pady=0)
        top.pack_propagate(False)

        # Logo / título
        ctk.CTkLabel(
            top, text="⛏  Mining Manager",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=BLUE,
        ).pack(side="left", padx=20, pady=10)

        # Status bar dentro del top
        self._status_var = StringVar(value="Listo.")
        self._status_label = ctk.CTkLabel(
            top, textvariable=self._status_var,
            font=ctk.CTkFont(size=12), text_color=TEXT_DIM,
        )
        self._status_label.pack(side="left", padx=20)

        # Progress bar
        self._progress = ctk.CTkProgressBar(top, width=200, mode="indeterminate")
        self._progress.pack(side="left", padx=10)
        self._progress.stop()

        # Botones de acción (derecha)
        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        self._btn_scan = ctk.CTkButton(
            btn_frame, text="🔍  SCAN", width=110, height=36,
            fg_color=ACCENT, hover_color="#1a5276",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_scan,
        )
        self._btn_scan.pack(side="left", padx=4)

        self._btn_monitor = ctk.CTkButton(
            btn_frame, text="📡  MONITOR", width=120, height=36,
            fg_color="#1b4332", hover_color="#40916c",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_monitor_toggle,
        )
        self._btn_monitor.pack(side="left", padx=4)

        self._btn_reboot_sel = ctk.CTkButton(
            btn_frame, text="🔄  REBOOT SEL.", width=130, height=36,
            fg_color="#7b2d00", hover_color="#c44d00",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_reboot_selected,
        )
        self._btn_reboot_sel.pack(side="left", padx=4)

        self._btn_reboot_all = ctk.CTkButton(
            btn_frame, text="🔄  REBOOT ALL", width=130, height=36,
            fg_color="#6b21a8", hover_color="#9333ea",
            font=ctk.CTkFont(weight="bold"),
            command=self._on_reboot_all,
        )
        self._btn_reboot_all.pack(side="left", padx=4)

        # ── Fila de configuración ─────────────────────────────────────────────
        cfg_row = ctk.CTkFrame(self, fg_color=PANEL_BG, corner_radius=0, height=50)
        cfg_row.pack(fill="x", side="top", padx=0, pady=(1, 0))
        cfg_row.pack_propagate(False)

        # IP Range
        ctk.CTkLabel(cfg_row, text="IP Range:", text_color=TEXT_DIM,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(16, 4), pady=10)
        net_cfg = self._cfg.get("network", {})
        self._ip_from_var = StringVar(value=net_cfg.get("ip_from", "192.168.1.1"))
        self._ip_to_var = StringVar(value=net_cfg.get("ip_to", "192.168.1.254"))
        ip_from = ctk.CTkEntry(cfg_row, textvariable=self._ip_from_var, width=140,
                               placeholder_text="IP inicio")
        ip_from.pack(side="left", padx=4)
        ctk.CTkLabel(cfg_row, text="→", text_color=TEXT_DIM).pack(side="left")
        ip_to = ctk.CTkEntry(cfg_row, textvariable=self._ip_to_var, width=140,
                             placeholder_text="IP fin")
        ip_to.pack(side="left", padx=4)

        # Botón de configuración (abre config.json)
        ctk.CTkButton(
            cfg_row, text="⚙  Config", width=90, height=28,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=11),
            command=self._open_config,
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            cfg_row, text="Las contraseñas se configuran en miner_app/config.json",
            text_color=TEXT_DIM, font=ctk.CTkFont(size=10),
        ).pack(side="left", padx=4)

        # Contador (derecha)
        self._count_var = StringVar(value="0 miners")
        ctk.CTkLabel(cfg_row, textvariable=self._count_var,
                     text_color=GREEN, font=ctk.CTkFont(size=13, weight="bold"),
                     ).pack(side="right", padx=20)

        # ── Cuerpo principal (tabla + panel pools) ────────────────────────────
        body = ctk.CTkFrame(self, fg_color=DARK_BG)
        body.pack(fill="both", expand=True, padx=8, pady=6)

        # Tabla (izquierda)
        table_frame = ctk.CTkFrame(body, fg_color=PANEL_BG, corner_radius=10)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._build_table(table_frame)

        # Panel derecho (pools + acciones)
        right = ctk.CTkFrame(body, fg_color=PANEL_BG, corner_radius=10, width=340)
        right.pack(side="right", fill="y", padx=(0, 0))
        right.pack_propagate(False)

        self._build_pool_panel(right)

    def _build_table(self, parent):
        # Frame con scrollbars
        header = ctk.CTkLabel(
            parent, text="Miners detectados",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=BLUE,
        )
        header.pack(anchor="w", padx=12, pady=(10, 4))

        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Miner.Treeview",
                        background="#0d1117",
                        foreground=TEXT,
                        fieldbackground="#0d1117",
                        rowheight=28,
                        font=("Consolas", 10))
        style.configure("Miner.Treeview.Heading",
                        background=ACCENT,
                        foreground="white",
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("Miner.Treeview",
                  background=[("selected", "#1a5276")],
                  foreground=[("selected", "white")])

        self._tree = ttk.Treeview(
            frame,
            columns=COLUMNS,
            show="headings",
            style="Miner.Treeview",
            selectmode="extended",
        )

        # Configurar columnas
        for col in COLUMNS:
            self._tree.heading(col, text=COL_LABELS[col],
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=COL_WIDTHS[col], anchor="w", stretch=True)

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        # Tags de colores por estado
        self._tree.tag_configure("mining", foreground="#06d6a0")
        self._tree.tag_configure("stopped", foreground="#ef476f")
        self._tree.tag_configure("error", foreground="#ffd166")
        self._tree.tag_configure("odd", background="#0d1117")
        self._tree.tag_configure("even", background="#111827")

        self._tree.bind("<Double-1>", self._on_row_double_click)

    def _build_pool_panel(self, parent):
        ctk.CTkLabel(
            parent, text="⚙️  Configurar Pools",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=BLUE,
        ).pack(anchor="w", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            parent, text="Selecciona miners en la tabla y rellena las pools:",
            text_color=TEXT_DIM, font=ctk.CTkFont(size=11), wraplength=300,
        ).pack(anchor="w", padx=14)

        # Pools form
        self._pool_vars: list[dict] = []

        for i in range(1, 4):
            pool_label = ctk.CTkLabel(
                parent, text=f"Pool {i}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_DIM,
            )
            pool_label.pack(anchor="w", padx=14, pady=(10, 0))

            frame = ctk.CTkFrame(parent, fg_color="#0d1117", corner_radius=6)
            frame.pack(fill="x", padx=10, pady=2)

            url_var = StringVar()
            worker_var = StringVar()
            pass_var = StringVar(value="x")

            ctk.CTkLabel(frame, text="URL:", text_color=TEXT_DIM,
                         font=ctk.CTkFont(size=10), width=50).grid(row=0, column=0, padx=4, pady=4, sticky="w")
            ctk.CTkEntry(frame, textvariable=url_var, placeholder_text="stratum+tcp://pool:port",
                         width=260).grid(row=0, column=1, padx=4, pady=4, columnspan=2, sticky="ew")

            ctk.CTkLabel(frame, text="Worker:", text_color=TEXT_DIM,
                         font=ctk.CTkFont(size=10), width=50).grid(row=1, column=0, padx=4, pady=2, sticky="w")
            ctk.CTkEntry(frame, textvariable=worker_var, placeholder_text="wallet.worker",
                         width=180).grid(row=1, column=1, padx=4, pady=2, sticky="ew")

            ctk.CTkLabel(frame, text="Pwd:", text_color=TEXT_DIM,
                         font=ctk.CTkFont(size=10), width=40).grid(row=1, column=2, padx=2, pady=2, sticky="e")
            ctk.CTkEntry(frame, textvariable=pass_var, width=60, show="*"
                         ).grid(row=1, column=3, padx=4, pady=2, sticky="ew")

            frame.columnconfigure(1, weight=1)

            self._pool_vars.append({"url": url_var, "user": worker_var, "password": pass_var})

        # Checkboxes de opciones
        self._only_enabled_var = BooleanVar(value=True)
        ctk.CTkCheckBox(
            parent, text="Solo pools activas", variable=self._only_enabled_var,
            text_color=TEXT_DIM, font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=14, pady=(10, 4))

        # Botón UPDATE
        ctk.CTkButton(
            parent, text="⬆  UPDATE CONFIG",
            height=42, fg_color="#1b4332", hover_color="#40916c",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_update_pools,
        ).pack(fill="x", padx=10, pady=(12, 6))

        # Separador
        ctk.CTkLabel(parent, text="─" * 40, text_color="#374151").pack(pady=4)

        # Info del miner seleccionado
        ctk.CTkLabel(
            parent, text="ℹ️  Info del miner seleccionado",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=BLUE,
        ).pack(anchor="w", padx=14, pady=(4, 4))

        self._info_text = ctk.CTkTextbox(
            parent, height=140, fg_color="#0d1117",
            text_color=TEXT_DIM, font=ctk.CTkFont(family="Consolas", size=10),
            state="disabled",
        )
        self._info_text.pack(fill="x", padx=10, pady=(0, 10))

        # Uptime / monitor info
        self._monitor_info_var = StringVar(value="Monitor: inactivo")
        ctk.CTkLabel(
            parent, textvariable=self._monitor_info_var,
            text_color=TEXT_DIM, font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=14, pady=2)

    # ─────────────────────────── LÓGICA ───────────────────────────────────────

    def _open_config(self):
        """Abre el archivo config.json con el editor por defecto del sistema."""
        import subprocess, os, sys
        from miner_app.core.scanner import _config_path
        path = _config_path()
        try:
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.run(["xdg-open", path])
            self._set_status(f"Abierto: {path} — reinicia la app para aplicar cambios.")
        except Exception as e:
            self._set_status(f"Error abriendo config: {e}")

    def _get_subnet(self) -> str:
        """Obtiene la subred a escanear a partir del IP Range configurado."""
        ip_from = self._ip_from_var.get().strip()
        # Usamos la IP 'from' como referencia para la subred /24
        parts = ip_from.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return "192.168.1.0/24"

    def _on_scan(self):
        if self._scan_running:
            self._set_status("⚠️  Ya hay un escaneo en curso...")
            return
        subnet = self._get_subnet()
        self._start_scan(subnet)

    def _start_scan(self, subnet: str):
        self._scan_running = True
        self._btn_scan.configure(state="disabled", text="Escaneando...")
        self._progress.start()
        self._set_status(f"Escaneando {subnet}...")

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                rows = loop.run_until_complete(
                    scan_network(subnet, progress_cb=self._set_status_thread)
                )
                self.after(0, self._update_table, rows)
            except Exception as e:
                self.after(0, self._set_status, f"Error: {e}")
            finally:
                loop.close()
                self.after(0, self._scan_done)

        threading.Thread(target=_run, daemon=True).start()

    def _scan_done(self):
        self._scan_running = False
        self._btn_scan.configure(state="normal", text="🔍  SCAN")
        self._progress.stop()

    def _on_monitor_toggle(self):
        if self._monitor_active:
            self._monitor_active = False
            self._btn_monitor.configure(
                text="📡  MONITOR", fg_color="#1b4332",
            )
            self._monitor_info_var.set("Monitor: inactivo")
            self._set_status("Monitor detenido.")
        else:
            self._monitor_active = True
            self._btn_monitor.configure(
                text="⏹  STOP MONITOR", fg_color=RED,
            )
            self._set_status("Monitor activo — escaneo cada 5 min.")
            self._monitor_info_var.set("Monitor: activo ⏱")
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True,
            )
            self._monitor_thread.start()

    def _monitor_loop(self):
        while self._monitor_active:
            subnet = self._get_subnet()
            self.after(0, self._set_status, "🔄 Monitor: escaneando...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                rows = loop.run_until_complete(
                    scan_network(subnet, progress_cb=self._set_status_thread)
                )
                self.after(0, self._update_table, rows)
            except Exception as e:
                self.after(0, self._set_status, f"Monitor error: {e}")
            finally:
                loop.close()

            # Esperar 5 minutos en intervalos de 1 segundo para poder cancelar
            for _ in range(300):
                if not self._monitor_active:
                    break
                time.sleep(1)

    def _update_table(self, rows: list[MinerRow]):
        # Limpiar tabla
        for item in self._tree.get_children():
            self._tree.delete(item)

        self._rows = rows
        self._miner_map = {r.ip: r for r in rows}

        mining_count = 0
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            status_lower = row.status.lower()
            if "mina" in status_lower:
                tag = "mining"
                mining_count += 1
            elif "error" in status_lower or "fail" in status_lower:
                tag = "error"
            elif "para" in status_lower:
                tag = "stopped"

            self._tree.insert(
                "", "end",
                iid=row.ip,
                values=(
                    row.ip,
                    row.status,
                    row.miner_type,
                    row.hashrate_str,
                    row.temperature,
                    row.pool1_url,
                    row.worker,
                ),
                tags=(tag,),
            )

        total_ths = sum(r.hashrate_ths for r in rows)
        self._count_var.set(
            f"{len(rows)} miners  |  {mining_count} activos  |  {total_ths:.2f} TH/s total"
        )
        self._set_status(f"✅  {len(rows)} miners encontrados — {total_ths:.2f} TH/s")

    def _get_selected_rows(self) -> list[MinerRow]:
        selected = self._tree.selection()
        return [self._miner_map[ip] for ip in selected if ip in self._miner_map]

    def _on_reboot_selected(self):
        sel = self._get_selected_rows()
        if not sel:
            messagebox.showinfo("Reboot", "Selecciona al menos un miner en la tabla.")
            return
        ips = [r.ip for r in sel]
        if not messagebox.askyesno("Confirmar Reboot",
                                   f"¿Reiniciar {len(sel)} miner(s)?\n{', '.join(ips)}"):
            return
        miners = [r.miner_obj for r in sel if r.miner_obj]
        self._do_reboot(miners)

    def _on_reboot_all(self):
        if not self._rows:
            messagebox.showinfo("Reboot All", "No hay miners cargados. Haz Scan primero.")
            return
        if not messagebox.askyesno("Confirmar Reboot ALL",
                                   f"¿Reiniciar TODOS los {len(self._rows)} miners?"):
            return
        miners = [r.miner_obj for r in self._rows if r.miner_obj]
        self._do_reboot(miners)

    def _do_reboot(self, miners: list):
        self._set_status(f"Reiniciando {len(miners)} miners...")
        self._progress.start()

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(reboot_miners(miners))
                ok = sum(1 for v in results.values() if v == "OK")
                self.after(0, self._set_status, f"✅ Reboot completado: {ok}/{len(miners)} OK")
                self.after(0, self._progress.stop)
            except Exception as e:
                self.after(0, self._set_status, f"Error reboot: {e}")
                self.after(0, self._progress.stop)
            finally:
                loop.close()

        threading.Thread(target=_run, daemon=True).start()

    def _on_update_pools(self):
        sel = self._get_selected_rows()
        if not sel:
            messagebox.showinfo("Update Pools", "Selecciona al menos un miner en la tabla.")
            return

        pools = []
        for pv in self._pool_vars:
            url = pv["url"].get().strip()
            if not url and self._only_enabled_var.get():
                continue
            pools.append({
                "url": url,
                "user": pv["user"].get().strip(),
                "password": pv["password"].get().strip() or "x",
            })

        if not pools:
            messagebox.showwarning("Update Pools", "Introduce al menos una URL de pool.")
            return

        miners = [r.miner_obj for r in sel if r.miner_obj]
        ips = [r.ip for r in sel]
        self._set_status(f"Enviando config a {len(miners)} miners...")
        self._progress.start()

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(send_pool_config(miners, pools))
                ok = sum(1 for v in results.values() if v == "OK")
                errors = {k: v for k, v in results.items() if v != "OK"}
                msg = f"✅ Update pools: {ok}/{len(miners)} OK"
                if errors:
                    msg += f" | Errores: {', '.join(errors.keys())}"
                self.after(0, self._set_status, msg)
                self.after(0, self._progress.stop)
            except Exception as e:
                self.after(0, self._set_status, f"Error update pools: {e}")
                self.after(0, self._progress.stop)
            finally:
                loop.close()

        threading.Thread(target=_run, daemon=True).start()

    def _on_row_double_click(self, event):
        sel = self._get_selected_rows()
        if not sel:
            return
        row = sel[0]
        data = row.data_obj

        self._info_text.configure(state="normal")
        self._info_text.delete("0.0", "end")

        lines = [
            f"IP:          {row.ip}",
            f"Modelo:      {row.miner_type}",
            f"Status:      {row.status}",
            f"Hashrate:    {row.hashrate_str}",
            f"Temperatura: {row.temperature}",
            f"Pool1:       {row.pool1_url}",
            f"Worker:      {row.worker}",
        ]

        if data:
            try:
                lines.append(f"Uptime:      {data.uptime // 3600}h" if data.uptime else "Uptime: N/A")
                lines.append(f"Fans:        {data.fan_1_speed} / {data.fan_2_speed} RPM")
            except Exception:
                pass

        self._info_text.insert("end", "\n".join(lines))
        self._info_text.configure(state="disabled")

    def _sort_by(self, col: str):
        """Ordena la tabla por la columna clickeada."""
        rows = [(self._tree.set(item, col), item) for item in self._tree.get_children("")]
        rows.sort(key=lambda x: x[0])
        for idx, (_, item) in enumerate(rows):
            self._tree.move(item, "", idx)

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    def _set_status_thread(self, msg: str):
        """Thread-safe status update."""
        self.after(0, self._set_status, msg)
