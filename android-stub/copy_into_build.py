"""
Inyecta el SmsReceiver y permisos en el proyecto Android generado por Flet.
Uso: python android-stub/copy_into_build.py <ruta_build_apk>
"""
from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
NS = "http://schemas.android.com/apk/res/android"


def merge_manifest(orig: Path, patch: Path) -> None:
    # Parsear ambos
    tree = ET.parse(orig)
    root = tree.getroot()
    ptree = ET.parse(patch)
    proot = ptree.getroot()

    # Añadir permisos faltantes
    existing_perms = {
        el.get(f"{{{NS}}}name")
        for el in root.findall("uses-permission")
    }
    for el in proot.findall("uses-permission"):
        name = el.get(f"{{{NS}}}name")
        if name and name not in existing_perms:
            root.append(el)

    # Añadir receiver dentro de <application>
    app = root.find("application")
    if app is not None:
        pa = proot.find("application")
        if pa is not None:
            existing_rx = {el.get(f"{{{NS}}}name") for el in app.findall("receiver")}
            for rx in pa.findall("receiver"):
                if rx.get(f"{{{NS}}}name") not in existing_rx:
                    app.append(rx)

    tree.write(orig, encoding="utf-8", xml_declaration=True)


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: copy_into_build.py <build_apk_dir>", file=sys.stderr)
        return 2
    build = Path(sys.argv[1]).resolve()
    if not build.exists():
        print(f"No existe {build}", file=sys.stderr)
        return 1

    # 1. Copiar el SmsReceiver.kt al paquete Kotlin de la app
    kt_src = HERE / "SmsReceiver.kt"
    kt_dst_dir = build / "android" / "app" / "src" / "main" / "kotlin" / "cu" / "soklar" / "sms_bridge"
    kt_dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(kt_src, kt_dst_dir / "SmsReceiver.kt")

    # 2. Fusionar el manifest
    manifest = build / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest.exists():
        merge_manifest(manifest, HERE / "AndroidManifest.patch.xml")
        print("Manifest fusionado OK")
    else:
        print("No se encontró AndroidManifest.xml; revisa la ruta", file=sys.stderr)
        return 1

    print("Stub inyectado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())