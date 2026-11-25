"""Vista de estado: probar conexión, contadores."""
from __future__ import annotations
from dataclasses import dataclass
import flet as ft
import settings as cfg
import forwarder


@dataclass
class _StatusView:
    control: ft.Control
    refresh: callable


def build_status_view(page: ft.Page) -> _StatusView:
    lbl_conexion = ft.Text("Sin probar", color=ft.colors.GREY_700)
    lbl_url = ft.Text("", size=11, color=ft.colors.GREY_600, selectable=True)
    lbl_count = ft.Text("0 pendientes", size=12)

    def probar(_):
        s = cfg.load_settings()
        lbl_url.value = s.server_url
        lbl_conexion.value = "Probando..."
        lbl_conexion.color = ft.colors.ORANGE
        page.update()

        import threading
        def run():
            ok, msg = forwarder.ping(s.server_url)
            lbl_conexion.value = f"{'OK' if ok else 'FALLO'} — {msg}"
            lbl_conexion.color = ft.colors.GREEN if ok else ft.colors.RED
            page.update()
        threading.Thread(target=run, daemon=True).start()

    def refresh():
        from sms_queue import Queue
        q = Queue(cfg.sms_queue())
        pend = sum(1 for i in q.items() if i.estado == "pendiente")
        fall = sum(1 for i in q.items() if i.estado == "fallido")
        lbl_count.value = f"{pend} pendientes · {fall} fallidos"

    btn = ft.ElevatedButton("Probar conexión", icon=ft.icons.WIFI_TETHERING, on_click=probar)
    control = ft.Column(
        [
            ft.Text("Estado del puente", size=18, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Conexión al POS:", size=12, weight=ft.FontWeight.BOLD),
                        lbl_conexion, lbl_url,
                        ft.Divider(height=1),
                        ft.Text("Cola de reintento:", size=12, weight=ft.FontWeight.BOLD),
                        lbl_count,
                        ft.Container(height=8),
                        btn,
                    ],
                    spacing=6,
                ),
                padding=12, border_radius=8, bgcolor=ft.colors.BLUE_50,
            ),
        ],
        spacing=12,
    )
    return _StatusView(control=control, refresh=refresh)