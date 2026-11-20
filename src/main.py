"""Entry point Flet: SOKLAR SMS Bridge."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import flet as ft

# Permite importar src.core en ejecución directa
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import settings as cfg
from core.queue import Queue
from core.sms_parser import parse_sms
from core.sms_watcher import SmsWatcher
from core import forwarder

from ui.config_view import build_config_view
from ui.log_view import build_log_view
from ui.status_view import build_status_view

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("soklar")


def _inbox_dir() -> Path:
    """Directorio donde el Kotlin deja los SMS. En Android es app_data/files/inbox."""
    base = os.environ.get("FLET_APP_STORAGE_DATA")
    if base:
        p = Path(base) / "inbox"
    else:
        p = cfg.data_dir() / "inbox"
    p.mkdir(parents=True, exist_ok=True)
    return p


def main(page: ft.Page) -> None:
    page.title = "SOKLAR SMS Bridge"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 12
    page.window_width = 420
    page.window_height = 760

    state = cfg.load_settings()
    cola = Queue(cfg.queue_path())

    # --- Callback: SMS capturado -> parsear -> encolar ---
    def on_sms(remitente: str, cuerpo: str) -> None:
        parsed = parse_sms(cuerpo)
        if not parsed:
            log.warning("SMS de %s no parseable, se ignora", remitente)
            return
        cola.add(remitente, cuerpo, parsed.__dict__)
        log.info("Encolado: %.2f %s conf=%s", parsed.monto, parsed.moneda, parsed.confirmacion)

    watcher = SmsWatcher(_inbox_dir(), on_sms=on_sms)
    watcher.start()
    cola.start()

    # --- Vistas ---
    status_view = build_status_view(page)
    log_view = build_log_view(page, cola)
    config_view = build_config_view(page, state)

    # Refresco periódico de la UI
    def tick() -> None:
        status_view.refresh()
        log_view.refresh()

    page.on_route_change = lambda _: None
    page.on_view_pop = lambda _: None

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(text="Estado", icon=ft.icons.WIFI, content=status_view.control),
            ft.Tab(text="Ajustes", icon=ft.icons.SETTINGS, content=config_view.control),
            ft.Tab(text="Envíos", icon=ft.icons.LIST_ALT, content=log_view.control),
        ],
        expand=1,
    )
    page.add(tabs)

    # Timer de refresco
    import threading

    def loop():
        import time
        while True:
            try:
                tick()
            except Exception:
                pass
            time.sleep(2)

    threading.Thread(target=loop, daemon=True).start()

    def on_close(_):
        watcher.stop()
        cola.stop()
    page.on_close = on_close


if __name__ == "__main__":
    ft.app(target=main)