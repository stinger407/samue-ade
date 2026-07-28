

from flask import Flask, g, render_template, request, redirect, url_for, session, flash, send_from_directory
import sqlite3
import os
import datetime
import secrets
import random
import string
from models import db, User, save_token_for_user
from email_utils import send_confirmation_email

app = Flask(__name__)
app.secret_key = "ofame-legacy-secret-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db.init_app(app)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'adminpass')


# The duplicate login_confirm route has been removed. Unified route is defined below.

@app.route('/clear-session')
def clear_session():
    session.clear()
    return redirect(url_for("index"))

MENU_ITEMS = [
    (1, "Beef - Ribeye (per kg)", 18.50, "Premium ribeye beef, trimmed and ready to cook.", "Meat"),
    (2, "Beef - Ground (per kg)", 9.50, "Lean ground beef, versatile for many recipes.", "Meat"),
    (3, "Goat Meat (per kg)", 11.00, "Fresh goat meat cuts, great for stews and roasting.", "Meat"),
    (4, "Rice - 25kg Bag", 25.00, "Staple long-grain rice, 25kg bag, pantry essential.", "Pantry"),
    (5, "Assorted Foodstuffs Box", 45.00, "Mixed pantry staples: rice, beans, oil, and spices.", "Pantry"),
]

ITEM_IMAGE_URLS = {
    1: "images/th.webp",
    2: "images/rice_bag.jpg",
    3: "images/OIP.webp",
    4: "images/raw_meat2.jpg",
    5: "images/food_box.jpg",
}

DEFAULT_IMAGE_URL = "images/th.webp"
DEFAULT_IMAGE_URL = "images/th.webp"


def normalize_image_url(url):
    if not url:
        return "/images/company_cows.jpg"
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "/" + url.lstrip("./")


@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'images'), filename)

DATABASE = "food.db"
def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


def init_db():
    create_database = not os.path.exists(DATABASE)
    db = None

    def create_schema(conn, cursor):
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY, name TEXT, price REAL, description TEXT, category TEXT, image_url TEXT)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, items TEXT, total REAL, customer_name TEXT, customer_email TEXT, payment_method TEXT, created_at TEXT, tracking_id TEXT, delivery_address TEXT, status TEXT DEFAULT 'Confirmed', status_updated_at TEXT)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, token TEXT, verified INTEGER DEFAULT 0, phone TEXT, address TEXT)"
        )
        cursor.execute("SELECT COUNT(*) FROM menu")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO menu (id, name, price, description, category) VALUES (?, ?, ?, ?, ?)", MENU_ITEMS
            )
        conn.commit()

    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        cursor.execute("PRAGMA quick_check")
        if cursor.fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("Database integrity check failed")

        if create_database:
            create_schema(db, cursor)
        else:
            cursor.execute("PRAGMA table_info(orders)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            if "customer_name" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT")
            if "customer_email" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_email TEXT")
            if "payment_method" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
            if "created_at" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN created_at TEXT")
            if "tracking_id" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN tracking_id TEXT")
            if "delivery_address" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN delivery_address TEXT")
            if "status" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'Confirmed'")
            if "status_updated_at" not in existing_columns:
                cursor.execute("ALTER TABLE orders ADD COLUMN status_updated_at TEXT")
            cursor.execute("PRAGMA table_info(menu)")
            menu_columns = [row[1] for row in cursor.fetchall()]
            if "category" not in menu_columns:
                cursor.execute("ALTER TABLE menu ADD COLUMN category TEXT")
            if "image_url" not in menu_columns:
                cursor.execute("ALTER TABLE menu ADD COLUMN image_url TEXT")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, token TEXT, verified INTEGER DEFAULT 0, phone TEXT, address TEXT)")
            else:
                cursor.execute("PRAGMA table_info(users)")
                users_columns = [row[1] for row in cursor.fetchall()]
                if "token" not in users_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN token TEXT")
                if "verified" not in users_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
                if "phone" not in users_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
                if "address" not in users_columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
            db.commit()
    except (sqlite3.DatabaseError, sqlite3.OperationalError):
        if db is not None:
            db.close()
        if os.path.exists(DATABASE):
            os.remove(DATABASE)
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        create_schema(db, cursor)
    finally:
        if db is not None:
            db.close()


