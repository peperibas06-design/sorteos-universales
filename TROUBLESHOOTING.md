# 🆘 TROUBLESHOOTING - Preguntas Frecuentes

## ❓ ¿Cuáles son las credenciales de administrador?

**Respuesta:** 
```
Usuario: adm
Contraseña: admin123456789
```

Están en el archivo `.env.example` y se pueden cambiar editando `.env`.

---

## ❓ ¿Dónde acceso al registro de usuarios?

**Respuesta:**
- URL: `http://localhost:5000/user/register`
- O click en "Registrarse" desde la página principal
- El formulario pide: Nombre, Apellido, Carnet, Teléfono, Email

---

## ❓ ¿Cómo veo el historial de acciones?

**Respuesta:**
1. Ingresa como administrador (`/admin/login`)
2. En el menú lateral, click en "Historial"
3. Verás tabla con todas las operaciones:
   - Crear evento
   - Cerrar evento
   - Eliminar evento
   - Crear boleto
   - Registrar usuario

---

## ❓ ¿Cómo imprimo un boleto?

**Respuesta:**
1. Después de comprar un boleto, accede: `/ticket/<número>/print`
2. Opciones:
   - 🖨️ Click "Imprimir" → Se abre diálogo de impresión
   - ⬇️ Click "Descargar QR" → Guarda QR como PNG
3. Imprime o descarga según necesites

---

## ❓ ¿Los boletos se pueden descargar como PDF?

**Respuesta:**
Actualmente se descargan como imagen PNG del QR.
Para PDF completo del boleto, es mejora futura.
De momento:
- Imprimir a PDF desde el navegador (Ctrl+P → "Guardar como PDF")
- O descargar QR como PNG

---

## ❓ ¿Dónde se guardan las imágenes?

**Respuesta:**
```
static/uploads/
```

Las imágenes subidas en:
- Evento
- Premio
- Fondo de boleto
- Ubicación

Se guardan automáticamente con nombres aleatorios (UUID).

---

## ❓ ¿Se puede deshacer una acción? (Undo)

**Respuesta:**
Actualmente **NO** tiene botón de undo/redo funcional.
Se registran las acciones en el historial para **futuro uso** (ver `action_history` table).

Para futuras versiones está planeado implementar:
- Botón "Deshacer"
- Botón "Rehacer"

---

## ❓ ¿Qué pasa si elimino un evento?

**Respuesta:**
Se eliminan:
1. El evento
2. Todos sus boletos
3. Todos los registros de sorteo

⚠️ **NO SE PUEDE RECUPERAR** - Por eso el sistema pide confirmación.

---

## ❓ ¿Un usuario puede tener múltiples boletos?

**Respuesta:**
- **SÍ** - Puede comprar varias veces
- **PERO** - En la tabla `users` solo aparece UNA VEZ (registro único por email/carnet)
- En `tickets` aparecen todos sus boletos (múltiples filas)

---

## ❓ ¿El email es único?

**Respuesta:**
- En tabla `users` - **SÍ**, email ÚNICO
- En tabla `tickets` - **NO**, puede haber múltiples boletos con mismo email
- Si intenta registrarse con email que ya existe, le pide que use otro

---

## ❓ ¿El carnet es único?

**Respuesta:**
- En tabla `users` - **SÍ**, carnet ÚNICO
- En tabla `tickets` - **NO**, hay validación por evento
- Un carnet **NO puede tener 2+ boletos en el MISMO evento**
- **PERO SÍ puede tener boletos en DIFERENTES eventos**

---

## ❓ ¿Cómo me aseguro que está todo instalado?

**Respuesta:**
Ejecuta el script de verificación:
```bash
python verify_changes.py
```

Debe mostrar todos los ✅ verdes.

---

## ❓ ¿Dónde está la base de datos?

**Respuesta:**
```
tickets.db
```

En la raíz del proyecto.
Se crea automáticamente en primer inicio.

---

## ❓ ¿Puedo cambiar las credenciales de admin?

**Respuesta:**
**SÍ**, edita el archivo `.env`:

```bash
# Abre .env
ADMIN_USER=adm
ADMIN_PASSWORD=admin123456789

# Cambia a:
ADMIN_USER=tuusuario
ADMIN_PASSWORD=tucontraseña
```

Reinicia la app y listo.

---

## ❓ ¿Qué información está en el historial?

