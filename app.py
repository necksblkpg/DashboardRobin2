from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
from dataclasses import dataclass
from typing import List
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

secret_key = os.environ.get("FLASK_SECRET_KEY")
if not secret_key:
    raise ValueError("FLASK_SECRET_KEY är inte satt i miljövariablerna.")

app.secret_key = secret_key

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

@dataclass
class Program:
    id: int
    name: str
    description: str
    url: str
    category: str
    icon: str

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT,
            category TEXT,
            icon TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            program_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, program_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (program_id) REFERENCES programs(id)
        )
    ''')
    conn.commit()

    # Kolla om programs är tom
    cur = conn.execute('SELECT COUNT(*) as count FROM programs')
    count = cur.fetchone()['count']
    if count == 0:
        initial_data = [
            {"name": "Svara på Kundrecensioner", "description": "Svara enkelt på kundfeedback", "url": "#", "category": "Customer service", "icon": "fa-star"},
            {"name": "Centra Translate", "description": "Textöversättning med språksidentifiering", "url": "https://translatedescdisplay.replit.app/login", "category": "Translation", "icon": "fa-language"},
            {"name": "Storyblok Translate", "description": "Dokumentöversättning och formatering", "url": "#", "category": "Translation", "icon": "fa-language"},
            {"name": "Looker Studio Report", "description": "Affärsanalys och rapportering i realtid", "url": "https://lookerstudio.google.com/u/0/reporting/751e0957-c4b2-4377-ad71-52d7f2e0da62/page/IJmAE", "category": "Performance", "icon": "fa-chart-line"},
            {"name": "Inköpsprogram", "description": "Håll koll på lagerstatus och beställningar", "url": "#", "category": "Inköp", "icon": "fa-box-open"}
        ]
        for prog in initial_data:
            conn.execute('INSERT INTO programs (name, description, url, category, icon) VALUES (?, ?, ?, ?, ?)',
                         (prog["name"], prog["description"], prog["url"], prog["category"], prog["icon"]))
        conn.commit()
    conn.close()

def load_programs_from_db() -> List[Program]:
    conn = get_db_connection()
    rows = conn.execute('SELECT id, name, description, url, category, icon FROM programs ORDER BY category, name').fetchall()
    conn.close()
    programs = [Program(id=row["id"], name=row["name"], description=row["description"],
                         url=row["url"], category=row["category"], icon=row["icon"]) for row in rows]
    return programs

@app.before_request
def require_login():
    # Lista av endpoints som ska få vara öppna utan inloggning
    open_endpoints = {'login', 'register', 'static'}

    # request.endpoint är namnet på den route-funktion som ska anropas
    # t.ex. om @app.route('/login') def login(): -> endpoint "login"
    # 'static' används för statiska filer.

    if request.endpoint not in open_endpoints and 'user_id' not in session:
        return redirect(url_for('login'))

@app.route('/')
def index():
    query = request.args.get("sok", "").strip().lower()
    programs = load_programs_from_db()

    user_id = session.get('user_id', None)
    user_favorites = []
    if user_id:
        conn = get_db_connection()
        fav_rows = conn.execute('SELECT program_id FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
        user_favorites = [r['program_id'] for r in fav_rows]
        conn.close()

    categories = {}
    for p in programs:
        if p.category not in categories:
            categories[p.category] = []
        categories[p.category].append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'url': p.url,
            'category': p.category,
            'icon': p.icon,
            'is_fav': (p.id in user_favorites)
        })

    if query:
        filtered_categories = {}
        for cat, prog_list in categories.items():
            matchade = [pr for pr in prog_list if query in pr['name'].lower() or query in pr['description'].lower()]
            if matchade:
                filtered_categories[cat] = matchade
        categories = filtered_categories

    return render_template('index.html', categories=categories, query=query)

@app.route('/om')
def about():
    return render_template('about.html')

@app.route('/program/<string:program_name>')
def show_program(program_name: str):
    conn = get_db_connection()
    row = conn.execute('''
        SELECT id, name, description, url, category, icon 
        FROM programs 
        WHERE LOWER(REPLACE(name, ' ', '_')) = ?
    ''', (program_name.lower(),)).fetchone()
    conn.close()

    if row:
        chosen = Program(id=row["id"], name=row["name"], description=row["description"], 
                         url=row["url"], category=row["category"], icon=row["icon"])
        return render_template('program.html', program=chosen)
    else:
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    # Här krävs inloggning pga before_request
    conn = get_db_connection()
    user = conn.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    if not user or user['username'] != 'admin':
        conn.close()
        return "Åtkomst nekad", 403

    rows = conn.execute('SELECT id, name, description, url, category, icon FROM programs ORDER BY category, name').fetchall()
    conn.close()
    return render_template('admin.html', programs=rows)

@app.route('/admin/add', methods=['POST'])
def admin_add():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    url = request.form.get('url', '').strip()
    category = request.form.get('category', '').strip()
    icon = request.form.get('icon', '').strip()

    if name:
        conn = get_db_connection()
        conn.execute('INSERT INTO programs (name, description, url, category, icon) VALUES (?, ?, ?, ?, ?)',
                     (name, description, url, category, icon))
        conn.commit()
        conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:program_id>', methods=['POST'])
def admin_delete(program_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM programs WHERE id = ?', (program_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/edit/<int:program_id>', methods=['GET', 'POST'])
def admin_edit(program_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        url = request.form.get('url', '').strip()
        category = request.form.get('category', '').strip()
        icon = request.form.get('icon', '').strip()

        conn.execute('UPDATE programs SET name = ?, description = ?, url = ?, category = ?, icon = ? WHERE id = ?',
                     (name, description, url, category, icon, program_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    else:
        row = conn.execute('SELECT id, name, description, url, category, icon FROM programs WHERE id = ?', (program_id,)).fetchone()
        conn.close()
        if row:
            prog = Program(id=row["id"], name=row["name"], description=row["description"], url=row["url"], category=row["category"], icon=row["icon"])
            return render_template('edit_program.html', program=prog)
        else:
            return redirect(url_for('admin'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Behöver vara öppen innan inlogg, lägg därför till "register" i open_endpoints i before_request
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            conn = get_db_connection()
            existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing:
                conn.close()
                return "Användarnamnet upptaget"
            pw_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?,?)', (username, pw_hash))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Behöver vara öppen, lägg "login" i open_endpoints i before_request
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        row = conn.execute('SELECT id, username, password_hash FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            session['user_id'] = row['id']
            return redirect(url_for('index'))
        else:
            return "Felaktigt användarnamn eller lösenord"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/favorite/<int:program_id>', methods=['POST'])
def favorite_program(program_id):
    user_id = session['user_id']
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM favorites WHERE user_id = ? AND program_id = ?', (user_id, program_id)).fetchone()
    if existing:
        conn.execute('DELETE FROM favorites WHERE user_id = ? AND program_id = ?', (user_id, program_id))
    else:
        conn.execute('INSERT INTO favorites (user_id, program_id) VALUES (?,?)', (user_id, program_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
