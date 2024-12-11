from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, create_engine, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import datetime

# Initialize the database base
Base = declarative_base()

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

# Example data for testing
todos = [
    {'id': 1, 'task': 'Write code'},
    {'id': 2, 'task': 'Read book'}
]

# Utility function to find todo by id
def find_todo_by_id(todo_id):
    return next((item for item in todos if item['id'] == todo_id), None)

@app.route('/')
def home():
    return 'Welcome to the API!'

# Get all todos
@app.route('/todos', methods=['GET'])
def get_todos():
    return jsonify(todos)

# Get a single todo by ID
@app.route('/todos/<int:id>', methods=['GET'])
def get_todo(id):
    todo = find_todo_by_id(id)
    if todo:
        return jsonify(todo)
    return jsonify({'error': 'Todo not found'}), 404

# Create a new todo
@app.route('/todos', methods=['POST'])
def add_todo():
    new_todo = request.get_json()
    todos.append(new_todo)
    return jsonify(new_todo), 201

# Update an existing todo
@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = find_todo_by_id(id)
    if todo:
        data = request.get_json()
        todo.update(data)
        return jsonify(todo)
    return jsonify({'error': 'Todo not found'}), 404

# Delete a todo
@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    global todos
    todos = [todo for todo in todos if todo['id'] != id]
    return jsonify({'message': 'Todo deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)

# Database engine for SQLAlchemy
engine = create_engine('mysql+mysqlconnector://root:music123@localhost/ecommerce_api2')

# Create tables in the database
Base.metadata.create_all(engine)
