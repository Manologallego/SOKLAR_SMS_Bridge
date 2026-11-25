"""Cola de reintento persistente en JSON. Un worker la drena cada N s."""
from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Callable
import threading
import forwarder
import settings as cfg


@dataclass
class Item:
    id: str
    remitente: str
    cuerpo: str
    pago: dict
    creado: str
    intentos: int = 0
    ultimo_error: str = ""
    estado: str = "pendiente"  # pendiente | enviado | fallido


class Queue:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._items: list[Item] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._listeners: list[Callable[[], None]] = []
        self._load()

    # ---------- persistencia ----------
    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._items = [Item(**r) for r in raw]
        except Exception:
            self._items = []

    def _save(self) -> None:
        self._path.write_text(
            json.dumps([asdict(i) for i in self._items], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ---------- API ----------
    def add(self, remitente: str, cuerpo: str, pago: dict) -> Item:
        with self._lock:
            item = Item(
                id=uuid.uuid4().hex,
                remitente=remitente,
                cuerpo=cuerpo,
                pago=pago,
                creado=datetime.now().isoformat(timespec="seconds"),
            )
            self._items.append(item)
            self._save()
        self._notify()
        return item

    def items(self) -> list[Item]:
        with self._lock:
            return list(self._items)

    def clear_sent(self) -> None:
        with self._lock:
            self._items = [i for i in self._items if i.estado != "enviado"]
            self._save()
        self._notify()

    def on_change(self, cb: Callable[[], None]) -> None:
        self._listeners.append(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    # ---------- worker ----------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="soklar-queue")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            s = cfg.load_settings()
            pending = [i for i in self.items() if i.estado == "pendiente"]
            for item in pending:
                urls = [u for u in (s.server_url, s.server_url_usb) if u]
                enviado = False
                ultimo = ""
                for url in urls:
                    from sms_parser import SmsPago
                    ok, msg = forwarder.enviar(
                        url, s.auth_token, item.remitente, item.cuerpo,
                        SmsPago(**item.pago),
                    )
                    if ok:
                        with self._lock:
                            item.estado = "enviado"
                            item.ultimo_error = ""
                        self._save()
                        enviado = True
                        break
                    ultimo = f"{url} → {msg}"
                if not enviado:
                    with self._lock:
                        item.intentos += 1
                        item.ultimo_error = ultimo
                        if item.intentos >= s.max_retries:
                            item.estado = "fallido"
                    self._save()
                    self._notify()
            self._notify()
            self._stop.wait(s.retry_interval_s)