**Respuesta:**
Se registra:
- **Acción**: CREATE, UPDATE, DELETE
- **Entidad**: event, ticket, user
- **ID**: ID de la entidad
- **Cambios**: JSON con detalles
- **Fecha**: Timestamp exacto

Ejemplo:
```json
{
  "action_type": "CREATE",
  "entity_type": "ticket",
  "entity_id": 1,
  "changes": {
    "quantity": 5,
    "buyer": "Juan Pérez",
    "email": "juan@example.com"
  },
  "created_at": "2026-06-23T14:35:20.123456"
}
```

---

## ❓ ¿El QR es seguro? ¿Se puede falsificar?

**Respuesta:**
**SÍ, es seguro** porque:
- Se genera en **servidor** (no en cliente)
- Contiene: `EVT{event_id}-TK{ticket_number}-{random_id}`
- Es único por boleto
- No se puede predecir sin acceso a servidor

---

## ❓ ¿Qué archivos nuevos se agregaron?

**Respuesta:**
```
Backend:
✅ app.py (modificado)
✅ .env.example (modificado)

Templates:
✅ templates/register_user.html (NUEVO)
✅ templates/print_ticket.html (NUEVO)
✅ templates/admin_history.html (NUEVO)
✅ base.html (modificado)
✅ admin_base.html (modificado)

Documentación:
✅ CHANGES.md (NUEVO)
✅ QUICK_START.md (NUEVO)
✅ IMPLEMENTATION_SUMMARY.md (NUEVO)
✅ TROUBLESHOOTING.md (este archivo)
✅ verify_changes.py (NUEVO)
```

---

## ❓ ¿Hay algún error en los templates?

**Respuesta:**
Si falta alguna variable o hay error de sintaxis:

1. Revisa que `app.py` esté actualizado
2. Elimina `tickets.db` y reinicia (recrea base de datos)
3. Revisa la consola de Python por errores
4. Ejecuta `verify_changes.py` para confirmar

---

## ❓ ¿Cómo hago un respaldo de la base de datos?

**Respuesta:**
Simplemente copia el archivo:
```bash
cp tickets.db tickets.db.backup
```

Para restaurar:
```bash
cp tickets.db.backup tickets.db
```

---

## ❓ ¿Puedo ver el historial en JSON?

**Respuesta:**
**SÍ**, en la tabla de historial hay un botón "Ver detalles" que expande el JSON.

O accede directamente a base de datos:
```sql
SELECT * FROM action_history;
```

---

## ❓ ¿Cuál es el puerto por defecto?

**Respuesta:**
```
5000
```

Se puede cambiar en `.env`:
```bash
PORT=8080
```

---

## ❓ ¿Necesito instalar algo más?

**Respuesta:**
Todas las dependencias están en `requirements.txt`:
```bash
pip install -r requirements.txt
```

Principales:
- Flask 3.0+
- Werkzeug 3.0+
- qrcode[pil] 7.4+
- openpyxl 3.1+
- python-dotenv 1.0+

---

## ❓ ¿Cómo reporto un problema?

**Respuesta:**
1. Ejecuta `verify_changes.py` para confirmar instalación
2. Revisa la consola de Python por errores
3. Mira el archivo `CHANGES.md` para detalles técnicos
4. Consulta este archivo `TROUBLESHOOTING.md`

---

## 🎯 CHECKLIST DE VERIFICACIÓN

Antes de decir que algo no funciona, verifica:

- [ ] ¿Ejecutaste `python app.py`? (sin errores)
- [ ] ¿Accediste a `http://localhost:5000`? (muestra página)
- [ ] ¿Ejecutaste `verify_changes.py`? (todos ✅)
- [ ] ¿Usaste credenciales correctas? (adm / admin123456789)
- [ ] ¿La base de datos existe? (`tickets.db` presente)
- [ ] ¿Los templates existen? (en carpeta `templates/`)
- [ ] ¿Tengo Python 3.10+? (`python --version`)
- [ ] ¿Instalé dependencias? (`pip install -r requirements.txt`)

---

## 📞 SOPORTE

Para más información:
- 📖 `CHANGES.md` - Detalles técnicos
- 🚀 `QUICK_START.md` - Guía rápida
- 📊 `IMPLEMENTATION_SUMMARY.md` - Resumen completo
- ✔️ `verify_changes.py` - Script de verificación
- 💻 `app.py` - Código fuente
- 🎨 `templates/` - Templates HTML

---

**¿Sigue sin funcionar?** Revisa la consola de Python por errores específicos 🔍
