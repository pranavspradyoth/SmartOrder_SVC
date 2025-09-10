from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
import os
import pymongo
from bson import ObjectId, json_util
import json
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
CORS(app)

client = pymongo.MongoClient(os.getenv('MONGO_URI'))
db = client[os.getenv('DATABASE_NAME')]

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Here you would normally verify the username and password
    if username == 'admin' and password == 'password':
        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
    
def serialize_order(order):
    return {
        "id": str(order["_id"]["$oid"]),
        "studentName": order.get("student"),
        "items": order.get("items", []),
        "status": order.get("status", "Order Received"),
        "createdAt": order.get("createdAt")
    }
 
# Get all orders
@app.route("/orders", methods=["GET"])
def get_orders():
    orders = json.loads(json_util.dumps(db['Orders'].find()))
    return jsonify([serialize_order(o) for o in orders])
 
# Add a new order (student placing order)
@app.route("/orders", methods=["POST"])
def add_order():
    data = request.json
    order = {
        "studentName": data.get("studentName"),
        "items": data.get("items", []),
        "status": "Order Received",
        "createdAt": data.get("createdAt")
    }
    result = db['Orders'].insert_one(order)
    order["_id"] = result.inserted_id
    return jsonify(serialize_order(order)), 201
 
# Update order status
@app.route("/orders/<order_id>", methods=["PUT"])
def update_order_status(order_id):
    data = request.json
    new_status = data.get("status")
    result = db['Orders'].update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": new_status}}
    )
    if result.modified_count == 0:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"id": order_id, "status": new_status})

def serialize_item(item):
    return {
        "_id": item["_id"],
        "name": item.get("name"),
        "price": item.get("price"),
        "stock": item.get("stock", 0),
        "available": item.get("available", True)
    }
 
# Get all items
@app.route("/items", methods=["GET"])
def get_items():
    items = json.loads(json_util.dumps(db['Menu'].find()))
    return jsonify([serialize_item(i) for i in items])
 
# Add a new item
@app.route("/items", methods=["POST"])
def add_item():
    data = request.json
    item = {
        "name": data.get("name"),
        "price": data.get("price"),
        "stock": data.get("stock", 0),
        "available": True
    }
    result = db['Menu'].insert_one(item)
    item["_id"] = result.inserted_id
    print(item)
    return jsonify({"message": "Item Added Successfully"}), 201

# Update item details (price, stock, availability)
@app.route("/items", methods=["PUT"])
def update_item():
    try:
        data = request.json
        update_fields = {}
        if "_id" in data:item_id = data["_id"]["$oid"]
        if "name" in data: update_fields["name"] = data["name"]
        if "price" in data: update_fields["price"] = data["price"]
        if "stock" in data: update_fields["stock"] = data["stock"]
        if "available" in data: update_fields["available"] = data["available"]
 
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
 
        result = db['Menu'].update_one({"_id": ObjectId(item_id)}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"error": "Item not found"}), 404
 
        updated_item = db['Menu'].find_one({"_id": ObjectId(item_id)})
        return jsonify({"message": "Item updated Successfully"}), 200

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500
 
# Delete an item
@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    result = db['Menu'].delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Item not found"}), 404
    return jsonify({"message": "Item deleted"})
    

if __name__=='__main__':
   app.run( port=5000,debug=True)