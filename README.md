# CraftConnect — Digital Marketplace for Local Artisans

A full-stack MVP built with **Flask + SQLite**, following the frozen project spec:
Customer / Artisan / Admin roles, product browsing & search, cart & simulated
checkout, order tracking, artisan product & order management, and an admin
dashboard with artisan verification.

## 1. Setup

```bash
cd craftconnect
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Create & seed the database

This creates `craftconnect.db` and loads demo categories, products, and
three ready-to-use accounts.

```bash
python seed.py
```

Demo logins:

| Role     | Email                     | Password    |
|----------|----------------------------|-------------|
| Admin    | admin@craftconnect.com     | admin123    |
| Artisan  | priya@craftconnect.com     | artisan123  |
| Customer | raj@example.com            | customer123 |

## 3. Run the app

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## 4. What's implemented (MVP scope)

- **Customer**: register/login, browse & search products by category,
  product detail with reviews, cart, checkout with a simulated
  UPI/Card/COD payment, order history & tracking, product reviews.
- **Artisan**: register/login, dashboard with stats (products, orders,
  sales), add/edit/delete products with photo upload, manage stock &
  status, view & update order status (Pending → Preparing → Shipped →
  Delivered).
- **Admin**: dashboard with platform-wide stats, verify/reject artisans,
  view all customers, products, and orders.
- Password hashing, session-based auth (Flask-Login), and role-based
  route protection (`@role_required`) so e.g. a customer can't open
  `/admin/dashboard`.
- Responsive layout (mobile/tablet/desktop) with a custom design system
  (see `static/css/style.css`) themed around the handicraft domain.

## 5. Next steps toward the full plan

Per the frozen roadmap, remaining steps are:

1. **UI polish** — swap placeholder product thumbnails for real artisan
   photos once uploaded.
2. **Deployment** — push to a host such as Render or Railway; set a real
   `SECRET_KEY` via an environment variable and switch `debug=False`.
3. **Physical prototype** — build the CraftConnect Artisan Showcase Kiosk
   with a QR code that links to `/products` or a specific artisan's
   products (e.g. `/products?category=<id>`).
4. **PPT + documentation + viva prep** — use section 34 of the project
   plan ("Final Project Summary") as your talking points.

## 6. Project structure

```
craftconnect/
├── app.py                  # Flask app & all routes
├── models.py                # SQLAlchemy models (User, Artisan, Category, Product, Order, OrderItem, Review)
├── seed.py                  # Creates DB + demo data
├── requirements.txt
├── static/
│   ├── css/style.css
│   └── uploads/              # artisan-uploaded product photos
└── templates/                # Jinja2 templates for all pages
```

## Note on this environment

This project was written and syntax-checked here, but `flask-sqlalchemy`
and `flask-login` couldn't be pip-installed in this sandbox (no internet
access), so it hasn't been run end-to-end yet. Run it locally following
the steps above — if anything doesn't behave as expected, send me the
error and I'll fix it.
