import os
from flask import Flask, render_template
from dataclasses import dataclass
from typing import List

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

@dataclass
class Program:
    name: str
    description: str
    url: str
    category: str
    icon: str

# Program data
programs: List[Program] = [
    Program(
        name="Shopping Program",
        description="Manage your shopping lists and track expenses",
        url="#",  # Replace with actual URL
        category="Utilities",
        icon="fa-cart-shopping"
    ),
    Program(
        name="Customer Reviews",
        description="Collect and analyze customer feedback",
        url="#",  # Replace with actual URL
        category="Business",
        icon="fa-star"
    ),
    Program(
        name="Translation Tool 1",
        description="Text translation with language detection",
        url="#",  # Replace with actual URL
        category="Language",
        icon="fa-language"
    ),
    Program(
        name="Translation Tool 2",
        description="Document translation and formatting",
        url="#",  # Replace with actual URL
        category="Language",
        icon="fa-file-language"
    ),
    Program(
        name="Looker Studio Report",
        description="Business analytics and reporting dashboard",
        url="#",  # Replace with actual URL
        category="Business",
        icon="fa-chart-line"
    )
]

@app.route('/')
def index():
    # Group programs by category
    categories = {}
    for program in programs:
        if program.category not in categories:
            categories[program.category] = []
        categories[program.category].append(program)
    
    return render_template('index.html', categories=categories)
