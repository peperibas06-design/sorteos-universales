# 🎟️ Guía Rápida - Nuevas Características

## 🔐 Acceso al Administrador

**URL:** `http://localhost:5000/admin/login`

```
Usuario: adm
Contraseña: admin123456789
```

---

## 👤 Nuevas Rutas Disponibles

### Público
| Ruta | Descripción |
|------|-------------|
| `/` | Página principal con eventos |
| `/user/register` | Registro de nuevos usuarios |
| `/event/<id>/buy` | Comprar boletos para evento |
| `/ticket/<número>/print` | Ver/imprimir boleto |

### Administrador (requiere login)
| Ruta | Descripción |
|------|-------------|
| `/admin/login` | Login del panel |
| `/admin/dashboard` | Panel principal |
| `/admin/history` | Historial de acciones ⭐ NUEVA |
| `/admin/event/create` | Crear evento |
| `/admin/event/<id>/edit` | Editar evento |
| `/admin/event/<id>/delete` | Eliminar evento |
| `/admin/event/<id>/raffle` | Realizar sorteo |
| `/admin/event/<id>/tickets` | Ver boletos |
| `/admin/coupons` | Gestionar cupones |
| `/admin/reports` | Ver reportes |

---

## 📊 Base de Datos - Nuevas Tablas

### Tabla `users` (Registro de participantes)
```
id              - ID único
first_name      - Nombre
last_name       - Apellido
phone           - Teléfono
email           - Email (único)
id_number       - Carnet (único)
created_at      - Fecha de registro
```

### Tabla `action_history` (Historial de operaciones)
```
id              - ID único
action_type     - CREATE, UPDATE, DELETE
entity_type     - event, ticket, user, etc.
entity_id       - ID de la entidad
changes         - Cambios en JSON
created_at      - Timestamp
is_redo         - Para futuro sistema undo/redo
```

---

## 🎯 Casos de Uso

### 1️⃣ Crear Evento
1. Ingresa como admin
2. Ve al dashboard
3. Completa "Crear nuevo evento"
4. Sube imágenes (evento, premio, fondo boleto, ubicación)
5. Click "Crear evento"
→ **Se registra automáticamente en historial**

### 2️⃣ Registrar Usuario
1. Desde página principal → "Registrarse"
2. Completa: Nombre, Apellido, Carnet, Teléfono, Email
3. Click "Registrarse"
→ **Se guarda en tabla `users` y se registra en historial**

### 3️⃣ Comprar Boleto
1. En página principal, elige evento
2. Completa datos (puede reutilizar datos de registro)
3. Elige cantidad y cupón (opcional)
4. Compra boleto
→ **Se registra acción en historial**

### 4️⃣ Imprimir Boleto
1. Después de compra: `/ticket/<número>/print`
2. O desde panel: Ver boleto → Imprimir
3. Opciones:
   - 🖨️ Click "Imprimir" (Ctrl+P)
   - ⬇️ Click "Descargar QR" para guardar código

### 5️⃣ Ver Historial
1. Ingresa como admin
2. Panel → "Historial"
3. Ve todas las operaciones:
   - Crear/editar/eliminar eventos
   - Boletos vendidos
   - Usuarios registrados
4. Click "Ver detalles" para información completa

---

## 🔧 Configuración

Edita `.env`:

```bash
# Credenciales
ADMIN_USER=adm
ADMIN_PASSWORD=admin123456789
SECRET_KEY=tu-clave-secreta-aqui
PORT=5000
```

---

## 📱 Características por Pantalla

### 🏠 Página Principal
- ✅ Ver eventos activos y cerrados
- ✅ Link "Registrarse" (NUEVO)
- ✅ Link "Admin"

### 📝 Registro de Usuario (NUEVO)
- ✅ Formulario validado
- ✅ Validaciones de email único, carnet único
- ✅ Validación de formato (teléfono, email)
- ✅ Guardar en tabla `users`

### 🎫 Compra de Boleto
- ✅ Validaciones habituales
- ✅ Número de boleto único por evento
- ✅ Cupones con descuento
- ✅ QR generado en servidor (no se puede falsificar)
- ✅ Confirmación de compra

### 🖨️ Impresión de Boleto (MEJORADO)
- ✅ Diseño profesional
- ✅ QR embebido
- ✅ Botón imprimir optimizado
- ✅ Descarga de QR como PNG
- ✅ Estilos CSS para impresión

### 📊 Panel Admin
- ✅ Dashboard con estadísticas
- ✅ Gestión de eventos
- ✅ Gestión de cupones
- ✅ Reportes
- ✅ **Historial (NUEVO)** ← Ver todas las operaciones

### 📜 Historial (NUEVO)
- ✅ Tabla con todas las acciones
- ✅ Filtrado por fecha
- ✅ Información de cambios
- ✅ Color por tipo: Verde (CREATE), Amarillo (UPDATE), Rojo (DELETE)
- ✅ Expandible para ver detalles JSON

---

## ⚠️ Importante

1. **Base de datos**: Se crea automáticamente en primer inicio
2. **Credenciales**: Cambia en `.env` antes de producción
3. **Imágenes**: Se guardan en `static/uploads/`
4. **Histórico**: Se registra TODA operación para auditoría
5. **QR**: Generado en servidor (seguro, no falsificable)

---

## 🐛 Troubleshooting

### Error: "No existe tabla users"
→ Elimina `tickets.db` y reinicia (se recrea con nuevas tablas)

### Error: "Usuario no existe"
→ Asegúrate de usar credenciales correctas: `adm` / `admin123456789`

### No veo el historial
→ Crea primero un evento → se debe registrar automáticamente

### No se imprime bien el boleto
→ Usa navegador moderno, prueba con Firefox o Chrome

---

## 📞 Soporte

Para más información, revisa:
- `CHANGES.md` - Detalles técnicos de cambios
- `README.md` - Instalación y estructura
- `app.py` - Código fuente con comentarios

---

**¡Listo para usar! 🚀**