@app.before_request
def setup():
    # Safeguard: if user is marked logged_in but no user exists in session, clear it.
    # This prevents redirect loops and fixes the missing homepage popup for legacy sessions.
    if session.get('logged_in') and not session.get('user'):
        session.pop('logged_in', None)




def row_to_item(row):
    item = {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "description": row["description"],
        "category": row["category"] or "Uncategorized",
    }
    if "image_url" in row.keys():
        image_url = row["image_url"] or ITEM_IMAGE_URLS.get(row["id"], DEFAULT_IMAGE_URL)
    else:
        image_url = ITEM_IMAGE_URLS.get(row["id"], DEFAULT_IMAGE_URL)
    item["image_url"] = normalize_image_url(image_url)
    return item


def build_cart_items(cart):
    if not cart:
        return [], 0.0

    db = get_db()
    item_ids = list(cart.keys())
    placeholders = ",".join("?" for _ in item_ids)
    rows = db.execute(f"SELECT * FROM menu WHERE id IN ({placeholders})", item_ids).fetchall()

    cart_items = []
    total = 0.0
    for row in rows:
        quantity = cart.get(str(row["id"]), 0)
        subtotal = row["price"] * quantity
        total += subtotal
        image_url = row["image_url"] or ITEM_IMAGE_URLS.get(row["id"], DEFAULT_IMAGE_URL)
        cart_items.append({
            "id": row["id"],
            "name": row["name"],
            "price": row["price"],
            "quantity": quantity,
            "subtotal": subtotal,
            "image_url": normalize_image_url(image_url),
        })

    return cart_items, total


