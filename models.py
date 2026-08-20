from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer")  # customer / artisan / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    artisan_profile = db.relationship("Artisan", backref="user", uselist=False)
    orders = db.relationship("Order", backref="customer", lazy=True)
    reviews = db.relationship("Review", backref="customer", lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Artisan(db.Model):
    __tablename__ = "artisans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    business_name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    location = db.Column(db.String(160), default="")
    profile_image = db.Column(db.String(255), default="")
    verification_status = db.Column(db.String(20), default="pending")  # pending / verified / rejected

    products = db.relationship("Product", backref="artisan", lazy=True)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    products = db.relationship("Product", backref="category", lazy=True)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    artisan_id = db.Column(db.Integer, db.ForeignKey("artisans.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)
    name = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(255), default="")
    status = db.Column(db.String(20), default="active")  # active / inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship("Review", backref="product", lazy=True)

    @property
    def average_rating(self):
        if not self.reviews:
            return 0
        return round(sum(r.rating for r in self.reviews) / len(self.reviews), 1)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default="COD")
    payment_status = db.Column(db.String(20), default="PENDING")  # PENDING / SUCCESS
    order_status = db.Column(db.String(20), default="Pending")  # Pending/Preparing/Shipped/Delivered
    shipping_address = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    artisan_id = db.Column(db.Integer, db.ForeignKey("artisans.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)

    product = db.relationship("Product")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
