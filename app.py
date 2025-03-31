from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import os
import pg8000
import supabase
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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
    return render_template('cart.html')

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
    cursor.execute("SELECT * FROM kits WHERE id = %s", (product_id,))
    product = cursor.fetchone()  
    conn.close()

    if not product:
        flash("Produkten hittades inte!", "danger")
        return redirect(url_for('products'))

    product = {'id': product[0], 'title': product[1], 'price': product[2], 'img': product[3]}

    return render_template('product.html', product=product)






    

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

@app.route('/logout/')
def logout():
    session.pop('username', None)
    flash('Utloggad!', 'success')
    return render_template('index.html')

@app.route('/success/')
def success():
    if 'username' in session:
        response = make_response(render_template('success.html', username=session["username"]))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    flash('Du måste logga in först!', 'warning')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
