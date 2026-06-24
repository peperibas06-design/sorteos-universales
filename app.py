import os
import sqlite3
import io
import random
import re
import datetime
import base64
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, jsonify
from werkzeug.utils import secure_filename
import qrcode
from openpyxl import Workbook
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'tickets.db')
TICKET_PRICE = 20
MAX_QUANTITY = 50
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ADMIN_USER = os.environ.get('ADMIN_USER', 'adm')
ADMIN_PASS = os.environ.get('ADMIN_PASSWORD', 'admin123456789')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey12345')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            event_date TEXT,
            created_at TEXT NOT NULL,
            closed INTEGER DEFAULT 0,
            winners TEXT,
            max_tickets INTEGER DEFAULT 250002,
            tickets_sold INTEGER DEFAULT 0,
            prize_image TEXT,
            location_image TEXT,
            ticket_bg_image TEXT,
            event_image TEXT,
            prize_count INTEGER DEFAULT 1
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            qr_payload TEXT,
            created_at TEXT NOT NULL,
            event_id INTEGER,
            event_ticket_number INTEGER,
            id_number TEXT,
            birthdate TEXT,
            coupon_code TEXT
        )'''
    )

    # Ensure uniqueness of ticket_number per event (composite unique index)
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_event_ticket_unique ON tickets(event_id, ticket_number)")

    # If there is a legacy global UNIQUE on ticket_number, migrate table to new schema
    # Detect unique indexes that only include ticket_number
    indexes = [row for row in cur.execute("PRAGMA index_list('tickets')").fetchall()]
    need_migrate = False
    for idx in indexes:
        if idx['unique']:
            idx_name = idx['name']
            cols = [c['name'] for c in cur.execute(f"PRAGMA index_info('{idx_name}')").fetchall()]
            if cols == ['ticket_number']:
                need_migrate = True
                break

    if need_migrate:
        # Recreate tickets table without global UNIQUE constraint
        cur.execute('ALTER TABLE tickets RENAME TO tickets_old')
        cur.execute(
            '''CREATE TABLE tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                qr_payload TEXT,
                created_at TEXT NOT NULL,
                event_id INTEGER,
                event_ticket_number INTEGER,
                id_number TEXT,
                birthdate TEXT,
                coupon_code TEXT
            )'''
        )
        # Recreate composite unique index
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_event_ticket_unique ON tickets(event_id, ticket_number)")
        # Copy data: set ticket_number to event_ticket_number if present, else keep old
        old_rows = cur.execute('SELECT * FROM tickets_old').fetchall()
        for row in old_rows:
            new_ticket_number = row['event_ticket_number'] if row['event_ticket_number'] else row['ticket_number']
            cur.execute(
                'INSERT INTO tickets (id, ticket_number, first_name, last_name, phone, email, qr_payload, created_at, event_id, event_ticket_number, id_number, birthdate, coupon_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (row['id'], new_ticket_number, row['first_name'], row['last_name'], row['phone'], row['email'], row['qr_payload'], row['created_at'], row['event_id'], row['event_ticket_number'], row['id_number'], row['birthdate'], row['coupon_code'])
            )
        cur.execute('DROP TABLE tickets_old')
        conn.commit()

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS admin_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS admin_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            id_number TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percent INTEGER,
            uses_remaining INTEGER,
            event_id INTEGER,
            active INTEGER DEFAULT 1,
            created_at TEXT
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS raffles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            ticket_number INTEGER,
            winner_name TEXT,
            drawn_at TEXT,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )'''
    )

    cur.execute(
        '''CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            changes TEXT,
            created_at TEXT NOT NULL,
            is_redo INTEGER DEFAULT 0
        )'''
    )

    conn.commit()
    conn.close()


