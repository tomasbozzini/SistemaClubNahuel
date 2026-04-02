# utils/updater.py
import os
import sys
import subprocess
import threading
import urllib.request


def _exe_path() -> str:
    return os.path.abspath(sys.argv[0])


def descargar_actualizacion(url: str, on_progress=None, on_done=None, on_error=None):
    """
    Descarga el exe nuevo en un thread daemon.
      on_progress(bytes_descargados, total_bytes)
      on_done(ruta_archivo_descargado)
      on_error(excepcion)
    """
    def _worker():
        try:
            exe_dir  = os.path.dirname(_exe_path())
            dest     = os.path.join(exe_dir, "_main_update.exe")

            req   = urllib.request.urlopen(url, timeout=60)
            total = int(req.headers.get("Content-Length", 0))
            descargado = 0

            with open(dest, "wb") as f:
                while True:
                    bloque = req.read(65536)
                    if not bloque:
                        break
                    f.write(bloque)
                    descargado += len(bloque)
                    if on_progress:
                        on_progress(descargado, total)

            if on_done:
                on_done(dest)
        except Exception as exc:
            if on_error:
                on_error(exc)

    threading.Thread(target=_worker, daemon=True).start()


def aplicar_actualizacion(ruta_nueva: str):
    """
    Reemplaza el exe actual con ruta_nueva y reinicia la app.
    Usa un .bat intermedio porque Windows no permite reemplazar
    un ejecutable mientras está corriendo.
    """
    exe_actual = _exe_path()
    exe_dir    = os.path.dirname(exe_actual)
    bat_path   = os.path.join(exe_dir, "_update_helper.bat")

    bat = (
        "@echo off\n"
        "ping -n 3 127.0.0.1 > NUL\n"
        f'move /y "{ruta_nueva}" "{exe_actual}"\n'
        f'start "" "{exe_actual}"\n'
        'del "%~f0"\n'
    )
    with open(bat_path, "w") as f:
        f.write(bat)

    subprocess.Popen(
        ["cmd.exe", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    sys.exit(0)
