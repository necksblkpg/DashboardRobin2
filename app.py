import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from dataclasses import dataclass
from typing import List

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "hemlig_nyckel_2024_modern"

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
    # Skapa tabellen om den inte finns
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
    conn.commit()

    # Kolla om tabellen är tom. Om ja, lägg till initial data.
    cur = conn.execute('SELECT COUNT(*) as count FROM programs')
    count = cur.fetchone()['count']
    if count == 0:
        # Lägg in initial data som fanns i programs.json
        initial_data = [
            {
                "name": "Svara på Kundrecensioner",
                "description": "Svara enkelt på kundfeedback",
                "url": "#",
                "category": "Customer service",
                "icon": "fa-star"
            },
            {
                "name": "Centra Translate",
                "description": "Textöversättning med språksidentifiering",
                "url": "https://translatedescdisplay.replit.app/login",
                "category": "Translation",
                "icon": "fa-language"
            },
            {
                "name": "Storyblok Translate",
                "description": "Dokumentöversättning och formatering",
                "url": "#",
                "category": "Translation",
                "icon": "fa-language"
            },
            {
                "name": "Looker Studio Report",
                "description": "Affärsanalys och rapportering i realtid",
                "url": "https://lookerstudio.google.com/u/0/reporting/751e0957-c4b2-4377-ad71-52d7f2e0da62/page/IJmAE",
                "category": "Performance",
                "icon": "fa-chart-line"
            },
            {
                "name": "Inköpsprogram",
                "description": "Håll koll på lagerstatus och beställningar",
                "url": "#",
                "category": "Inköp",
                "icon": "fa-box-open"
            }
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

@app.route('/')
def index():
    query = request.args.get("sok", "").strip().lower()
    programs = load_programs_from_db()

    categories = {}
    for p in programs:
        if p.category not in categories:
            categories[p.category] = []
        categories[p.category].append(p)

    if query:
        filtered_categories = {}
        for cat, prog_list in categories.items():
            matchade = [pr for pr in prog_list if query in pr.name.lower() or query in pr.description.lower()]
            if matchade:
                filtered_categories[cat] = matchade
        categories = filtered_categories

    return render_template('index.html', categories=categories, query=query)

@app.route('/om')
def about():
    return render_template('about.html')

@app.route('/program/<string:program_name>')
def show_program(program_name: str):
    # Här justerar vi sökningen så att vi hittar program baserat på name.
    # Normalt bör vi ha unika namn. Om inte, använd ID istället.
    conn = get_db_connection()
    row = conn.execute('SELECT id, name, description, url, category, icon FROM programs').fetchall()
    conn.close()

    chosen = None
    for r in row:
        if r["name"].replace(" ", "_").lower() == program_name.lower():
            chosen = Program(id=r["id"], name=r["name"], description=r["description"], 
                             url=r["url"], category=r["category"], icon=r["icon"])
            break

    if chosen:
        return render_template('program.html', program=chosen)
    else:
        return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
