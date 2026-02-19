from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
from devloom.models import Product, Category


class Command(BaseCommand):
    help = 'Ensure every product image file has a Product; create products as needed and assign images. Use --preview first.'

    def add_arguments(self, parser):
        parser.add_argument('--preview', action='store_true', help='Show planned creations/assignments without saving')
        parser.add_argument('--apply', action='store_true', help='Apply planned creations/assignments')

    def handle(self, *args, **options):
        preview = options.get('preview', False)
        apply = options.get('apply', False)
        images_dir = os.path.join(settings.BASE_DIR, 'devloom', 'static', 'devloom', 'images')
        if not os.path.isdir(images_dir):
            self.stdout.write(self.style.ERROR(f'Images directory not found: {images_dir}'))
            return

        files = [f for f in os.listdir(images_dir)
                 if os.path.isfile(os.path.join(images_dir, f)) and f.split('.')[-1].lower() in ('png', 'jpg', 'jpeg', 'webp', 'gif', 'svg')]

        # ignore obvious non-product images
        ignore_patterns = [r'devloom_logo', r'logo', r'online shopping', r'hero', r'background']

        product_files = []
        for f in files:
            fn = f.lower()
            if any(re.search(pat, fn) for pat in ignore_patterns):
                continue
            product_files.append(f)

        if not product_files:
            self.stdout.write(self.style.WARNING('No candidate product images found.'))
            return

        # keyword map for categories
        keyword_map = {
            'laptop': 'Laptops', 'notebook': 'Laptops', 'macbook': 'Laptops',
            'desktop': 'Desktops', 'tower': 'Desktops', 'workstation': 'Desktops',
            'accessory': 'Accessories', 'accessories': 'Accessories', 'mouse': 'Accessories', 'keyboard': 'Accessories', 'bag': 'Accessories', 'charger': 'Accessories'
        }

        categories = {c.name.lower(): c for c in Category.objects.all()}
        default_category = None
        if 'laptops' in categories:
            default_category = categories['laptops']
        else:
            # pick any category
            default_category = next(iter(categories.values())) if categories else None

        planned = []  # tuples: (filename, existing_product_or_none, create_flag, target_category)
        reserved_product_ids = set()

        # existing images mapping
        existing_images = {p.image: p for p in Product.objects.exclude(image__isnull=True).exclude(image__exact='')}

        for fname in product_files:
            relpath = f'devloom/images/{fname}'
            if relpath in existing_images:
                # already assigned
                planned.append((fname, existing_images[relpath], False, None))
                continue

            # infer category
            fn = fname.lower()
            inferred = None
            for kw, cname in keyword_map.items():
                if kw in fn:
                    inferred = categories.get(cname.lower())
                    if inferred:
                        break
            if not inferred:
                # fallback: try to find category name in filename
                for cname, cobj in categories.items():
                    if cname in fn:
                        inferred = cobj
                        break
            if not inferred:
                inferred = default_category

            # find a product in that category without an image
            target_product = None
            if inferred:
                for p in inferred.products.all():
                    if not p.image:
                        target_product = p
                        break

            if target_product:
                # reserve this product so we don't reuse it for multiple files
                if target_product.id in reserved_product_ids:
                    # try to find another product in the category not yet reserved
                    next_prod = None
                    for p in inferred.products.all():
                        if not p.image and p.id not in reserved_product_ids:
                            next_prod = p
                            break
                    if next_prod:
                        target_product = next_prod
                    else:
                        # no available product, mark to create a new one
                        target_product = None

                if target_product:
                    reserved_product_ids.add(target_product.id)
                    planned.append((fname, target_product, False, inferred))
                else:
                    planned.append((fname, None, True, inferred))
            else:
                # will create a new product
                planned.append((fname, None, True, inferred))

        # report preview
        self.stdout.write('\nPlanned assignments:')
        creates = 0
        assigns = 0
        for fname, prod, will_create, cat in planned:
            if prod and not will_create:
                self.stdout.write(f'  {fname} -> existing {prod.category.name} / {prod.name}')
                assigns += 1
            elif will_create:
                cname = cat.name if cat else 'UNSPECIFIED'
                self.stdout.write(f'  {fname} -> will CREATE product in {cname}')
                creates += 1
            else:
                self.stdout.write(f'  {fname} -> assign to {prod.category.name} / {prod.name}')
                assigns += 1

        self.stdout.write(self.style.SUCCESS(f'Preview: {creates} products will be created, {assigns} assignments to existing products.'))

        if preview and not apply:
            self.stdout.write(self.style.SUCCESS('\nRun with --apply to perform these changes.'))
            return

        if not apply:
            self.stdout.write(self.style.WARNING('No --apply flag provided; nothing was changed. Use --apply to apply.'))
            return

        # Apply creations and assignments
        created_count = 0
        assigned_count = 0
        for fname, prod, will_create, cat in planned:
            rel = f'devloom/images/{fname}'
            if prod and not will_create:
                prod.image = rel
                prod.save()
                assigned_count += 1
                continue
            if will_create:
                # create a product using filename
                base = os.path.splitext(fname)[0]
                # sanitize name
                name = re.sub(r'[_\-]+', ' ', base).strip()
                if not name:
                    name = 'Product'
                # ensure category
                if not cat:
                    cat = default_category
                # create product
                newp = Product.objects.create(
                    category=cat,
                    name=name,
                    description='Imported product image',
                    price=0.00,
                    stock=10,
                    image=rel
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Applied: created {created_count} products and assigned images where applicable.'))