@app.route("/")
def index():
    selected_category = request.args.get("category", "").strip()
    db = get_db()
    categories = [row["category"] for row in db.execute("SELECT DISTINCT category FROM menu ORDER BY category").fetchall() if row["category"]]
    if selected_category:
        rows = db.execute("SELECT * FROM menu WHERE category = ? ORDER BY id", (selected_category,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM menu ORDER BY id").fetchall()
    items = [row_to_item(row) for row in rows]
    cart = session.get("cart", {})
    cart_count = sum(cart.values())
    return render_template("index.html", items=items, categories=categories, selected_category=selected_category, cart_count=cart_count)





@app.route('/item/<int:item_id>')
def item_detail(item_id):
    db = get_db()
    row = db.execute('SELECT * FROM menu WHERE id = ?', (item_id,)).fetchone()
    if not row:
        flash('Item not found.')
        return redirect(url_for('index'))
    item = row_to_item(row)
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    return render_template('item.html', item=item, cart_count=cart_count)


@app.route("/add", methods=["POST"])
def add_to_cart():
    item_id = request.form.get("item_id")
    if not item_id:
        flash("No item selected.")
        return redirect(url_for("index"))
    cart = session.get("cart", {})
    cart[item_id] = cart.get(item_id, 0) + 1
    session["cart"] = cart
    flash("Item added to cart.")
    return redirect(url_for("index"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        db = get_db()
        user_email = session.get('user', {}).get('email')
        existing_user = db.execute("SELECT * FROM users WHERE email = ?", (user_email,)).fetchone() if user_email else None
        if existing_user:
            return redirect(url_for('account'))
        else:
            session.pop('user', None)
            session.pop('logged_in', None)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        name_field = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        # Handle name formatting from different forms
        if first_name or last_name:
            name = f"{first_name} {last_name}".strip()
        else:
            name = name_field

        if not email:
            flash('Email is required.')
            return redirect(url_for('login'))
        if not name:
            name = email.split('@')[0]

        db = get_db()
        # Find or create user in SQLite database
        try:
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if not user:
                db.execute("INSERT INTO users (name, email, phone, address) VALUES (?, ?, ?, ?)", (name, email, phone or None, address or None))
                db.commit()
                user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            else:
                user_keys = user.keys() if hasattr(user, 'keys') else []
                if phone and ('phone' in user_keys) and not user['phone']:
                    db.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user['id']))
                if address and ('address' in user_keys) and not user['address']:
                    db.execute("UPDATE users SET address = ? WHERE id = ?", (address, user['id']))
                db.commit()
                user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

            token = secrets.token_urlsafe(32)
            db.execute("UPDATE users SET token = ? WHERE id = ?", (token, user['id']))
            db.commit()
        except Exception as e:
            app.logger.error(f"Database error during login: {e}")
            flash('Database error. Please try again.')
            return redirect(url_for('login'))

        # Build dynamic verification link
        verification_link = request.url_root.rstrip('/') + url_for('verify', token=token)

        # Send verification/confirmation code via email safely
        try:
            send_confirmation_email(email, verification_link, token)
        except Exception as e:
            app.logger.error(f"Email sending error: {e}")

        user_keys = user.keys() if hasattr(user, 'keys') else []
        session['logged_in'] = True
        session['user'] = {
            'name': user['name'],
            'email': user['email'],
            'phone': user['phone'] if 'phone' in user_keys else None,
            'address': user['address'] if 'address' in user_keys else None
        }

        flash('Your account has been created and you are now signed in.')
        return redirect(url_for('account'))

    return render_template('login.html')


@app.route('/verify')
def verify():
    token = request.args.get('token', '').strip()
    if not token:
        flash("Invalid or missing verification token.")
        return redirect(url_for('index'))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
    if user:
        db.execute("UPDATE users SET verified = 1 WHERE id = ?", (user['id'],))
        db.commit()

        # Log the user in if they aren't already
        session['logged_in'] = True
        session['user'] = {
            'name': user['name'], 'email': user['email'],
            'phone': user['phone'], 'address': user['address']
        }

        flash("Your email has been verified successfully!")
        return redirect(url_for('account'))
    else:
        flash("Verification token is invalid or has expired.")
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Admin signed in.')
            return redirect(url_for('admin_menu'))
        flash('Wrong admin password.')
        return redirect(url_for('admin_login'))
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Admin signed out.')
    return redirect(url_for('index'))


def admin_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.')
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)

    return wrapper


@app.route('/admin/menu')
@admin_required
def admin_menu():
    db = get_db()
    items = db.execute('SELECT * FROM menu ORDER BY id').fetchall()
    return render_template('admin_menu.html', items=items)


@app.route('/admin/menu/add', methods=['GET', 'POST'])
@admin_required
def admin_add_item():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price', '0') or 0)
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip() or 'Uncategorized'
        image_url = request.form.get('image_url', '').strip() or None
        db = get_db()
        db.execute(
            'INSERT INTO menu (name, price, description, category, image_url) VALUES (?, ?, ?, ?, ?)',
            (name, price, description, category, image_url),
        )
        db.commit()
        flash('Item added.')
        return redirect(url_for('admin_menu'))
    return render_template('admin_edit_item.html', item=None)


@app.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_item(item_id):
    db = get_db()
    item = db.execute('SELECT * FROM menu WHERE id = ?', (item_id,)).fetchone()
    if not item:
        flash('Item not found.')
        return redirect(url_for('admin_menu'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = float(request.form.get('price', '0') or 0)
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip() or 'Uncategorized'
        image_url = request.form.get('image_url', '').strip() or None
        db.execute(
            'UPDATE menu SET name = ?, price = ?, description = ?, category = ?, image_url = ? WHERE id = ?',
            (name, price, description, category, image_url, item_id),
        )
        db.commit()
        flash('Item updated.')
        return redirect(url_for('admin_menu'))
    return render_template('admin_edit_item.html', item=item)


@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
@admin_required
def admin_delete_item(item_id):
    db = get_db()
    db.execute('DELETE FROM menu WHERE id = ?', (item_id,))
    db.commit()
    flash('Item deleted.')
    return redirect(url_for('admin_menu'))


@app.route('/admin/users')
@admin_required
def admin_users():
    q = request.args.get('q', '').strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        users = db.execute(
            'SELECT * FROM users WHERE name LIKE ? OR email LIKE ? ORDER BY id',
            (like, like),
        ).fetchall()
    else:
        users = db.execute('SELECT * FROM users ORDER BY id').fetchall()
    return render_template('admin_users.html', users=users, q=q)


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found.')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        if not name or not email:
            flash('Please enter both name and email.')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        db.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, user_id))
        db.commit()
        flash('User updated.')
        return redirect(url_for('admin_users'))

    return render_template('admin_edit_user.html', user=user)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    flash('User deleted.')
    return redirect(url_for('admin_users'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'date_desc').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    db = get_db()
    clauses = []
    args = []
    if q:
        like = f"%{q}%"
        clauses.append("(customer_name LIKE ? OR customer_email LIKE ? OR items LIKE ?)")
        args.extend([like, like, like])
    if date_from:
        clauses.append("substr(created_at,1,10) >= ?")
        args.append(date_from)
    if date_to:
        clauses.append("substr(created_at,1,10) <= ?")
        args.append(date_to)
    order_by = "ORDER BY substr(created_at,1,19) DESC"
    if sort == 'date_asc':
        order_by = "ORDER BY substr(created_at,1,19) ASC"
    elif sort == 'total_asc':
        order_by = "ORDER BY total ASC"
    elif sort == 'total_desc':
        order_by = "ORDER BY total DESC"
    sql = "SELECT * FROM orders"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " " + order_by
    orders = db.execute(sql, args).fetchall()
    return render_template('admin_orders.html', orders=orders, q=q, sort=sort, date_from=date_from, date_to=date_to)


@app.route('/admin/orders/delete/<int:order_id>', methods=['POST'])
@admin_required
def admin_delete_order(order_id):
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()
    flash('Order deleted.')
    return redirect(url_for('admin_orders'))


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    cart_items, total = build_cart_items(cart)
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/update-cart", methods=["POST"])
def update_cart():
    item_id = request.form.get("item_id")
    quantity = request.form.get("quantity")
    action = request.form.get("action")
    cart = session.get("cart", {})

    if not item_id:
        flash("No item selected.")
        return redirect(url_for("cart"))

    if action == "remove" or not quantity or int(quantity) <= 0:
        cart.pop(item_id, None)
        flash("Item removed from the cart.")
    else:
        cart[item_id] = int(quantity)
        flash("Cart updated.")

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/checkout")
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for("index"))

    cart_items, total = build_cart_items(cart)
    # Load full user from DB to get saved address
    saved_address = ''
    session_user = session.get('user')
    if session_user:
        db = get_db()
        db_user = db.execute("SELECT address FROM users WHERE email = ?", (session_user['email'],)).fetchone()
        if db_user and db_user['address']:
            saved_address = db_user['address']
    return render_template("checkout.html", cart_items=cart_items, total=total, saved_address=saved_address)


@app.route("/place-order", methods=["POST"])
def place_order():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for("index"))

    session_user = session.get("user")
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    payment_method = request.form.get("payment_method", "Card")
    delivery_address = request.form.get("delivery_address", "").strip()

    if session_user:
        name = session_user.get("name", name)
        email = session_user.get("email", email)

    if not name or not email:
        flash("Please enter your name and email to complete the order.")
        return redirect(url_for("checkout"))

    cart_items, total = build_cart_items(cart)
    order_lines = [f"{item['quantity']}× {item['name']}" for item in cart_items]
    created_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    # Generate unique tracking ID e.g. OFM-A4B2C1
    tracking_id = "OFM-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    db = get_db()
    db.execute(
        "INSERT INTO orders (items, total, customer_name, customer_email, payment_method, created_at, tracking_id, delivery_address, status, status_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (", ".join(order_lines), total, name, email, payment_method, created_at, tracking_id, delivery_address or None, 'Confirmed', created_at),
    )
    db.commit()

    session["cart"] = {}
    flash(f"Order placed successfully! Your tracking ID is {tracking_id}. Thank you.")
    return redirect(url_for("order_history"))


