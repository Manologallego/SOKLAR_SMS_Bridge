"""
Vigila el directorio donde el receptor Kotlin deja un .json por cada SMS.
En desktop (Windows/Linux) puedes apuntar watch_dir a una carpeta local para
probar el flujo completo sin Android.

Formato de archivo que escribe el Kotlin:
  <epoch_ms>_<random>.json
  {"remitente": "...", "cuerpo": "...", "ts": 1712345678901}
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Callable

log = logging.getLogger(__name__)


class SmsWatcher:
    def __init__(self, watch_dir: Path, on_sms: Callable[[str, str], None],
                 poll_s: float = 1.5) -> None:
        self._dir = watch_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._on_sms = on_sms
        self._poll = poll_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="soklar-watcher")
        self._thread.start()
        log.info("Vigilando SMS en %s", self._dir)

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        procesados: set[str] = set()
        while not self._stop.is_set():
            try:
                for f in sorted(self._dir.glob("*.json")):
                    if f.name in procesados:
                        continue
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        rem = str(data.get("remitente", ""))
                        cuerpo = str(data.get("cuerpo", ""))
                        procesados.add(f.name)
                        if rem and cuerpo:
                            log.info("SMS nuevo de %s (%d chars)", rem, len(cuerpo))
                            self._on_sms(rem, cuerpo)
                        f.unlink(missing_ok=True)
                    except Exception as e:  # noqa: BLE001
                        log.warning("Archivo %s inválido: %s", f.name, e)
                        procesados.add(f.name)
            except Exception as e:  # noqa: BLE001
                log.exception("Watcher: %s", e)
            self._stop.wait(self._poll)