def ensure_column(table, column, definition):
    conn = get_db()
    cur = conn.cursor()
    existing = [row['name'] for row in cur.execute(f"PRAGMA table_info({table})")]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute('SELECT value FROM admin_settings WHERE key = ?', (key,)).fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO admin_settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_storage):
    if file_storage and file_storage.filename and allowed_file(file_storage.filename):
        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        safe_name = f"{uuid4().hex}.{ext}"
        destination = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
        file_storage.save(destination)
        return safe_name
    return None


def is_valid_email(email):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


def is_valid_phone(phone):
    digits = re.sub(r'\D', '', phone or '')
    return len(digits) >= 7


def calculate_age(birthdate):
    try:
        dob = datetime.datetime.strptime(birthdate, '%Y-%m-%d').date()
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return age
    except Exception:
        return 0


def get_event(event_id):
    conn = get_db()
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()
    return event


def get_ticket(ticket_number, event_id=None):
    conn = get_db()
    if event_id:
        ticket = conn.execute('SELECT * FROM tickets WHERE ticket_number = ? AND event_id = ?', (ticket_number, event_id)).fetchone()
    else:
        ticket = conn.execute('SELECT * FROM tickets WHERE ticket_number = ? ORDER BY id DESC', (ticket_number,)).fetchone()
    conn.close()
    return ticket


def get_coupon(code, event_id=None):
    conn = get_db()
    cur = conn.cursor()
    coupon = cur.execute(
        'SELECT * FROM coupons WHERE UPPER(code) = UPPER(?) AND active = 1',
        (code.strip(),)
    ).fetchone()
    conn.close()
    if coupon and coupon['event_id'] not in (None, 0) and coupon['event_id'] != event_id:
        return None
    return coupon


def get_next_ticket_number(conn, event_id=None):
    try:
        cursor = conn.execute('SELECT MAX(ticket_number) as maxn FROM tickets')
        row = cursor.fetchone()
        if row and row['maxn'] is not None:
            try:
                return int(row['maxn']) + 1
            except ValueError:
                pass
    except Exception:
        pass

        while True:
            random_num = random.randint(1000000, 9999999)
            cursor = conn.execute('SELECT id FROM tickets WHERE ticket_number = ?', (random_num,))
            existing = cursor.fetchone()
            if not existing:
                return random_num

def is_ticket_number_available(ticket_number):
    """Verifica si un número de boleto está disponible."""
    conn = get_db()
    exists = conn.execute('SELECT id FROM tickets WHERE ticket_number = ?', (ticket_number,)).fetchone()
    conn.close()
    return not exists


def is_ci_available_for_event(id_number, event_id):
    """Verifica si un CI no ha comprado boletos en este evento."""
    conn = get_db()
    exists = conn.execute('SELECT id FROM tickets WHERE id_number = ? AND event_id = ?', (id_number, event_id)).fetchone()
    conn.close()
    return not exists

def is_ticket_number_available_for_event(ticket_number, event_id):
    """Verifica si un número de boleto está disponible dentro de un evento."""
    conn = get_db()
    exists = conn.execute('SELECT id FROM tickets WHERE ticket_number = ? AND event_id = ?', (ticket_number, event_id)).fetchone()
    conn.close()
    return not exists


def generate_qr_data_url(text):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(text or '')
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffered = io.BytesIO()
    img.save(buffered, format='PNG')
    buffered.seek(0)
    data = buffered.read()
    return 'data:image/png;base64,' + base64.b64encode(data).decode('utf-8')


@app.context_processor
def inject_globals():
    """Disponible en TODAS las plantillas, sin que cada ruta tenga que pasarlo."""
    return {
        'site_settings': {
            'page_text_color': get_setting('page_text_color', '#F5F1E6'),
            'page_button_color': get_setting('page_button_color', '#F2B705'),
            'page_button_text_color': get_setting('page_button_text_color', '#211B12'),
            'page_background': get_setting('page_background', ''),
        },
        'current_year': datetime.datetime.now().year,
    }


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)

    return wrapper


