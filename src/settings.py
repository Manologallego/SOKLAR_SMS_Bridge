"""Persistencia local de configuración y cola. Todo en JSON en app_data_dir."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Settings(BaseModel):
    server_url: str = "http://192.168.1.100:8080/sms"
    server_url_usb: str = "http://192.168.42.1:8080/sms"
    auth_token: str = ""
    remitentes: list[str] = Field(default_factory=lambda: [
        "pagoxmovil", "pagox", "pago x movil",
        "transfermovil", "transfermóvil", "transfer movil",
    ])
    watch_dir: str = ""          # se resuelve en runtime
    retry_interval_s: int = 30
    max_retries: int = 20


def _data_dir() -> Path:
    # Flet expone FLET_APP_STORAGE_DATA en Android; en desktop usamos ~/.soklar
    env = os.environ.get("FLET_APP_STORAGE_DATA")
    if env:
        p = Path(env)
    else:
        p = Path.home() / ".soklar-sms"
    p.mkdir(parents=True, exist_ok=True)
    return p


_DATA_DIR = _data_dir()
_SETTINGS_FILE = _DATA_DIR / "settings.json"
_QUEUE_FILE = _DATA_DIR / "queue.json"
_LOG_FILE = _DATA_DIR / "envios.log"


def load_settings() -> Settings:
    if _SETTINGS_FILE.exists():
        try:
            return Settings(**json.loads(_SETTINGS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return Settings()


def save_settings(s: Settings) -> None:
    _SETTINGS_FILE.write_text(
        json.dumps(s.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def sms_queue_path() -> Path:
    return _QUEUE_FILE


def log_path() -> Path:
    return _LOG_FILE


def data_dir() -> Path:
    return _DATA_DIR