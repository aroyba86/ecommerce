from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, create_engine, func
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import ValidationError

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
    order_date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="orders")
    products = relationship("Product", secondary="association", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_date={self.order_date})>"

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    product_name = Column(String(100), nullable=False)
    price = Column(Float)
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

# Helper function for getting a single instance or returning 404
def get_instance_or_404(model, model_id, schema):
    session = Session()
    instance = session.query(model).get(model_id)
    if not instance:
        return jsonify({"error": f"{model.__name__} not found"}), 404
    return schema().dump(instance)

# Helper function for getting all instances
def get_all_instances(model, schema):
    session = Session()
    instances = session.query(model).all()
    return jsonify(schema(many=True).dump(instances))

# Helper function for creating an instance
def create_instance(model, data, schema):
    session = Session()
    try:
        instance = schema().load(data, session=session)
        session.add(instance)
        session.commit()
        return jsonify(schema().dump(instance)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

# Helper function for updating an instance
def update_instance(model, model_id, data, schema):
    session = Session()
    instance = session.query(model).get(model_id)
    if not instance:
        return jsonify({"error": f"{model.__name__} not found"}), 404
    try:
        schema().load(data, instance=instance, session=session)
        session.commit()
        return jsonify(schema().dump(instance)), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

# Helper function for deleting an instance
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
    return get_all_instances(User, UserSchema)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return get_instance_or_404(User, user_id, UserSchema)

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
    return get_all_instances(Product, ProductSchema)

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    return get_instance_or_404(Product, product_id, ProductSchema)

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
    return get_all_instances(Order, OrderSchema)

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data.get('user_id') or not data.get('product_ids'):
        return jsonify({"error": "Missing user_id or product_ids"}), 400
    session = Session()
    order = Order(user_id=data['user_id'])
    session.add(order)
    session.commit()
    
    # Associate products with order
    for product_id in data['product_ids']:
        product = session.query(Product).get(product_id)
        if product:
            order.products.append(product)
    session.commit()

    return jsonify(OrderSchema().dump(order)), 201

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    return get_instance_or_404(Order, order_id, OrderSchema)

@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.get_json()
    return update_instance(Order, order_id, data, OrderSchema)

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    return delete_instance(Order, order_id)

# Error handling
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request', 'message': error.description}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': error.description}), 404

# Initialize database
if __name__ == '__main__':
    Base.metadata.create_all(engine)
    app.run(debug=True)
