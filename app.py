import mysql.connector
from flask import Flask,jsonify,request,render_template,url_for,redirect,flash
from flask import session
import datetime

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'

users = {
    'admin': 'admin123',
    'user1': 'pass1'
}

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('product'))
        else:
            error = "Invalid username or password"
    return render_template('home.html', error=error)

def db_conn():
    conn =mysql.connector.connect(
    host="localhost",
    user="root",
    password="dharani@2004",
    database="Inventory"
)
    return conn


# add_fields
@app.route('/add_product', methods=['post'])
def add_product():
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)
    
    product_name =request.form['product_name']
    cursor.execute("SELECT * FROM product WHERE product_name = %s", (product_name,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO product (product_name) VALUES (%s)", (product_name,))
        conn.commit()
    else:
        return jsonify({"message": "Product already exists"}), 400
    cursor.close()
    conn.close()
    return redirect(url_for('product'))

@app.route('/add_location', methods=['post'])
def add_location():
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)
    
    location_name =request.form['location_name']
    cursor.execute("SELECT * FROM location WHERE location_name = %s", (location_name,))
    existing = cursor.fetchone()
    if not existing:
        cursor.execute("INSERT INTO location (location_name) VALUES (%s)", (location_name,))
        conn.commit()
    else:
        return jsonify({"message": "location already exists"}), 400
    cursor.close()
    conn.close()
    return redirect(url_for('location'))

@app.route('/add_product_movement', methods=['POST'])
def add_product_movement():
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    today = datetime.date.today()
    from_location = request.form.get('from_location') or None
    to_location = request.form.get('to_location') or None
    product_id = request.form['product_id']
    qty = int(request.form['qty'])
    
    cursor.execute("""
        INSERT INTO product_movement (date, from_location, to_location, product_id, qty)
        VALUES (%s, %s, %s, %s, %s)
    """, (today, from_location, to_location, product_id, qty))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Product movement recorded successfully.", "success")
    return redirect('/product_movement')




# view_fields
@app.route('/product')
def product():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(100) UNIQUE
        )
    ''')
    cursor.execute('''SELECT * FROM product''')

    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('product.html', products=products)

@app.route('/location')
def location():
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS location (
            location_id INT AUTO_INCREMENT PRIMARY KEY,
            location_name VARCHAR(100) UNIQUE
        )
    ''')
    cursor.execute('''SELECT * FROM location''')
    
    locations = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('location.html', locations=locations)

@app.route('/product_movement')
def product_movement():
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_movement (
            movement_id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE DEFAULT (CURRENT_DATE),
            from_location INT,
            to_location INT,
            product_id INT NOT NULL,
            qty INT NOT NULL CHECK(qty>0),
            FOREIGN KEY (from_location) REFERENCES location(location_id),
            FOREIGN KEY (to_location) REFERENCES location(location_id),
            FOREIGN KEY (product_id) REFERENCES product(product_id)
        );
    ''')
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    cursor.execute("SELECT * FROM location")
    locations = cursor.fetchall()
    cursor.execute("SELECT * FROM product_movement")
    movements = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('product_movement.html',  movements=movements, products=products, locations=locations)

#update_fields
@app.route('/update_product', methods=['POST'])
def update_product():
    product_id = request.form['product_id']
    product_name = request.form['product_name']

    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE product SET product_name = %s WHERE product_id = %s", (product_name, product_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('product'))

@app.route('/update_location', methods=['POST'])
def update_location():
    location_id = request.form['location_id']
    location_name = request.form['location_name']
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("UPDATE location SET location_name = %s WHERE location_id = %s", (location_name, location_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('location'))

#report_fields
@app.route('/report')
def report():
    conn = db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_name FROM product")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, location_name FROM location")
    locations = cursor.fetchall()
    cursor.execute("SELECT product_id, from_location, to_location, qty FROM product_movement")
    movements = cursor.fetchall()
    balance = []
    for p_id, p_name in products:
        for l_id, l_name in locations:
            inbound = 0
            outbound = 0

            for m in movements:
                product_id = m[0]
                from_location = m[1]
                to_location = m[2]
                qty = m[3] or 0  

                if product_id == p_id:
                    if to_location == l_id:
                        inbound += qty
                    if from_location == l_id:
                        outbound += qty
            balance.append({
                'product': p_name,
                'location': l_name,
                'quantity': inbound - outbound
            })
            
    cursor.close()
    conn.close()
    return render_template("report.html", balance=balance)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Starting Flask App")
    app.run(debug=True)