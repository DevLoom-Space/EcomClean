from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
from devloom.models import Product, Category


class Command(BaseCommand):
    help = 'Assign static images from devloom/static/devloom/images to products. Use --preview to only show mapping.'

    def add_arguments(self, parser):
        parser.add_argument('--preview', action='store_true', help='Show mapping without writing changes')

    def handle(self, *args, **options):
        preview = options.get('preview', False)
        images_dir = os.path.join(settings.BASE_DIR, 'devloom', 'static', 'devloom', 'images')
        if not os.path.isdir(images_dir):
            self.stdout.write(self.style.ERROR(f'Images directory not found: {images_dir}'))
            return

        files = [f for f in os.listdir(images_dir)
                 if os.path.isfile(os.path.join(images_dir, f)) and f.split('.')[-1].lower() in ('png', 'jpg', 'jpeg', 'webp', 'gif', 'svg')]

        if not files:
            self.stdout.write(self.style.WARNING('No image files found in images directory.'))
            return

        # Build categories map
        categories = {c.name.lower(): c for c in Category.objects.all()}

        # Simple keyword map to infer category from filename
        keyword_map = {
            'laptop': 'laptops', 'notebook': 'laptops', 'macbook': 'laptops',
            'desktop': 'desktops', 'tower': 'desktops', 'workstation': 'desktops',
            'accessory': 'accessories', 'accessories': 'accessories', 'mouse': 'accessories', 'keyboard': 'accessories', 'bag': 'accessories', 'charger': 'accessories'
        }

        # preload products grouped by category
        products_by_cat = {}
        for c in Category.objects.all():
            products_by_cat[c.name.lower()] = list(c.products.all())

        assignments = []  # list of (filename, Product or None)

        for fname in files:
            fn = fname.lower()
            assigned = False

            # try keyword-based category assignment
            for kw, catname in keyword_map.items():
                if kw in fn:
                    cat = categories.get(catname)
                    if cat:
                        # try to match product by name substring
                        prod = None
                        tokens = re.split(r'[^a-z0-9]+', fn)
                        for p in products_by_cat.get(cat.name.lower(), []):
                            pname = p.name.lower()
                            if pname in fn:
                                prod = p
                                break
                            # try tokens matching product name parts
                            for t in tokens:
                                if len(t) > 2 and t in pname:
                                    prod = p
                                    break
                            if prod:
                                break

                        # fallback: first product in category without an image
                        if not prod:
                            for p in products_by_cat.get(cat.name.lower(), []):
                                if not p.image:
                                    prod = p
                                    break
                        # final fallback: first product in category
                        if not prod and products_by_cat.get(cat.name.lower()):
                            prod = products_by_cat[cat.name.lower()][0]

                        assignments.append((fname, prod))
                        assigned = True
                        break
            if assigned:
                continue

            # fallback: attempt to find a product across all categories by name substring
            prod = None
            for p in Product.objects.all():
                if p.name.lower() in fn:
                    prod = p
                    break
            assignments.append((fname, prod))

        # Print preview
        self.stdout.write('\nImage -> Product preview mapping:')
        for fname, prod in assignments:
            if prod:
                self.stdout.write(f'  {fname} -> {prod.category.name} / {prod.name}')
            else:
                self.stdout.write(f'  {fname} -> UNASSIGNED')

        if preview:
            self.stdout.write(self.style.SUCCESS('\nPreview complete. Run without --preview to apply these assignments.'))
            return

        # Apply assignments
        changed = 0
        for fname, prod in assignments:
            if prod:
                rel = f'devloom/images/{fname}'
                prod.image = rel
                prod.save()
                changed += 1

        self.stdout.write(self.style.SUCCESS(f'Applied assignments. Updated image field on {changed} products.'))
