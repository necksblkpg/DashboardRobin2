import os
from flask import Flask, render_template, request, redirect, url_for
from dataclasses import dataclass
from typing import List
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "hemlig_nyckel_2024_modern"

@dataclass
class Program:
    name: str
    description: str
    url: str
    category: str
    icon: str

def load_programs_from_json(filepath: str) -> List[Program]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Program(**item) for item in data]

PROGRAMS_FILE = os.path.join(os.path.dirname(__file__), 'programs.json')
programs: List[Program] = load_programs_from_json(PROGRAMS_FILE)

@app.route('/')
def index():
    query = request.args.get("sok", "").strip().lower()
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
    chosen = None
    for p in programs:
        if p.name.replace(" ", "_").lower() == program_name.lower():
            chosen = p
            break
    if chosen:
        return render_template('program.html', program=chosen)
    else:
        return redirect(url_for('index'))
