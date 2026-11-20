"""Parser de SMS de Transfermóvil/PagoxMovil. Tolera varios formatos."""
from __future__ import annotations

import re
from dataclasses import dataclass

_RE_MONTO_EXPL = re.compile(
    r"(?:monto|importe|valor|por|recibido\s+de)[^\d]{0,10}\$?\s*([\d.,]+)\s*(CUP|USD|MLC)?",
    re.IGNORECASE,
)
_RE_MONTO_GEN = re.compile(
    r"\$?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2}|\d+[.,]\d{2})\s*(CUP|USD|MLC)?",
    re.IGNORECASE,
)
_RE_SALDO = re.compile(
    r"saldo[^\d]{0,15}([\d.,]+)\s*(CUP|USD|MLC)?",
    re.IGNORECASE,
)
_RE_CONFIRMA = re.compile(
    r"(?:confirmaci[oó]n|operaci[oó]n|referencia|no\.?\s*(?:de\s*)?(?:operaci[oó]n|transacci[oó]n)|id)"
    r"[^\d]{0,15}(\d{4,})",
    re.IGNORECASE,
)
_RE_TELEFONO = re.compile(r"\b(5\d{7}|\d{8})\b")

_CONTEXTO = ("recibido", "transferencia", "pago", "abono", "depósito", "deposito", "acredit")


@dataclass
class SmsPago:
    monto: float
    moneda: str
    saldo: float | None = None
    confirmacion: str | None = None
    telefono: str | None = None


def _parse_num(s: str) -> float | None:
    t = s.strip().rstrip(".,")
    if not t:
        return None
    ld, lc = t.rfind("."), t.rfind(",")
    try:
        if ld >= 0 and lc >= 0:
            return float(t.replace(",", "") if ld > lc else t.replace(".", "").replace(",", "."))
        if lc >= 0:
            return float(t.replace(",", "."))
        return float(t)
    except ValueError:
        return None


def parse_sms(body: str) -> SmsPago | None:
    lower = body.lower()
    if not any(c in lower for c in _CONTEXTO):
        return None

    m = _RE_MONTO_EXPL.search(body) or _RE_MONTO_GEN.search(body)
    if not m:
        return None
    monto = _parse_num(m.group(1))
    if monto is None or monto <= 0:
        return None
    moneda = (m.group(2) or "CUP").upper()

    saldo = None
    if (sm := _RE_SALDO.search(body)) is not None:
        saldo = _parse_num(sm.group(1))

    conf = _RE_CONFIRMA.search(body)
    tel = _RE_TELEFONO.search(body)

    return SmsPago(
        monto=monto,
        moneda=moneda,
        saldo=saldo,
        confirmacion=conf.group(1) if conf else None,
        telefono=tel.group(0) if tel else None,
    )