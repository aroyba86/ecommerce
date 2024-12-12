from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, create_engine, func
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import ValidationError
import datetime
import uuid

# Initialize the database base and engine
Base = declarative_base()
engine = create_engine('mysql+mysqlconnector://root:music123@localhost/ecommerce_api2')
Session = sessionmaker(bind=engine)

# Models
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    address = Column(String(100), unique=True)

    orders = relationship("Order", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name})>"

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_date = Column(DateTime, default=func.now())  # UTC time by default with func.now()
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="orders")
    products = relationship("Product", secondary="association", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_date={self.order_date})>"

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    product_name = Column(String(100), nullable=False)
    price = Column(Float)  # Numeric can be used for more precision

    orders = relationship("Order", secondary="association", back_populates="products")

    def __repr__(self):
        return f"<Product(id={self.id}, product_name={self.product_name}, price={self.price})>"

class Association(Base):
    __tablename__ = 'association'

    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)

# Marshmallow schemas for serialization
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order

class ProductSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Product

# Initialize Flask app
app = Flask(__name__)

# Helper functions for CRUD operations

def get_or_404(model, model_id, schema):
    session = Session()
    instance = session.query(model).get(model_id)
    if instance is None:
        return jsonify({"error": f"{model.__name__} not found"}), 404
    return schema().dump(instance)

def get_all(model, schema):
    session = Session()
    instances = session.query(model).all()
    return jsonify(schema(many=True).dump(instances))

def create_instance(model, data, schema):
    session = Session()
    try:
        instance = schema().load(data, session=session)  # Marshmallow handles deserialization
        session.add(instance)
        session.commit()
        return jsonify(schema().dump(instance)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

def update_instance(model, model_id, data, schema):
    session = Session()
    instance = session.query(model).get(model_id)
    if not instance:
        return jsonify({"error": f"{model.__name__} not found"}), 404
    try:
        schema().load(data, instance=instance, session=session)  # Marshmallow updates the instance
        session.commit()
        return jsonify(schema().dump(instance)), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

def delete_instance(model, model_id):
    session = Session()
    instance = session.query(model).get(model_id)
    if not instance:
        return jsonify({"error": f"{model.__name__} not found"}), 404
    session.delete(instance)
    session.commit()
    return jsonify({"message": f"{model.__name__} deleted"}), 200

# Routes for Users
@app.route('/users', methods=['GET'])
def get_users():
    return get_all(User, UserSchema)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return get_or_404(User, user_id, UserSchema)

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return create_instance(User, data, UserSchema)

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    return update_instance(User, user_id, data, UserSchema)

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return delete_instance(User, user_id)

# Routes for Products
@app.route('/api/products', methods=['GET'])
def get_products():
    return get_all(Product, ProductSchema)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    return get_or_404(Product, product_id, ProductSchema)

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json()
    return create_instance(Product, data, ProductSchema)

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    return update_instance(Product, product_id, data, ProductSchema)

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    return delete_instance(Product, product_id)

# Routes for Orders
@app.route('/orders', methods=['GET'])
def get_orders():
    return get_all(Order, OrderSchema)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data.get('customer_name') or not data.get('items'):
        return jsonify({"error": "Missing customer_name or items"}), 400
    order_id = str(uuid.uuid4())  # Generate a unique order ID
    order = {
        'id': order_id,
        'customer_name': data['customer_name'],
        'items': data['items'],
        'status': 'pending'  # Default order status
    }
    orders[order_id] = order
    return jsonify(order), 201

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Get a single order by its ID"""
    order = orders.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order), 200

@app.route('/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    """Update an existing order by its ID"""
    order = orders.get(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    data = request.get_json()

    # Update the fields based on what was provided
    if 'customer_name' in data:
        order['customer_name'] = data['customer_name']
    if 'items' in data:
        order['items'] = data['items']
    if 'status' in data:
        order['status'] = data['status']

    return jsonify(order), 200

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """Delete an order by its ID"""
    order = orders.pop(order_id, None)
    if order is None:
        return jsonify({"error": "Order not found"}), 404
    return jsonify({"message": "Order deleted"}), 200


if __name__ == '__main__':
    # Create tables in the database
    Base.metadata.create_all(engine)
    app.run(debug=True)
