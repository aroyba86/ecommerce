from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, create_engine, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import datetime

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
    order_date = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))  # UTC time by default
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="orders")
    products = relationship("Product", secondary="association", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.id}, order_date={self.order_date})>"

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    product_name = Column(String(100), nullable=False)
    price = Column(Float)  # or Column(Numeric(10, 2)) for more precision

    orders = relationship("Order", secondary="association", back_populates="products")

    def __repr__(self):
        return f"<Product(id={self.id}, product_name={self.product_name}, price={self.price})>"

class Association(Base):
    __tablename__ = 'association'

    order_id = Column(Integer, ForeignKey('orders.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)

# Marshmallow schemas
class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order

class ProductSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Product

# Database engine
engine = create_engine('mysql+mysqlconnector://root:<music123>@localhost/ecommerce_api2')

# Create tables in the database
Base.metadata.create_all(engine)
