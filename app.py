from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import os
from datetime import datetime

# ─────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────
app = Flask(__name__)
app.secret_key = "tshop_secret_key_2024"

ADMIN_USER = "admin"
ADMIN_PASS = "132457"

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    # CATEGORIES
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE
        )
    ''')

    # PRODUCTS
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            original_price REAL,
            image_url TEXT,
            affiliate_link TEXT NOT NULL,
            category_id INTEGER,
            rating REAL DEFAULT 4.5,
            reviews INTEGER DEFAULT 0,
            badge TEXT,
            featured INTEGER DEFAULT 0,
            on_sale INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # CATEGORIAS PADRÃO
    cats = [
        ('Eletrônicos', '💻', 'eletronicos'),
        ('Moda', '👗', 'moda'),
        ('Casa & Deco', '🏠', 'casa'),
        ('Esportes', '⚡', 'esportes'),
        ('Beleza', '✨', 'beleza'),
        ('Games', '🎮', 'games'),
        ('Livros', '📚', 'livros'),
        ('Automotivo', '🚗', 'automotivo'),
    ]

    for name, icon, slug in cats:
        c.execute(
            'INSERT OR IGNORE INTO categories (name, icon, slug) VALUES (?,?,?)',
            (name, icon, slug)
        )

    # PRODUTO EXEMPLO
    c.execute('''
        INSERT OR IGNORE INTO products
        (name, description, price, original_price, image_url, affiliate_link,
         category_id, rating, reviews, badge, featured, on_sale)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        "12 Envelopes Panini Copa 2026",
        "Coleção oficial Panini Copa do Mundo 2026",
        39.90,
        49.90,
        "https://http2.mlstatic.com/D_NQ_NP_2X_903022-MLA109894312615_032026-F.webp",
        "SEU_LINK_AFILIADO",
        1,
        4.8,
        120,
        "PROMOÇÃO",
        1,
        1
    ))

    conn.commit()
    conn.close()
 
# ─────────────────────────────
# LOGIN ADMIN
# ─────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        if user == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return "Login inválido"

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


# ─────────────────────────────
# ROTAS
# ─────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    featured = conn.execute('SELECT * FROM products WHERE featured=1').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()

    return render_template('index.html',
                           featured=featured,
                           categories=categories)


@app.route('/produtos')
def produtos():
    conn = get_db()
    products = conn.execute('SELECT * FROM products').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()

    return render_template('produtos.html',
                           products=products,
                           categories=categories)


@app.route('/promocoes')
def promocoes():
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE on_sale=1').fetchall()
    conn.close()

    return render_template('promocoes.html', products=products)


# ─────────────────────────────
# ADMIN PROTEGIDO
# ─────────────────────────────
@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():

    conn = get_db()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            conn.execute('''
                INSERT INTO products
                (name, description, price, original_price, image_url, affiliate_link,
                 category_id, rating, reviews, badge, featured, on_sale)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                request.form['name'],
                request.form['description'],
                float(request.form['price']),
                float(request.form.get('original_price') or request.form['price']),
                request.form.get('image_url'),
                request.form['affiliate_link'],
                int(request.form['category_id']),
                float(request.form.get('rating', 4.5)),
                int(request.form.get('reviews', 0)),
                request.form.get('badge'),
                1 if request.form.get('featured') else 0,
                1 if request.form.get('on_sale') else 0
            ))
            conn.commit()

        elif action == 'delete':
            conn.execute('DELETE FROM products WHERE id=?',
                         (request.form['product_id'],))
            conn.commit()

        conn.close()
        return redirect(url_for('admin'))

    # GET
    products = conn.execute('SELECT * FROM products').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()

    conn.close()

    return render_template(
        'admin.html',
        products=products,
        categories=categories
    )

# ─────────────────────────────
# API SEARCH
# ─────────────────────────────
@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')

    conn = get_db()
    results = conn.execute(
        'SELECT id, name, price, image_url FROM products WHERE name LIKE ? LIMIT 6',
        (f'%{q}%',)
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in results])


# ─────────────────────────────
# PRODUTO DETALHE
# ─────────────────────────────
@app.route('/produto/<int:product_id>')
def produto_detalhe(product_id):
    conn = get_db()

    product = conn.execute(
        'SELECT * FROM products WHERE id=?',
        (product_id,)
    ).fetchone()

    if not product:
        return redirect(url_for('index'))

    related = conn.execute(
        'SELECT * FROM products WHERE category_id=? AND id!=? LIMIT 4',
        (product['category_id'], product_id)
    ).fetchall()

    conn.close()

    return render_template('produto_detalhe.html',
                           product=product,
                           related=related)


# ─────────────────────────────
# START
# ─────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)