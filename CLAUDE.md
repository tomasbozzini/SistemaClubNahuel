# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Desktop GUI application for managing sports court reservations at Club Nahuel. Built with Python, CustomTkinter, and SQLite.

## Running the app

```bash
# Activate the virtual environment first (Windows)
venv\Scripts\activate

# Run the application
python main.py

# Seed the database with initial courts (run once if DB is empty)
python init_db.py

# Build a standalone executable
pyinstaller main.spec
```

## Key dependencies

- `customtkinter 5.2.2` — modern-styled Tkinter widgets
- `tkcalendar 1.6.1` — calendar/date picker widgets
- `Pillow 12.0.0` — logo image loading
- `pyinstaller 6.16.0` — packaging to `.exe`

## Architecture

```
main.py                  # Entry point: creates data/, initializes DB, launches MainWindow
init_db.py               # Standalone seed script for initial courts
models/models.py         # All SQLite DB logic (raw sqlite3, no ORM)
ui/main_window.py        # Root CTk window; opens all other windows
ui/reservas_window.py    # CTkToplevel: create a reservation
ui/ver_reservas_window.py    # CTkToplevel: list and delete reservations
ui/gestionar_canchas_window.py  # CTkToplevel: add/remove courts
ui/calendario_reservas_window.py  # CTkToplevel: calendar view of reservations
utils/validaciones.py    # Input validation helpers (hora format HH:MM)
assets/                  # Logo images
data/reservas.db         # SQLite DB (auto-created at runtime)
```

## Data model

Two tables in `data/reservas.db`:

- **canchas** — `id, nombre, tipo (Fútbol/Pádel/Tenis), estado (disponible/alquilada)`
- **reservas** — `id, cliente, cancha_id, fecha (YYYY-MM-DD), hora (HH:MM), observaciones`

`DB_PATH` is derived from `sys.argv[0]` (not `__file__`) so it resolves correctly when packaged with PyInstaller.

## Important behaviors

- **Overlap detection**: each reservation blocks 1 hour. `hay_superposicion()` checks if the new slot overlaps any existing [hora, hora+1h) interval for the same court and date.
- **Court status**: inserting a reservation sets the court to `'alquilada'`; deleting it sets it back to `'disponible'`. The status only reflects the most recent state — a court with multiple future reservations may show `'disponible'` after one is deleted.
- **Auto-cleanup**: `MainWindow` calls `eliminar_reservas_expiradas()` on startup and every 60 seconds via `self.after(60000, ...)`. This deletes reservations whose end time (hora + 1h) has passed and resets court status to `'disponible'`.
- **All sub-windows** are `CTkToplevel` instances set as `transient(parent)` — they float above the main window but are not strictly modal (no `grab_set()`).
