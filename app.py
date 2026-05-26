from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tshop_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# ─────────────────────────────────────────
#  Database helpers
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE
        )
    ''')

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

    # Seed categories
    # Seed categories
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

    # Seed products
    products = [
        (
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
        )
    ]

    for p in products:
        c.execute('''INSERT OR IGNORE INTO products
            (name, description, price, original_price, image_url, affiliate_link,
             category_id, rating, reviews, badge, featured, on_sale)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', p)

    conn.commit()
    conn.close()
# ─────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────

@app.route('/')
def index():
    conn = get_db()
    featured   = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.featured=1 LIMIT 8').fetchall()
    on_sale    = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.on_sale=1 LIMIT 8').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    recent     = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC LIMIT 6').fetchall()
    conn.close()
    return render_template('index.html', featured=featured, on_sale=on_sale, categories=categories, recent=recent)


@app.route('/produtos')
def produtos():
    query    = request.args.get('q', '')
    cat_slug = request.args.get('categoria', '')
    sort     = request.args.get('sort', 'relevancia')

    conn = get_db()
    categories = conn.execute('SELECT * FROM categories').fetchall()

    sql    = 'SELECT p.*, c.name as cat_name, c.slug as cat_slug FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE 1=1'
    params = []

    if query:
        sql += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        params += [f'%{query}%', f'%{query}%']
    if cat_slug:
        sql += ' AND c.slug = ?'
        params.append(cat_slug)

    order_map = {
        'menor_preco': 'p.price ASC',
        'maior_preco': 'p.price DESC',
        'avaliacao':   'p.rating DESC',
        'relevancia':  'p.featured DESC, p.reviews DESC',
    }
    sql += f' ORDER BY {order_map.get(sort, "p.featured DESC")}'

    products = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template('produtos.html',
                           products=products,
                           categories=categories,
                           query=query,
                           current_cat=cat_slug,
                           sort=sort)


@app.route('/promocoes')
def promocoes():
    conn = get_db()
    on_sale    = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.on_sale=1 ORDER BY (p.original_price - p.price) DESC').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    conn.close()
    return render_template('promocoes.html', products=on_sale, categories=categories)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        action = request.form.get('action')
        conn = get_db()

        if action == 'add':
            conn.execute('''INSERT INTO products
                (name, description, price, original_price, image_url, affiliate_link,
                 category_id, rating, reviews, badge, featured, on_sale)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', (
                request.form['name'],
                request.form['description'],
                float(request.form['price']),
                float(request.form.get('original_price') or request.form['price']),
                request.form.get('image_url', 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400'),
                request.form['affiliate_link'],
                int(request.form['category_id']),
                float(request.form.get('rating', 4.5)),
                int(request.form.get('reviews', 0)),
                request.form.get('badge') or None,
                1 if request.form.get('featured') else 0,
                1 if request.form.get('on_sale') else 0,
            ))
            conn.commit()

        elif action == 'delete':
            conn.execute('DELETE FROM products WHERE id=?', (request.form['product_id'],))
            conn.commit()

        conn.close()
        return redirect(url_for('admin'))

    conn = get_db()
    products   = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.id DESC').fetchall()
    categories = conn.execute('SELECT * FROM categories').fetchall()
    total_products = conn.execute('SELECT COUNT(*) as n FROM products').fetchone()['n']
    on_sale_count  = conn.execute('SELECT COUNT(*) as n FROM products WHERE on_sale=1').fetchone()['n']
    featured_count = conn.execute('SELECT COUNT(*) as n FROM products WHERE featured=1').fetchone()['n']
    conn.close()
    return render_template('admin.html', products=products, categories=categories,
                           total_products=total_products, on_sale_count=on_sale_count,
                           featured_count=featured_count)


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


@app.route('/produto/<int:product_id>')
def produto_detalhe(product_id):
    conn = get_db()
    product    = conn.execute('SELECT p.*, c.name as cat_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE p.id=?', (product_id,)).fetchone()
    related    = conn.execute('SELECT * FROM products WHERE category_id=? AND id!=? LIMIT 4', (product['category_id'], product_id)).fetchall()
    conn.close()
    if not product:
        return redirect(url_for('index'))
    return render_template('produto_detalhe.html', product=product, related=related)


if __name__ == '__main__':
    init_db()
    print('\n🛒 TShop iniciado! Acesse: http://127.0.0.1:5000\n')
    app.run(debug=True, host='0.0.0.0', port=5000)
