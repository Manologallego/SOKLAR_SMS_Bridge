"""Editar URL, token y lista de remitentes."""
from __future__ import annotations
from dataclasses import dataclass
import flet as ft
import settings as cfg


@dataclass
class _ConfigView:
    control: ft.Control
    refresh: callable


def build_config_view(page: ft.Page, state: cfg.Settings) -> _ConfigView:
    et_wifi = ft.TextField(label="URL Wi-Fi", value=state.server_url, width=380)
    et_usb = ft.TextField(label="URL USB tethering", value=state.server_url_usb, width=380)
    et_tok = ft.TextField(label="Token (X-SOKLAR-Token)", value=state.auth_token,
                          password=True, can_reveal_password=True, width=380)
    et_rem = ft.TextField(label="Remitentes (separados por coma)",
                          value=", ".join(state.remitentes), width=380, multiline=True,
                          min_lines=1, max_lines=3)

    snack = ft.SnackBar(content=ft.Text(""))

    def guardar(_):
        s = cfg.Settings(
            server_url=et_wifi.value.strip(),
            server_url_usb=et_usb.value.strip(),
            auth_token=et_tok.value.strip(),
            remitentes=[r.strip() for r in et_rem.value.split(",") if r.strip()],
        )
        cfg.save_settings(s)
        snack.content.value = "Guardado"
        snack.open = True
        page.update()

    control = ft.Column(
        [
            ft.Text("Configuración", size=18, weight=ft.FontWeight.BOLD),
            et_wifi, et_usb, et_tok, et_rem,
            ft.ElevatedButton("Guardar", icon=ft.icons.SAVE, on_click=guardar),
            snack,
        ],
        spacing=10,
    )
    return _ConfigView(control=control, refresh=lambda: None)