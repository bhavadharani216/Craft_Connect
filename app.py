import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from models import db, User, Artisan, Category, Product, Order, OrderItem, Review

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "craftconnect-dev-secret-change-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "craftconnect.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to continue."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- helpers ----------
    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

    def role_required(role):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if not current_user.is_authenticated or current_user.role != role:
                    abort(403)
                return f(*args, **kwargs)
            return wrapped
        return decorator

    def get_cart():
        return session.setdefault("cart", {})  # {product_id(str): qty}

    def cart_details():
        cart = get_cart()
        items = []
        total = 0
        for pid, qty in cart.items():
            product = Product.query.get(int(pid))
            if not product:
                continue
            subtotal = product.price * qty
            total += subtotal
            items.append({"product": product, "qty": qty, "subtotal": subtotal})
        return items, total

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        return {"cart_count": sum(cart.values()) if cart else 0}

    # ---------- public / customer routes ----------
    @app.route("/")
    def index():
        categories = Category.query.all()
        featured = Product.query.filter_by(status="active").order_by(Product.created_at.desc()).limit(8).all()
        return render_template("index.html", categories=categories, featured=featured)

    @app.route("/products")
    def products():
        q = request.args.get("q", "").strip()
        category_id = request.args.get("category", type=int)
        query = Product.query.filter_by(status="active")
        if q:
            query = query.filter(Product.name.ilike(f"%{q}%"))
        if category_id:
            query = query.filter_by(category_id=category_id)
        items = query.order_by(Product.created_at.desc()).all()
        categories = Category.query.all()
        return render_template("products.html", products=items, categories=categories,
                                q=q, selected_category=category_id)

    @app.route("/product/<int:product_id>")
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        return render_template("product_detail.html", product=product)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "customer")
            if role not in ("customer", "artisan"):
                role = "customer"

            if not name or not email or not password:
                flash("Please fill in all fields.", "error")
                return redirect(url_for("register"))

            if User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "error")
                return redirect(url_for("register"))

            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            if role == "artisan":
                business_name = request.form.get("business_name", "").strip() or f"{name}'s Crafts"
                artisan = Artisan(user_id=user.id, business_name=business_name,
                                   location=request.form.get("location", "").strip())
                db.session.add(artisan)

            db.session.commit()
            login_user(user)
            flash("Welcome to CraftConnect!", "success")
            if role == "artisan":
                return redirect(url_for("artisan_dashboard"))
            return redirect(url_for("index"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Logged in successfully.", "success")
                if user.role == "admin":
                    return redirect(url_for("admin_dashboard"))
                if user.role == "artisan":
                    return redirect(url_for("artisan_dashboard"))
                return redirect(url_for("index"))
            flash("Invalid email or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You've been logged out.", "success")
        return redirect(url_for("index"))

    # ---------- cart / checkout ----------
    @app.route("/cart")
    def cart():
        items, total = cart_details()
        return render_template("cart.html", items=items, total=total)

    @app.route("/cart/add/<int:product_id>", methods=["POST"])
    def cart_add(product_id):
        product = Product.query.get_or_404(product_id)
        cart = get_cart()
        qty = int(request.form.get("qty", 1))
        pid = str(product_id)
        cart[pid] = cart.get(pid, 0) + max(qty, 1)
        session.modified = True
        flash(f'Added "{product.name}" to your cart.', "success")
        return redirect(request.referrer or url_for("products"))

    @app.route("/cart/update/<int:product_id>", methods=["POST"])
    def cart_update(product_id):
        cart = get_cart()
        qty = int(request.form.get("qty", 1))
        pid = str(product_id)
        if qty <= 0:
            cart.pop(pid, None)
        else:
            cart[pid] = qty
        session.modified = True
        return redirect(url_for("cart"))

    @app.route("/cart/remove/<int:product_id>")
    def cart_remove(product_id):
        cart = get_cart()
        cart.pop(str(product_id), None)
        session.modified = True
        return redirect(url_for("cart"))

    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        items, total = cart_details()
        if not items:
            flash("Your cart is empty.", "error")
            return redirect(url_for("products"))

        if request.method == "POST":
            address = request.form.get("address", "").strip()
            payment_method = request.form.get("payment_method", "COD")

            order = Order(
                customer_id=current_user.id,
                total_amount=total,
                payment_method=payment_method,
                payment_status="SUCCESS",  # simulated/demo payment
                order_status="Pending",
                shipping_address=address,
            )
            db.session.add(order)
            db.session.flush()

            for item in items:
                product = item["product"]
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    artisan_id=product.artisan_id,
                    quantity=item["qty"],
                    price=product.price,
                ))
                product.stock = max(product.stock - item["qty"], 0)

            db.session.commit()
            session["cart"] = {}
            session.modified = True
            return redirect(url_for("order_confirmation", order_id=order.id))

        return render_template("checkout.html", items=items, total=total)

    @app.route("/order-confirmation/<int:order_id>")
    @login_required
    def order_confirmation(order_id):
        order = Order.query.get_or_404(order_id)
        if order.customer_id != current_user.id:
            abort(403)
        return render_template("order_confirmation.html", order=order)

    @app.route("/my-orders")
    @login_required
    def my_orders():
        orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("my_orders.html", orders=orders)

    @app.route("/review/<int:product_id>", methods=["POST"])
    @login_required
    def add_review(product_id):
        product = Product.query.get_or_404(product_id)
        rating = int(request.form.get("rating", 5))
        comment = request.form.get("comment", "").strip()
        review = Review(customer_id=current_user.id, product_id=product.id,
                         rating=max(1, min(rating, 5)), comment=comment)
        db.session.add(review)
        db.session.commit()
        flash("Thanks for your review!", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    # ---------- artisan routes ----------
    @app.route("/artisan/dashboard")
    @login_required
    @role_required("artisan")
    def artisan_dashboard():
        artisan = current_user.artisan_profile
        products_count = len(artisan.products)
        product_ids = [p.id for p in artisan.products]
        items = OrderItem.query.filter(OrderItem.artisan_id == artisan.id).all()
        total_sales = sum(i.price * i.quantity for i in items)
        recent_order_ids = sorted({i.order_id for i in items}, reverse=True)[:5]
        recent_orders = Order.query.filter(Order.id.in_(recent_order_ids)).all() if recent_order_ids else []
        pending = sum(1 for i in items if i.order.order_status == "Pending")
        return render_template("artisan_dashboard.html", artisan=artisan,
                                products_count=products_count, total_sales=total_sales,
                                recent_orders=recent_orders, pending=pending,
                                total_orders=len({i.order_id for i in items}))

    @app.route("/artisan/products")
    @login_required
    @role_required("artisan")
    def artisan_products():
        artisan = current_user.artisan_profile
        return render_template("artisan_products.html", products=artisan.products)

    @app.route("/artisan/products/add", methods=["GET", "POST"])
    @login_required
    @role_required("artisan")
    def artisan_add_product():
        categories = Category.query.all()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            price = request.form.get("price", type=float)
            stock = request.form.get("stock", type=int) or 0
            category_id = request.form.get("category_id", type=int)
            description = request.form.get("description", "").strip()

            image_filename = ""
            file = request.files.get("image")
            if file and file.filename and allowed_file(file.filename):
                image_filename = secure_filename(f"{current_user.id}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))

            if not name or not price:
                flash("Product name and price are required.", "error")
                return redirect(url_for("artisan_add_product"))

            product = Product(
                artisan_id=current_user.artisan_profile.id,
                category_id=category_id,
                name=name, description=description,
                price=price, stock=stock,
                image=image_filename,
            )
            db.session.add(product)
            db.session.commit()
            flash("Product added.", "success")
            return redirect(url_for("artisan_products"))

        return render_template("artisan_add_product.html", categories=categories, product=None)

    @app.route("/artisan/products/edit/<int:product_id>", methods=["GET", "POST"])
    @login_required
    @role_required("artisan")
    def artisan_edit_product(product_id):
        product = Product.query.get_or_404(product_id)
        if product.artisan_id != current_user.artisan_profile.id:
            abort(403)
        categories = Category.query.all()
        if request.method == "POST":
            product.name = request.form.get("name", product.name).strip()
            product.price = request.form.get("price", type=float) or product.price
            product.stock = request.form.get("stock", type=int) or 0
            product.category_id = request.form.get("category_id", type=int)
            product.description = request.form.get("description", "").strip()
            product.status = request.form.get("status", product.status)

            file = request.files.get("image")
            if file and file.filename and allowed_file(file.filename):
                image_filename = secure_filename(f"{current_user.id}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_filename))
                product.image = image_filename

            db.session.commit()
            flash("Product updated.", "success")
            return redirect(url_for("artisan_products"))

        return render_template("artisan_add_product.html", categories=categories, product=product)

    @app.route("/artisan/products/delete/<int:product_id>", methods=["POST"])
    @login_required
    @role_required("artisan")
    def artisan_delete_product(product_id):
        product = Product.query.get_or_404(product_id)
        if product.artisan_id != current_user.artisan_profile.id:
            abort(403)
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted.", "success")
        return redirect(url_for("artisan_products"))

    @app.route("/artisan/orders")
    @login_required
    @role_required("artisan")
    def artisan_orders():
        artisan = current_user.artisan_profile
        items = OrderItem.query.filter_by(artisan_id=artisan.id).all()
        order_ids = sorted({i.order_id for i in items}, reverse=True)
        orders = Order.query.filter(Order.id.in_(order_ids)).all() if order_ids else []
        orders.sort(key=lambda o: o.created_at, reverse=True)
        return render_template("artisan_orders.html", orders=orders, artisan_id=artisan.id)

    @app.route("/artisan/orders/<int:order_id>/status", methods=["POST"])
    @login_required
    @role_required("artisan")
    def artisan_update_order_status(order_id):
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get("status")
        if new_status in ("Pending", "Preparing", "Shipped", "Delivered"):
            order.order_status = new_status
            db.session.commit()
            flash("Order status updated.", "success")
        return redirect(url_for("artisan_orders"))

    # ---------- admin routes ----------
    @app.route("/admin/dashboard")
    @login_required
    @role_required("admin")
    def admin_dashboard():
        stats = {
            "users": User.query.filter_by(role="customer").count(),
            "artisans": Artisan.query.count(),
            "products": Product.query.count(),
            "orders": Order.query.count(),
            "revenue": sum(o.total_amount for o in Order.query.filter_by(payment_status="SUCCESS").all()),
        }
        pending_artisans = Artisan.query.filter_by(verification_status="pending").all()
        return render_template("admin_dashboard.html", stats=stats, pending_artisans=pending_artisans)

    @app.route("/admin/artisans")
    @login_required
    @role_required("admin")
    def admin_artisans():
        artisans = Artisan.query.all()
        return render_template("admin_artisans.html", artisans=artisans)

    @app.route("/admin/artisans/<int:artisan_id>/verify", methods=["POST"])
    @login_required
    @role_required("admin")
    def admin_verify_artisan(artisan_id):
        artisan = Artisan.query.get_or_404(artisan_id)
        artisan.verification_status = request.form.get("status", "verified")
        db.session.commit()
        flash("Artisan status updated.", "success")
        return redirect(url_for("admin_artisans"))

    @app.route("/admin/users")
    @login_required
    @role_required("admin")
    def admin_users():
        users = User.query.filter_by(role="customer").all()
        return render_template("admin_users.html", users=users)

    @app.route("/admin/products")
    @login_required
    @role_required("admin")
    def admin_products():
        products = Product.query.all()
        return render_template("admin_products.html", products=products)

    @app.route("/admin/orders")
    @login_required
    @role_required("admin")
    def admin_orders():
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return render_template("admin_orders.html", orders=orders)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have access to this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="That page doesn't exist."), 404

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
