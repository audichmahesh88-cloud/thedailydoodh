from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB_NAME = "database.db"

def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""CREATE TABLE sellers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT UNIQUE,
                        password TEXT
                    )""")
        c.execute("""CREATE TABLE products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        seller_id INTEGER,
                        product_name TEXT,
                        price REAL,
                        contact TEXT,
                        FOREIGN KEY(seller_id) REFERENCES sellers(id)
                    )""")
        c.execute("""CREATE TABLE orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        customer_name TEXT,
                        customer_address TEXT,
                        customer_phone TEXT,
                        FOREIGN KEY(product_id) REFERENCES products(id)
                    )""")
        conn.commit()
        conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT products.id, products.product_name, products.price, products.contact, sellers.name FROM products JOIN sellers ON products.seller_id = sellers.id")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
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
            return redirect(url_for('login'))
        except:
            conn.close()
            return "Email already registered!"
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'seller_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        price = request.form['price']
        contact = request.form['contact']
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO products (seller_id, product_name, price, contact) VALUES (?, ?, ?, ?)",
                  (session['seller_id'], product_name, price, contact))
        conn.commit()
        conn.close()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT product_name, price, contact FROM products WHERE seller_id=?", (session['seller_id'],))
    products = c.fetchall()
    conn.close()
    return render_template("dashboard.html", seller=session['seller_name'], products=products)

@app.route('/order/<int:product_id>', methods=['GET', 'POST'])
def order(product_id):
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO orders (product_id, customer_name, customer_address, customer_phone) VALUES (?, ?, ?, ?)",
                  (product_id, name, address, phone))
        conn.commit()
        conn.close()
        return "Order placed successfully! ✅"
    
    return render_template("order.html", product_id=product_id)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/vision')
def vision():
    return render_template("vision.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
