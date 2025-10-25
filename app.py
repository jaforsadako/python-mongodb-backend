from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import datetime

# Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"  # For session management

# MongoDB connection
uri = "mongodb+srv://jafor:aJ6tTFxdpxLf4a9@cluster0.dp7b8.mongodb.net/grocery-db?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.get_database('product_management')

# ========================
# ROUTES
# ========================

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('index.html')

# ===== Authentication =====

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)

    users_collection = db.get_collection('users')
    if users_collection.find_one({"username": username}):
        return "User already exists"
    
    users_collection.insert_one({"username": username, "password": hashed_password})
    return redirect(url_for('index'))

@app.route('/signin', methods=['POST'])
def signin():
    username = request.form['username']
    password = request.form['password']

    users_collection = db.get_collection('users')
    user = users_collection.find_one({"username": username})

    if not user or not check_password_hash(user['password'], password):
        return "Invalid credentials"

    session['username'] = username
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# ===== Products =====

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'username' not in session:
        return redirect(url_for('index'))

    name = request.form['name']
    quantity = request.form['quantity']
    price = request.form['price']
    date = datetime.datetime.now().strftime('%Y-%m-%d')

    products_collection = db.get_collection('products')
    products_collection.insert_one({
        "name": name,
        "quantity": int(quantity),
        "price": float(price),
        "date": date
    })
    return redirect(url_for('index'))

@app.route('/get_products')
def get_products():
    products_collection = db.get_collection('products')
    products = products_collection.find()
    product_list = []
    total_price = 0

    for product in products:
        product_data = {
            "_id": str(product["_id"]),
            "name": product['name'],
            "quantity": product['quantity'],
            "price": product['price']
        }
        product_list.append(product_data)
        total_price += product['quantity'] * product['price']

    return jsonify(product_list)

@app.route('/edit_product/<product_id>', methods=['POST'])
def edit_product(product_id):
    data = request.json
    products_collection = db.get_collection('products')
    products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {
            "name": data['name'],
            "quantity": int(data['quantity']),
            "price": float(data['price'])
        }}
    )
    return jsonify({"message": "Product updated successfully"})

@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    products_collection = db.get_collection('products')
    products_collection.delete_one({"_id": ObjectId(product_id)})
    return jsonify({"message": "Product deleted successfully"})

@app.route('/delete_all_products', methods=['POST'])
def delete_all_products():
    products_collection = db.get_collection('products')
    products_collection.delete_many({})
    return jsonify({"message": "All products deleted successfully"})

@app.route('/get_invoice/<date>', methods=['GET'])
def get_invoice(date):
    products_collection = db.get_collection('products')
    products = products_collection.find({"date": date})
    invoice_list = []
    total_amount = 0
    for product in products:
        invoice_list.append({
            "name": product['name'],
            "quantity": product['quantity'],
            "price": product['price']
        })
        total_amount += product['quantity'] * product['price']
    return jsonify(invoice_list)

# ========================
# MAIN
# ========================
if __name__ == '__main__':
    app.run(debug=True)
