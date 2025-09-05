from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "database.db"

# Ensure uploads folder exists
if not os.path.exists("static/uploads"):
    os.makedirs("static/uploads")

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Seller table
        c.execute("""CREATE TABLE sellers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT UNIQUE,
                        password TEXT
                    )""")

        # Customer table
        c.execute("""CREATE TABLE customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT UNIQUE,
                        password TEXT
                    )""")

        # Products table (with image)
        c.execute("""CREATE TABLE products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        seller_id INTEGER,
                        product_name TEXT,
                        price REAL,
                        contact TEXT,
                        image TEXT,
                        FOREIGN KEY(seller_id) REFERENCES sellers(id)
                    )""")

        # Orders table
        c.execute("""CREATE TABLE orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        customer_id INTEGER,
                        product_id INTEGER,
                        quantity INTEGER,
                        status TEXT DEFAULT 'Pending',
                        FOREIGN KEY(customer_id) REFERENCES customers(id),
                        FOREIGN KEY(product_id) REFERENCES products(id)
                    )""")

        conn.commit()
        conn.close()

# ---------------- Home ----------------
@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT products.id, products.product_name, products.price, 
                        products.contact, products.image, sellers.id, sellers.name
                 FROM products 
                 JOIN sellers ON products.seller_id = sellers.id""")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)

# ---------------- Seller Auth ----------------
@app.route('/seller/register', methods=['GET', 'POST'])
def seller_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO sellers (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('seller_login'))
        except:
            conn.close()
            return "Email already registered!"
    return render_template("register.html", role="Seller")

@app.route('/seller/login', methods=['GET', 'POST'])
def seller_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM sellers WHERE email=? AND password=?", (email, password))
        seller = c.fetchone()
        conn.close()
        if seller:
            session['seller_id'] = seller[0]
            session['seller_name'] = seller[1]
            session['role'] = "seller"
            return redirect(url_for('seller_dashboard'))
        else:
            return "Invalid credentials!"
    return render_template("login.html", role="Seller")

@app.route('/seller/dashboard', methods=['GET', 'POST'])
def seller_dashboard():
    if 'seller_id' not in session:
        return redirect(url_for('seller_login'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        price = request.form['price']
        contact = request.form['contact']

        # Save image
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != "":
                image = os.path.join("static/uploads", file.filename)
                file.save(image)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO products (seller_id, product_name, price, contact, image) VALUES (?, ?, ?, ?, ?)",
                  (session['seller_id'], product_name, price, contact, image))
        conn.commit()
        conn.close()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT product_name, price, contact, image FROM products WHERE seller_id=?", (session['seller_id'],))
    products = c.fetchall()
    conn.close()
    return render_template("dashboard.html", seller=session['seller_name'], products=products, role="Seller")

# ---------------- Customer Auth ----------------
@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO customers (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for('customer_login'))
        except:
            conn.close()
            return "Email already registered!"
    return render_template("register.html", role="Customer")

@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE email=? AND password=?", (email, password))
        customer = c.fetchone()
        conn.close()
        if customer:
            session['customer_id'] = customer[0]
            session['customer_name'] = customer[1]
            session['role'] = "customer"
            return redirect(url_for('customer_dashboard'))
        else:
            return "Invalid credentials!"
    return render_template("login.html", role="Customer")

@app.route('/customer/dashboard')
def customer_dashboard():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT products.id, products.product_name, products.price, 
                        products.contact, products.image, sellers.name
                 FROM products 
                 JOIN sellers ON products.seller_id = sellers.id""")
    products = c.fetchall()

    # Get customer orders
    c.execute("""SELECT orders.id, products.product_name, orders.quantity, orders.status 
                 FROM orders 
                 JOIN products ON orders.product_id = products.id
                 WHERE orders.customer_id=?""", (session['customer_id'],))
    orders = c.fetchall()

    conn.close()
    return render_template("customer_dashboard.html", customer=session['customer_name'], products=products, orders=orders, role="Customer")

# ---------------- Seller Profile ----------------
@app.route('/seller/<int:seller_id>')
def seller_profile(seller_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, email FROM sellers WHERE id=?", (seller_id,))
    seller = c.fetchone()
    c.execute("SELECT id, product_name, price, contact, image FROM products WHERE seller_id=?", (seller_id,))
    products = c.fetchall()
    conn.close()
    return render_template("seller_profile.html", seller=seller, products=products)

# ---------------- Orders ----------------
@app.route('/order/<int:product_id>', methods=['POST'])
def place_order(product_id):
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))

    quantity = int(request.form['quantity'])

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO orders (customer_id, product_id, quantity) VALUES (?, ?, ?)",
              (session['customer_id'], product_id, quantity))
    conn.commit()
    conn.close()

    return redirect(url_for('customer_dashboard'))

# ---------------- Static Pages ----------------
@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/vision')
def vision():
    return render_template("vision.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
