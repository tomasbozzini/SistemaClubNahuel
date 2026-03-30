# Sistema de Reservas - Club Nahuel

Aplicación de escritorio para gestionar reservas de canchas deportivas. Construida con Python, CustomTkinter y PostgreSQL (Supabase).

## Tecnologías

- Python 3.11
- CustomTkinter 5.2.2
- PostgreSQL via Supabase
- SQLAlchemy
- bcrypt
- PyInstaller

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/sistema-club-nahuel.git
cd sistema-club-nahuel
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Editá `.env` con tus credenciales de Supabase:

```
user=postgres.TU_PROJECT_ID
password=TU_PASSWORD
host=aws-0-sa-east-1.pooler.supabase.com
port=5432
dbname=postgres
ADMIN_PASSWORD=UNA_PASSWORD_SEGURA
```

### 4. Inicializar la base de datos

```bash
python db/init_db.py
python db/seed.py
```

### 5. Ejecutar la aplicación

```bash
python main.py
```

## Compilar ejecutable

```bash
pyinstaller main.spec
```

El ejecutable queda en `dist/main.exe`. La carpeta `assets/` debe estar en el mismo directorio que el `.exe`.

## Estructura del proyecto

```
main.py                  # Punto de entrada
auth/                    # Autenticación y sesiones
db/                      # Conexión, migraciones y seed
models/                  # Modelos y servicios de datos
ui/                      # Ventanas de la interfaz
sync/                    # Sincronización en tiempo real
utils/                   # Validaciones
assets/                  # Imágenes y recursos
```

## Roles de usuario

- **Admin**: acceso total — canchas, reservas, usuarios, reportes financieros
- **Supervisor**: acceso a reservas y disponibilidad

## Notas de seguridad

- Nunca commitear el archivo `.env` (está en `.gitignore`)
- Cambiar `ADMIN_PASSWORD` antes de ejecutar `seed.py` en producción
- Las contraseñas se almacenan hasheadas con bcrypt