@app.route('/')
def home():
    conn = get_db()
    active_events = conn.execute('SELECT * FROM events WHERE closed = 0 ORDER BY event_date').fetchall()
    closed_events = conn.execute('SELECT * FROM events WHERE closed = 1 ORDER BY event_date DESC').fetchall()
    conn.close()
    settings = {
        'page_text_color': get_setting('page_text_color', '#333333'),
        'page_button_color': get_setting('page_button_color', '#007bff'),
        'page_button_text_color': get_setting('page_button_text_color', '#ffffff'),
        'page_background': get_setting('page_background', ''),
    }
    admin_note = get_setting('admin_note', '')
    default_qr = get_setting('default_qr', '')
    return render_template('index.html', active_events=active_events, closed_events=closed_events, settings=settings, admin_note=admin_note, default_qr=default_qr, ticket_price=TICKET_PRICE)


@app.route('/event/<int:event_id>/buy', methods=['GET', 'POST'])
def buy_ticket(event_id):
    event = get_event(event_id)
    if not event:
        return redirect(url_for('home'))

    if event['closed'] or event['tickets_sold'] >= event['max_tickets']:
        return render_template('sold_out.html', event_name=event['name'], max_tickets=event['max_tickets'])

    error = None
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        id_number = request.form.get('id_number', '').strip()
        birthdate = request.form.get('birthdate', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        quantity = request.form.get('quantity', '1')
        coupon_code = request.form.get('coupon_code', '').strip()
        custom_ticket_number = request.form.get('custom_ticket_number', '').strip()

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        if not first_name or not last_name:
            error = 'Debes ingresar nombre y apellido.'
        elif len(id_number) < 6:
            error = 'El carnet de identidad debe tener al menos 6 caracteres.'
        elif calculate_age(birthdate) < 18:
            error = 'Debes ser mayor de 18 años para comprar boletos.'
        elif not is_valid_phone(phone):
            error = 'Ingresa un teléfono válido con al menos 7 dígitos.'
        elif not is_valid_email(email):
            error = 'Ingresa un correo electrónico válido.'
        elif quantity < 1 or quantity > MAX_QUANTITY:
            error = f'Puedes comprar entre 1 y {MAX_QUANTITY} boletos.'
        elif event['tickets_sold'] + quantity > event['max_tickets']:
            error = f'Solo quedan {event["max_tickets"] - event["tickets_sold"]} boletos disponibles.'
        elif not is_ci_available_for_event(id_number, event['id']):
            error = 'Este carnet de identidad ya tiene un boleto registrado para este evento.'

        coupon = None
        discount_percent = 0
        if not error and coupon_code:
            coupon = get_coupon(coupon_code, event['id'])
            if not coupon:
                error = 'Cupón inválido o no aplicable para este evento.'
            elif coupon['uses_remaining'] <= 0:
                error = 'Este cupón ya no tiene usos disponibles.'
            else:
                discount_percent = coupon['discount_percent'] or 0

        custom_num = None
        if not error and custom_ticket_number:
            # Validar si el usuario quiere un número específico
            try:
                custom_num = int(custom_ticket_number)
                if not is_ticket_number_available_for_event(custom_num, event['id']):
                    error = f'El boleto #{custom_num} ya está vendido en este evento. Escoge otro o deja el campo vacío para asignar uno automáticamente.'
                elif quantity > 1:
                    error = 'Si seleccionas un número específico, solo puedes comprar 1 boleto.'
            except ValueError:
                error = 'El número de boleto debe ser un número entero.'

        if not error:
            conn = get_db()
            cur = conn.cursor()
            tickets = []
            created_at = datetime.datetime.now().isoformat()

            try:
                for i in range(quantity):
                    event_ticket_number = event['tickets_sold'] + i + 1
                    ticket_number = custom_num if (custom_num and i == 0) else event_ticket_number

                    # El QR se genera en el servidor (no lo manda el cliente) para
                    # que no se pueda falsificar el boleto.
                    qr_text = f"EVT{event['id']}-TK{event_ticket_number}-{uuid4().hex[:8].upper()}"

                    cur.execute(
                        '''INSERT INTO tickets
                           (ticket_number, first_name, last_name, phone, email, qr_payload,
                            created_at, event_id, event_ticket_number, id_number, birthdate, coupon_code)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (ticket_number, first_name, last_name, phone, email, qr_text,
                         created_at, event['id'], event_ticket_number, id_number, birthdate,
                         coupon['code'] if coupon else None)
                    )

                    tickets.append({
                        'ticket_number': ticket_number,
                        'event_ticket_number': event_ticket_number,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'qr_payload': qr_text,
                    })

                conn.execute(
                    'UPDATE events SET tickets_sold = tickets_sold + ? WHERE id = ?',
                    (quantity, event['id'])
                )

                if coupon:
                    conn.execute(
                        'UPDATE coupons SET uses_remaining = uses_remaining - 1 WHERE id = ?',
                        (coupon['id'],)
                    )

                conn.commit()
                # Registrar la acción en el historial
                import json
                log_action('CREATE', 'ticket', event['id'], {
                    'quantity': quantity,
                    'buyer': f"{first_name} {last_name}",
                    'email': email
                })
            except sqlite3.IntegrityError:
                conn.rollback()
                conn.close()
                error = ('Uno de los números de boleto que intentabas usar fue tomado justo '
                         'ahora por otra persona. Por favor intenta de nuevo.')
            else:
                conn.close()

            if not error:
                subtotal = TICKET_PRICE * quantity
                total_price = subtotal * (100 - discount_percent) / 100

                return render_template(
                    'ticket_confirmation.html',
                    event=event,
                    tickets=tickets,
                    subtotal=subtotal,
                    discount_percent=discount_percent,
                    total_price=total_price,
                )

    return render_template(
        'buy_ticket.html',
        event=event,
        error=error,
        ticket_price=TICKET_PRICE,
        max_quantity=MAX_QUANTITY,
    )


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Usuario o contraseña incorrectos.')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    events = conn.execute('SELECT * FROM events ORDER BY event_date DESC').fetchall()
    conn.close()
    settings = {
        'page_text_color': get_setting('page_text_color', '#333333'),
        'page_button_color': get_setting('page_button_color', '#007bff'),
        'page_button_text_color': get_setting('page_button_text_color', '#ffffff'),
        'page_background': get_setting('page_background', ''),
    }
    admin_note = get_setting('admin_note', '')
    default_qr = get_setting('default_qr', '')
    return render_template('admin_dashboard.html', events=events, settings=settings, admin_note=admin_note, default_qr=default_qr)


@app.route('/admin/api/sales_data')
@admin_required
def admin_sales_data():
    """Devuelve datos de ventas por evento en formato JSON para gráficos."""
    conn = get_db()
    events = conn.execute('SELECT id, name, max_tickets, tickets_sold FROM events ORDER BY event_date DESC LIMIT 10').fetchall()
    conn.close()
    
    data = {
        'labels': [e['name'][:20] for e in events],
        'sold': [e['tickets_sold'] for e in events],
        'remaining': [e['max_tickets'] - e['tickets_sold'] for e in events],
    }
    return jsonify(data)


@app.route('/admin/settings', methods=['POST'])
@admin_required
def admin_settings():
    set_setting('page_text_color', request.form.get('page_text_color', '#333333'))
    set_setting('page_button_color', request.form.get('page_button_color', '#007bff'))
    set_setting('page_button_text_color', request.form.get('page_button_text_color', '#ffffff'))

    background = request.files.get('page_background')
    if background and background.filename:
        filename = save_uploaded_file(background)
        if filename:
            set_setting('page_background', filename)

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/notes', methods=['POST'])
@admin_required
def admin_notes():
    set_setting('admin_note', request.form.get('content', ''))
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/upload_qr', methods=['POST'])
@admin_required
def admin_upload_qr():
    qrfile = request.files.get('qrfile')
    if qrfile and qrfile.filename:
        filename = save_uploaded_file(qrfile)
        if filename:
            set_setting('default_qr', filename)
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/coupons', methods=['GET', 'POST'])
@admin_required
def admin_coupons():
    conn = get_db()
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        discount = int(request.form.get('discount_percent', 0))
        uses = int(request.form.get('uses_remaining', 1))
        event_id = request.form.get('event_id')
        event_id = int(event_id) if event_id else None
        created_at = datetime.datetime.now().isoformat()
        conn.execute('INSERT INTO coupons (code, discount_percent, uses_remaining, event_id, active, created_at) VALUES (?, ?, ?, ?, 1, ?)', (code, discount, uses, event_id, created_at))
        conn.commit()
    events = conn.execute('SELECT id, name FROM events ORDER BY event_date DESC').fetchall()
    coupons = conn.execute('SELECT * FROM coupons ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin_coupons.html', events=events, coupons=coupons)


@app.route('/admin/coupons/delete/<int:coupon_id>', methods=['POST'])
@admin_required
def admin_delete_coupon(coupon_id):
    conn = get_db()
    conn.execute('DELETE FROM coupons WHERE id = ?', (coupon_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_coupons'))


@app.route('/admin/reports')
@admin_required
def admin_reports():
    conn = get_db()
    summary = conn.execute('SELECT COUNT(*) AS total_tickets, COUNT(DISTINCT email) AS unique_emails, SUM(CASE WHEN coupon_code IS NOT NULL AND coupon_code != "" THEN 1 ELSE 0 END) AS coupon_tickets, COUNT(*) AS total_raffles FROM tickets LEFT JOIN raffles ON tickets.event_id = raffles.event_id').fetchone()
    events_report = conn.execute('SELECT e.id, e.name, e.max_tickets, e.tickets_sold, COUNT(DISTINCT t.email) AS unique_buyers, SUM(CASE WHEN t.coupon_code != "" THEN 1 ELSE 0 END) AS coupon_count FROM events e LEFT JOIN tickets t ON e.id = t.event_id GROUP BY e.id ORDER BY e.event_date DESC').fetchall()
    coupons_report = conn.execute('SELECT code, discount_percent, COUNT(*) AS used, uses_remaining FROM coupons GROUP BY code ORDER BY used DESC').fetchall()
    conn.close()
    return render_template('admin_reports.html', summary=summary, events_report=events_report, coupons_report=coupons_report)


@app.route('/admin/event/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_event(event_id):
    event = get_event(event_id)
    if not event:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        max_tickets = int(request.form.get('max_tickets', event['max_tickets']))
        prize_count = int(request.form.get('prize_count', event['prize_count'] or 1))
        description = request.form.get('description', event['description'])
        location_image = request.files.get('location_image')
        event_image = request.files.get('event_image')
        ticket_bg_image = request.files.get('ticket_bg_image')
        prize_image = request.files.get('prize_image')

        updates = {
            'max_tickets': max_tickets,
            'prize_count': prize_count,
            'description': description,
        }

        if location_image and location_image.filename:
            updates['location_image'] = save_uploaded_file(location_image)
        if event_image and event_image.filename:
            updates['event_image'] = save_uploaded_file(event_image)
        if ticket_bg_image and ticket_bg_image.filename:
            updates['ticket_bg_image'] = save_uploaded_file(ticket_bg_image)
        if prize_image and prize_image.filename:
            updates['prize_image'] = save_uploaded_file(prize_image)

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [event_id]
        conn = get_db()
        conn.execute(f'UPDATE events SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        return redirect(url_for('admin_edit_event', event_id=event_id))

    return render_template('admin_edit_event.html', event=event)


@app.route('/admin/event/<int:event_id>/raffle', methods=['GET', 'POST'])
@admin_required
def admin_raffle(event_id):
    event = get_event(event_id)
    if not event:
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    tickets = conn.execute('SELECT event_ticket_number, first_name, last_name FROM tickets WHERE event_id = ? ORDER BY event_ticket_number', (event_id,)).fetchall()
    raffle = conn.execute('SELECT * FROM raffles WHERE event_id = ? ORDER BY drawn_at DESC LIMIT 1', (event_id,)).fetchone()
    if request.method == 'POST' and tickets:
        winner = random.choice(tickets)
        conn.execute('INSERT INTO raffles (event_id, ticket_number, winner_name, drawn_at) VALUES (?, ?, ?, ?)', (event_id, winner['event_ticket_number'], f"{winner['first_name']} {winner['last_name']}", datetime.datetime.now().isoformat()))
        conn.commit()
        raffle = conn.execute('SELECT * FROM raffles WHERE event_id = ? ORDER BY drawn_at DESC LIMIT 1', (event_id,)).fetchone()
    conn.close()
    return render_template('admin_raffle.html', event=event, tickets=tickets, raffle=raffle)


@app.route('/admin/event/<int:event_id>/tickets')
@admin_required
def admin_event_tickets(event_id):
    event = get_event(event_id)
    if not event:
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    tickets = conn.execute('SELECT * FROM tickets WHERE event_id = ? ORDER BY event_ticket_number', (event_id,)).fetchall()
    conn.close()
    return render_template('admin_event_tickets.html', event=event, tickets=tickets)


@app.route('/event/<int:event_id>/export')
@admin_required
def admin_export_event(event_id):
    conn = get_db()
    event = get_event(event_id)
    tickets = conn.execute('SELECT * FROM tickets WHERE event_id = ? ORDER BY event_ticket_number', (event_id,)).fetchall()
    conn.close()

    wb = Workbook()
    sheet = wb.active
    sheet.title = 'Boletos'
    sheet.append(['Ticket', 'Nombre', 'Apellido', 'Telefono', 'Email', 'CI', 'Fecha Nac', 'QR Texto', 'Fecha Compra', 'Numero Evento'])
    for t in tickets:
        sheet.append([t['ticket_number'], t['first_name'], t['last_name'], t['phone'], t['email'], t['id_number'], t['birthdate'], t['qr_payload'], t['created_at'], t['event_ticket_number']])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name=f'event_{event_id}_tickets.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


@app.route('/event/<int:event_id>/close', methods=['POST'])
@admin_required
def admin_close_event(event_id):
    conn = get_db()
    conn.execute('UPDATE events SET closed = 1 WHERE id = ?', (event_id,))
    conn.commit()
    log_action('UPDATE', 'event', event_id, {'status': 'closed'})
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/event/create', methods=['POST'])
@admin_required
def create_event():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    event_date = request.form.get('event_date', '').strip()
    max_tickets = int(request.form.get('max_tickets', 100))
    prize_count = int(request.form.get('prize_count', 1))
    event_image_file = request.files.get('event_image')
    prize_image_file = request.files.get('prize_image')
    ticket_bg_image_file = request.files.get('ticket_bg_image')
    location_image_file = request.files.get('location_image')
    event_image = save_uploaded_file(event_image_file) if event_image_file and event_image_file.filename else None
    prize_image = save_uploaded_file(prize_image_file) if prize_image_file and prize_image_file.filename else None
    ticket_bg_image = save_uploaded_file(ticket_bg_image_file) if ticket_bg_image_file and ticket_bg_image_file.filename else None
    location_image = save_uploaded_file(location_image_file) if location_image_file and location_image_file.filename else None
    created_at = datetime.datetime.now().isoformat()
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO events (name, description, event_date, created_at, max_tickets, prize_count, event_image, prize_image, ticket_bg_image, location_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (name, description, event_date, created_at, max_tickets, prize_count, event_image, prize_image, ticket_bg_image, location_image))
    conn.commit()
    event_id = cur.lastrowid
    log_action('CREATE', 'event', event_id, {
        'name': name,
        'max_tickets': max_tickets,
        'prize_count': prize_count
    })
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/event/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = get_event(event_id)
    conn = get_db()
    conn.execute('DELETE FROM tickets WHERE event_id = ?', (event_id,))
    conn.execute('DELETE FROM raffles WHERE event_id = ?', (event_id,))
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    log_action('DELETE', 'event', event_id, {'name': event['name'] if event else 'N/A'})
    conn.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/ticket/<int:ticket_number>/qr')
def download_qr(ticket_number):
    # Optional event_id as query param to disambiguate when ticket numbers reset per event
    event_id = request.args.get('event_id', None, type=int)
    ticket = get_ticket(ticket_number, event_id=event_id)
    if not ticket:
        return redirect(url_for('home'))

    qr = qrcode.make(ticket['qr_payload'] or f"Ticket {ticket['event_ticket_number']}")
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    filename = f"ticket_{ticket['event_ticket_number']}_qr.png" if ticket else f"ticket_{ticket_number}_qr.png"
    return send_file(img_io, mimetype='image/png', download_name=filename)


def log_action(action_type, entity_type, entity_id, changes=None):
    """Registra una acción en el historial para undo/redo."""
    import json
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO action_history (action_type, entity_type, entity_id, changes, created_at) VALUES (?, ?, ?, ?, ?)',
        (action_type, entity_type, entity_id, json.dumps(changes) if changes else None, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_action_history(entity_type=None, limit=50):
    """Obtiene el historial de acciones."""
    conn = get_db()
    if entity_type:
        history = conn.execute('SELECT * FROM action_history WHERE entity_type = ? ORDER BY created_at DESC LIMIT ?', (entity_type, limit)).fetchall()
    else:
        history = conn.execute('SELECT * FROM action_history ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return history


@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    """Registro de usuarios."""
    error = None
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        id_number = request.form.get('id_number', '').strip()

        if not first_name or not last_name:
            error = 'Debes ingresar nombre y apellido.'
        elif len(id_number) < 6:
            error = 'El carnet de identidad debe tener al menos 6 caracteres.'
        elif not is_valid_phone(phone):
            error = 'Ingresa un teléfono válido con al menos 7 dígitos.'
        elif not is_valid_email(email):
            error = 'Ingresa un correo electrónico válido.'
        else:
            conn = get_db()
            try:
                conn.execute(
                    'INSERT INTO users (first_name, last_name, phone, email, id_number, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (first_name, last_name, phone, email, id_number, datetime.datetime.now().isoformat())
                )
                conn.commit()
                log_action('CREATE', 'user', None, {'name': f"{first_name} {last_name}", 'email': email})
                conn.close()
                flash('¡Registro completado exitosamente!', 'success')
                return redirect(url_for('home'))
            except sqlite3.IntegrityError:
                conn.close()
                error = 'El email o carnet de identidad ya está registrado.'

    return render_template('register_user.html', error=error)


@app.route('/ticket/<int:ticket_number>/print')
def print_ticket(ticket_number):
    """Descargar boleto como PDF imprimible."""
    event_id = request.args.get('event_id', None, type=int)
    ticket = get_ticket(ticket_number, event_id=event_id)
    if not ticket:
        return redirect(url_for('home'))
    event = get_event(ticket['event_id'])
    return render_template('print_ticket.html', ticket=ticket, event=event)


@app.route('/admin/history')
@admin_required
def admin_history():
    """Ver historial de acciones para undo/redo."""
    conn = get_db()
    history = conn.execute('SELECT * FROM action_history ORDER BY created_at DESC LIMIT 100').fetchall()
    conn.close()
    return render_template('admin_history.html', history=history)


import os

if __name__ == "__main__":
    init_db()
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto)
    