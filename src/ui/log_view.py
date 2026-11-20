"""Lista de envíos con estado, y botón para limpiar los enviados."""
from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from core import settings as cfg
from core.queue import Queue


@dataclass
class _LogView:
    control: ft.Control
    refresh: callable


def build_log_view(page: ft.Page, cola: Queue) -> _LogView:
    lista = ft.ListView(expand=1, spacing=4, padding=4)

    def _fila(i) -> ft.Control:
        color = {"enviado": ft.colors.GREEN_300, "fallido": ft.colors.RED_300}.get(i.estado, ft.colors.AMBER_200)
        pago = i.pago or {}
        monto = pago.get("monto", 0)
        moneda = pago.get("moneda", "CUP")
        detalle = ft.Column(
            [
                ft.Text(f"{monto:.2f} {moneda} · {i.remitente}", weight=ft.FontWeight.BOLD, size=12),
                ft.Text(f"{i.creado} · {i.estado} · intentos={i.intentos}", size=10),
                ft.Text(i.ultimo_error, size=9, color=ft.colors.RED_700, selectable=True) if i.ultimo_error else ft.Container(),
            ],
            spacing=1,
        )
        return ft.Container(
            content=detalle,
            padding=8,
            border_radius=6,
            bgcolor=color,
            margin=ft.margin.symmetric(vertical=2),
        )

    def refresh():
        items = list(reversed(cola.items()))[:100]
        lista.controls = [_fila(i) for i in items] or [ft.Text("Sin envíos aún", italic=True)]
        page.update()

    def limpiar(_):
        cola.clear_sent()
        refresh()

    control = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Envíos recientes", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(ft.icons.CLEANING_SERVICES, tooltip="Limpiar enviados", on_click=limpiar),
                ],
            ),
            lista,
        ],
        expand=1,
        spacing=8,
    )
    cola.on_change(refresh)
    return _LogView(control=control, refresh=refresh)