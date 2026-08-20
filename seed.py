"""
Run this once to set up the database and load demo data:

    python seed.py

Creates:
  - an admin account       admin@craftconnect.com   / admin123
  - a demo artisan account priya@craftconnect.com   / artisan123
  - a demo customer        raj@example.com           / customer123
  - a handful of categories and sample products
"""
from app import create_app
from models import db, User, Artisan, Category, Product

app = create_app()

SAMPLE_PRODUCTS = [
    ("Handmade Terracotta Pot", "Terracotta", 450, 20,
     "Hand-shaped terracotta pot, fired in a traditional kiln. Great for indoor plants."),
    ("Woven Bamboo Basket", "Bamboo Crafts", 700, 15,
     "Sturdy bamboo basket, hand-woven using traditional techniques."),
    ("Silver Oxidised Necklace", "Jewellery", 950, 10,
     "Hand-finished oxidised silver necklace with traditional tribal motifs."),
    ("Handloom Cotton Stole", "Handloom", 550, 25,
     "Soft handloom cotton stole, woven on a traditional pit loom."),
    ("Carved Wooden Elephant", "Wooden Crafts", 620, 12,
     "Hand-carved rosewood elephant figurine, polished finish."),
    ("Clay Diya Set (6 pcs)", "Terracotta", 250, 40,
     "Set of six hand-painted clay diyas, perfect for festive decor."),
]


def run():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Categories
        category_names = ["Terracotta", "Bamboo Crafts", "Jewellery", "Handloom", "Wooden Crafts", "Pottery"]
        categories = {}
        for cname in category_names:
            c = Category(name=cname)
            db.session.add(c)
            categories[cname] = c
        db.session.flush()

        # Admin
        admin = User(name="CraftConnect Admin", email="admin@craftconnect.com", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Demo artisan
        artisan_user = User(name="Priya Sharma", email="priya@craftconnect.com", role="artisan")
        artisan_user.set_password("artisan123")
        db.session.add(artisan_user)
        db.session.flush()

        artisan = Artisan(
            user_id=artisan_user.id,
            business_name="Priya Crafts",
            description="Handmade terracotta, bamboo and wooden crafts made by local artisans.",
            location="Coimbatore, Tamil Nadu",
            verification_status="verified",
        )
        db.session.add(artisan)
        db.session.flush()

        # Demo customer
        customer = User(name="Raj Kumar", email="raj@example.com", role="customer")
        customer.set_password("customer123")
        db.session.add(customer)

        # Products
        for name, cat, price, stock, desc in SAMPLE_PRODUCTS:
            db.session.add(Product(
                artisan_id=artisan.id,
                category_id=categories[cat].id,
                name=name, description=desc, price=price, stock=stock,
                status="active",
            ))

        db.session.commit()
        print("Database created and seeded successfully.")
        print("Admin login:    admin@craftconnect.com / admin123")
        print("Artisan login:  priya@craftconnect.com / artisan123")
        print("Customer login: raj@example.com / customer123")


if __name__ == "__main__":
    run()