@app.route('/account')
def account():
    if not session.get('user'):
        flash('Please sign in to view your account.')
        return redirect(url_for('login'))
    session_user = session['user']
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    db = get_db()
    # Load full user from DB to get phone, address, verified status
    user = db.execute("SELECT * FROM users WHERE email = ?", (session_user['email'],)).fetchone()
    if not user:
        session.pop('user', None)
        session.pop('logged_in', None)
        flash('User record not found. Please sign in again.')
        return redirect(url_for('login'))
    orders = db.execute(
        'SELECT * FROM orders WHERE customer_email = ? ORDER BY substr(created_at,1,19) DESC',
        (user['email'],)
    ).fetchall()
    return render_template('account.html', user=user, orders=orders, cart_count=cart_count)


@app.route('/account/update', methods=['POST'])
def account_update():
    if not session.get('user'):
        return redirect(url_for('login'))
    email = session['user']['email']
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    db = get_db()
    db.execute("UPDATE users SET phone = ?, address = ? WHERE email = ?", (phone or None, address or None, email))
    db.commit()
    # Refresh session with new data
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    session['user'] = {
        'name': user['name'], 'email': user['email'],
        'phone': user['phone'], 'address': user['address']
    }
    flash('Your details have been updated successfully.')
    return redirect(url_for('account'))


