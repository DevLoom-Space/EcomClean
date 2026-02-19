from django.core.management.base import BaseCommand
from devloom.models import Category, Product

class Command(BaseCommand):
    help = "Seed the devloom app with sample categories and products"

    def handle(self, *args, **options):
        categories = [
            ("Laptops", "Portable computers for work, gaming, and creation."),
            ("Desktops", "High-performance desktops and workstations."),
            ("Accessories", "Peripherals and accessories: mice, keyboards, docks, cables."),
        ]

        created = 0
        for name, desc in categories:
            cat, _ = Category.objects.get_or_create(name=name, defaults={"description": desc})

            # create 2 sample products per category if none exist
            if not cat.products.exists():
                for i in range(1, 3):
                    p = Product.objects.create(
                        category=cat,
                        name=f"{name[:-1]} Sample {i}",
                        description=f"This is a demo {name[:-1].lower()} with useful specs and features. Ideal for testing the catalog.",
                        price=999.99 if name == "Laptops" else (1299.99 if name == "Desktops" else 49.99),
                        stock=10 * i,
                    )
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Seed complete — created {created} products (if missing)."))
