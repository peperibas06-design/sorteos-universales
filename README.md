# Rifa — boletos digitales

Sistema de venta de boletos para rifas/sorteos: catálogo público de eventos, compra de
boletos con cupón de descuento y QR de verificación, y panel de administración para
crear eventos, ver reportes y realizar el sorteo.

## Requisitos

- Python 3.10 o superior

## Instalación local

```bash
# 1. Entrá a la carpeta del proyecto
cd raffle

# 2. Creá un entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 3. Instalá las dependencias
pip install -r requirements.txt

# 4. Copiá el archivo de variables de entorno y editalo
cp .env.example .env
# abrí .env y cambiá SECRET_KEY, ADMIN_USER y ADMIN_PASSWORD

# 5. Corré la app
python app.py
```

Abrí tu navegador en **http://127.0.0.1:5000** para ver el sitio público, y en
**http://127.0.0.1:5000/admin/login** para entrar al panel de administración con el
usuario y contraseña que pusiste en `.env`.

La base de datos SQLite (`tickets.db`) y las imágenes subidas (`static/uploads/`) se
crean solas la primera vez que corrés la app — no hace falta ninguna configuración
adicional.

## Estructura

```
app.py                  Backend Flask (rutas, base de datos, lógica de negocio)
templates/               Plantillas HTML (Jinja2)
static/css/style.css     Estilos
static/uploads/          Imágenes subidas desde el panel de administración (se genera sola)
tickets.db                Base de datos SQLite (se genera sola)
```

## Notas

- Si cambiás `ADMIN_USER`/`ADMIN_PASSWORD` en `.env` después de haber iniciado sesión
  una vez, vas a tener que volver a loguearte.
- El QR de cada boleto se genera en el servidor a partir de un código único — no lo
  define quien compra el boleto, así no se puede falsificar.
