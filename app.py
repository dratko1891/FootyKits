from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, jsonify
import os
import pg8000
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv  # type: ignore

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_db_connection():
    connection = pg8000.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT
    )
    return connection

@app.route('/favorites')
def favorites():
    return render_template('favorites.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/cart')
def cart():
    if 'username' not in session:
        flash("Du måste vara inloggad för att visa din varukorg.", "warning")
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    base_url = "https://hcqxsfiqisutksicxfjr.supabase.co/storage/v1/object/public/images/"
    return render_template('cart.html', cartItems=cart_items, base_url=base_url)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        flash("Du måste vara inloggad för att lägga till produkter i varukorgen.", "warning")
        return redirect(url_for('login'))

    product_id = request.form.get("product_id")
    size = request.form.get("size")

    if not product_id or not size:
        flash("Ogiltigt produkt-ID eller storlek.", "danger")
        return redirect(url_for('products'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, price, img FROM kits WHERE id = %s", (product_id,))
    item = cursor.fetchone()
    conn.close()

    if not item:
        flash("Produkten hittades inte.", "danger")
        return redirect(url_for('products'))

    cart_item = {
        'product_id': item[0],
        'title': item[1],
        'price': item[2],
        'img': item[3],
        'size': size
    }

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']
    cart.append(cart_item)
    session['cart'] = cart 

    flash("Produkten har lagts till i varukorgen!", "success")
    return redirect(url_for('cart'))



@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get("product_id")
    size = request.form.get("size")

    if 'cart' in session and product_id and size:
        cart = session['cart']
        session['cart'] = [item for item in cart if not (str(item['product_id']) == product_id and item['size'] == size)]
        flash("Produkten har tagits bort från din varukorg.", "success")
    else:
        flash("Något gick fel vid borttagningen.", "danger")

    return redirect(url_for('cart'))


@app.route('/')
def products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM kits")
    products = [{'id': row[0], 'title': row[1], 'price': row[2], 'img': row[3]} for row in cursor.fetchall()]
    conn.close()
    base_url = "https://hcqxsfiqisutksicxfjr.supabase.co/storage/v1/object/public/images/"
    return render_template('index.html', products=products, base_url=base_url)

@app.route('/product/<int:product_id>')
def product_page(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, price, img, info FROM kits WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        product = {'id': product[0], 'title': product[1], 'price': product[2], 'img': product[3], 'info': product[4]}
        base_url = "https://hcqxsfiqisutksicxfjr.supabase.co/storage/v1/object/public/images/"
        return render_template('product.html', product=product, base_url=base_url)
    else:
        flash("Produkten hittades inte.", "danger")
        return redirect(url_for('products'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
        except pg8000.IntegrityError:
            conn.rollback()
            flash('Användarnamnet är redan registrerat.', 'warning')
            return redirect(url_for('register'))

        conn.close()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password): 
            session['username'] = user[1]  
            flash('Inloggningen lyckades!', 'success')
            return redirect(url_for('success'))
        else:
            flash('Felaktigt användarnamn eller lösenord.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('cart', None) 
    flash("Du har loggats ut.", "success")
    return redirect(url_for('login'))


@app.route('/success')
def success():
    if 'username' not in session:
        flash('Du måste vara inloggad för att komma åt denna sida!', 'warning')
        return redirect(url_for('login'))

    return render_template('success.html', username=session["username"])

if __name__ == '__main__':
    app.run(debug=True)
