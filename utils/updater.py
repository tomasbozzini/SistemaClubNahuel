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
    Usa VBScript + ShellExecute para lanzar el nuevo exe exactamente
    igual que si el usuario hiciera doble click — evita problemas de
    contexto/DLL que ocurren al lanzar desde procesos hijos detached.
    """
    exe_actual = _exe_path()
    exe_dir    = os.path.dirname(exe_actual)
    vbs_path   = os.path.join(exe_dir, "_update_helper.vbs")

    vbs = (
        'WScript.Sleep 6000\n'
        'Set fso = CreateObject("Scripting.FileSystemObject")\n'
        f'fso.MoveFile "{ruta_nueva}", "{exe_actual}"\n'
        'Set sh = CreateObject("Shell.Application")\n'
        f'sh.ShellExecute "{exe_actual}", "", "{exe_dir}", "open", 1\n'
        'WScript.Quit\n'
    )
    with open(vbs_path, "w") as f:
        f.write(vbs)

    subprocess.Popen(
        ["wscript.exe", "//B", vbs_path],
        creationflags=subprocess.DETACHED_PROCESS,
        close_fds=True,
    )
    sys.exit(0)