@app.route("/order-history")
def order_history():
    if session.get("is_admin"):
        return redirect(url_for('admin_orders'))
    if not session.get("user"):
        flash("Please sign in to view your order history.")
        return redirect(url_for("login"))

    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'date_desc').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    user_email = session["user"].get("email")
    db = get_db()
    clauses = ["customer_email = ?"]
    args = [user_email]
    if q:
        like = f"%{q}%"
        clauses.append("(customer_name LIKE ? OR items LIKE ?)")
        args.extend([like, like])
    if date_from:
        clauses.append("substr(created_at,1,10) >= ?")
        args.append(date_from)
    if date_to:
        clauses.append("substr(created_at,1,10) <= ?")
        args.append(date_to)
    order_by = "ORDER BY substr(created_at,1,19) DESC"
    if sort == 'date_asc':
        order_by = "ORDER BY substr(created_at,1,19) ASC"
    elif sort == 'total_asc':
        order_by = "ORDER BY total ASC"
    elif sort == 'total_desc':
        order_by = "ORDER BY total DESC"
    sql = "SELECT * FROM orders WHERE " + " AND ".join(clauses) + " " + order_by
    orders = db.execute(sql, args).fetchall()
    return render_template("order_history.html", orders=orders, q=q, sort=sort, date_from=date_from, date_to=date_to)


@app.route('/track/<tracking_id>')
def track_order(tracking_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE tracking_id = ?", (tracking_id.upper(),)).fetchone()
    if not order:
        flash("No order found with that tracking ID.")
        return redirect(url_for('index'))
    statuses = ['Confirmed', 'Processing', 'Dispatched', 'Out for Delivery', 'Delivered']
    current_index = statuses.index(order['status']) if order['status'] in statuses else 0
    return render_template('track.html', order=order, statuses=statuses, current_index=current_index)


@app.route('/admin/orders/update-status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    new_status = request.form.get('status', '').strip()
    valid_statuses = ['Confirmed', 'Processing', 'Dispatched', 'Out for Delivery', 'Delivered']
    if new_status not in valid_statuses:
        flash('Invalid status.')
        return redirect(url_for('admin_orders'))
    updated_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    db.execute(
        "UPDATE orders SET status = ?, status_updated_at = ? WHERE id = ?",
        (new_status, updated_at, order_id)
    )
    db.commit()
    flash(f'Order #{order_id} status updated to "{new_status}".')
    return redirect(url_for('admin_orders'))


# Initialize database once at startup
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)


