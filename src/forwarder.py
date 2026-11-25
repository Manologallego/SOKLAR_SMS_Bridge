"""Envío HTTP al webhook del POS."""
from __future__ import annotations
import logging
from dataclasses import asdict
import httpx
from sms_parser import SmsPago

log = logging.getLogger(__name__)


def enviar(
    url: str,
    token: str,
    remitente: str,
    cuerpo: str,
    pago: SmsPago,
    timeout: float = 6.0,
) -> tuple[bool, str]:
    """Devuelve (ok, mensaje)."""
    payload = {
        "remitente": remitente,
        "cuerpo": cuerpo,
        **asdict(pago),
    }
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-SOKLAR-Token"] = token

    try:
        with httpx.Client(timeout=timeout) as cli:
            r = cli.post(url, json=payload, headers=headers)
        if r.status_code in (200, 201, 202):
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}: {r.text[:120]}"
    except httpx.ConnectError as e:
        return False, f"Sin conexión: {e}"
    except httpx.TimeoutException:
        return False, "Timeout"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def ping(url: str, timeout: float = 4.0) -> tuple[bool, str]:
    base = url.rstrip("/").replace("/sms", "") + "/ping"
    try:
        with httpx.Client(timeout=timeout) as cli:
            r = cli.get(base)
        return r.status_code == 200, f"HTTP {r.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"