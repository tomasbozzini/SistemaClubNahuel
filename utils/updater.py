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
            exe_dir = os.path.dirname(_exe_path())
            dest    = os.path.join(exe_dir, "_main_update.exe")

            req   = urllib.request.urlopen(url, timeout=120)
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

            # Verificar que el archivo esté completo
            if total and descargado < total:
                raise IOError(
                    f"Descarga incompleta: {descargado} de {total} bytes."
                )

            # Desbloquear el archivo (Windows lo marca como descargado de internet)
            try:
                subprocess.run(
                    ["powershell", "-Command", f'Unblock-File -Path "{dest}"'],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
            except Exception:
                pass

            if on_done:
                on_done(dest)
        except Exception as exc:
            if on_error:
                on_error(exc)

    threading.Thread(target=_worker, daemon=True).start()


def aplicar_actualizacion(ruta_nueva: str):
    """
    Reemplaza el exe actual con ruta_nueva y reinicia la app.
    Usa PowerShell para evitar que variables de entorno de PyInstaller
    (_MEIPASS2) se hereden al nuevo proceso y rompan la carga del DLL.
    """
    exe_actual = _exe_path()
    exe_dir    = os.path.dirname(exe_actual)

    # PowerShell: esperar, reemplazar, limpiar env de PyInstaller, lanzar limpio
    ps_cmd = (
        f"Start-Sleep -Seconds 6; "
        f"Move-Item -Force '{ruta_nueva}' '{exe_actual}'; "
        f"$env:_MEIPASS2 = $null; "
        f"Remove-Item Env:_MEIPASS2 -ErrorAction SilentlyContinue; "
        f"Start-Process -FilePath '{exe_actual}' "
        f"-WorkingDirectory '{exe_dir}'"
    )

    subprocess.Popen(
        [
            "powershell",
            "-WindowStyle", "Hidden",
            "-NonInteractive",
            "-Command", ps_cmd,
        ],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    sys.exit(0)
