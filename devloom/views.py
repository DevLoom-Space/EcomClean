# Contact page view (professional, with email sending and feedback)
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from django.conf import settings
from django.utils.html import strip_tags
import re

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        # Basic validation
        errors = []
        if not name or len(name) < 2:
            errors.append('Please enter your full name.')
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not email or not re.match(email_regex, email):
            errors.append('Please enter a valid email address.')
        if not message or len(message) < 10:
            errors.append('Message should be at least 10 characters long.')
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'devloom/contact.html', {'name': name, 'email': email, 'message': message})
        # Compose email
        subject = f"New Contact Form Submission from {name}"
        html_message = f"""
            <h2>Contact Form Submission</h2>
            <p><b>Name:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Message:</b><br>{message.replace('\n', '<br>')}</p>
        """
        plain_message = strip_tags(html_message)
        recipient = getattr(settings, 'CONTACT_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'devloomspace@gmail.com'
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                html_message=html_message,
            )
            messages.success(request, 'Thank you for contacting us! Your message has been sent successfully. Our team will get back to you soon.')
            return render(request, 'devloom/contact.html')
        except BadHeaderError:
            messages.error(request, 'Invalid header found. Please try again.')
        except Exception as e:
            messages.error(request, 'Sorry, there was an error sending your message. Please try again later.')
            # Optionally log the error: print(e)
        return render(request, 'devloom/contact.html', {'name': name, 'email': email, 'message': message})
    return render(request, 'devloom/contact.html')
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Product, Category
from urllib.parse import quote


def home(request):
    return render(request, 'devloom/home.html')


def product_list(request):
    """Show products. Optional GET param `category` filters by category name.

    Examples:
    - /products/                     -> all products
    - /products/?category=laptops    -> products in category named 'laptops' (case-insensitive)
    """
    category_q = request.GET.get('category')
    # annotate categories with product counts so templates can show badges
    categories = Category.objects.annotate(product_count=Count('products'))
    products = Product.objects.all()

    # total products overall (used for "All" badge)
    total_products = Product.objects.count()

    current_category = None
    if category_q:
        # try to find a matching category by name (case-insensitive)
        try:
            current_category = Category.objects.get(name__iexact=category_q)
            products = products.filter(category=current_category)
        except Category.DoesNotExist:
            # no matching category -> empty queryset
            products = products.none()

    context = {
        'products': products,
        'categories': categories,
        'current_category': current_category,
        'total_products': total_products,
    }
    return render(request, 'devloom/product_list.html', context)


import re
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    # Extract RAM and storage from description if not set
    ram = getattr(product, 'ram', None)
    storage = getattr(product, 'storage', None)
    desc = product.description or ''
    # Remove extra blank lines from description
    import re
    cleaned_desc = re.sub(r'\n{2,}', '\n', desc.strip())
    # Try to extract RAM (e.g., '16gb ram')
    if (not ram or ram == 'N/A') and desc:
        match = re.search(r'(\d{1,3})\s*gb\s*ram', desc.lower())
        if match:
            ram = f"{match.group(1)} GB"
        else:
            ram = 'N/A'
    # Try to extract storage (e.g., '256 ssd')
    if (not storage or storage == 'N/A') and desc:
        match = re.search(r'(\d{2,4})\s*(gb|tb)?\s*ssd', desc.lower())
        if match:
            size = match.group(1)
            unit = match.group(2) or 'GB'
            storage = f"{size} {unit.upper()} SSD"
        else:
            storage = 'N/A'
    return render(request, 'devloom/product_detail.html', {
        'product': product,
        'ram': ram,
        'storage': storage,
        'cleaned_desc': cleaned_desc,
    })


def add_to_cart(request, id):
    """Simple session-backed cart increment for demonstration.

    Increments `request.session['cart_count']` and redirects back to
    the product detail page.
    """
    product = get_object_or_404(Product, id=id)
    # maintain a cart_items list in session with simple {id,name,price,image,qty}
    cart = request.session.get('cart_items', [])
    # look for existing item
    found = None
    for entry in cart:
        if int(entry.get('id')) == int(id):
            found = entry
            break
    if found:
        # increment quantity
        try:
            found['qty'] = int(found.get('qty', 1)) + 1
        except Exception:
            found['qty'] = 1
    else:
        # add new item snapshot
        cart.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'image': product.image or '',
            'qty': 1,
        })
    request.session['cart_items'] = cart
    # update cart_count as total quantity
    total_qty = 0
    for entry in cart:
        try:
            total_qty += int(entry.get('qty', 0))
        except Exception:
            total_qty += 0
    request.session['cart_count'] = total_qty
    # redirect back to product detail or product list
    return redirect('product_detail', id=id)


def cart_view(request):
    count = request.session.get('cart_count', 0)
    items = request.session.get('cart_items', [])
    # compute subtotal (sum of price * qty) where price may be stored as string
    subtotal = 0.0
    for it in items:
        try:
            price = float(it.get('price', 0) or 0)
            qty = int(it.get('qty', 1))
            subtotal += price * qty
        except Exception:
            continue
    # build a prefilled WhatsApp message listing items
    if items:
        parts = []
        for it in items:
            parts.append(f"{it.get('qty', 1)}x {it.get('name')}")
        wa_text = "I'd like to order: " + ", ".join(parts)
        wa_link = f"https://wa.me/254111670942?text={quote(wa_text)}"
    else:
        wa_link = "https://wa.me/254111670942"

    # --- Recommendations logic ---
    from random import sample
    recommendations = []
    # Try to get up to 3 random laptops or accessories
    try:
        laptop_cat = Category.objects.filter(name__icontains='laptop').first()
        acc_cat = Category.objects.filter(name__icontains='accessor').first()
        products_qs = Product.objects.none()
        if laptop_cat:
            products_qs = products_qs | Product.objects.filter(category=laptop_cat)
        if acc_cat:
            products_qs = products_qs | Product.objects.filter(category=acc_cat)
        # Exclude items already in cart
        cart_ids = [it.get('id') for it in items]
        products_qs = products_qs.exclude(id__in=cart_ids)
        products = list(products_qs)
        if products:
            recommendations = sample(products, min(3, len(products)))
    except Exception:
        recommendations = []

    return render(request, 'devloom/cart.html', {
        'count': count,
        'items': items,
        'subtotal': subtotal,
        'wa_link': wa_link,
        'recommendations': recommendations,
    })


def remove_from_cart(request, id):
    # only allow POST to remove
    if request.method != 'POST':
        return redirect('cart')
    cart = request.session.get('cart_items', [])
    new_cart = [it for it in cart if int(it.get('id')) != int(id)]
    request.session['cart_items'] = new_cart
    # recompute count
    total_qty = 0
    for entry in new_cart:
        try:
            total_qty += int(entry.get('qty', 0))
        except Exception:
            pass
    request.session['cart_count'] = total_qty
    return redirect('cart')


def place_order(request):
    from .models import Order, OrderItem
    if request.method == 'POST':
        # Get customer info from POST or use placeholders
        name = request.POST.get('customer_name', '').strip() or 'Anonymous'
        email = request.POST.get('customer_email', '').strip() or 'noemail@example.com'
        cart_items = request.session.get('cart_items', [])
        if not cart_items:
            return redirect('cart')
        # Save order
        order = Order.objects.create(customer_name=name, customer_email=email)
        for it in cart_items:
            OrderItem.objects.create(
                order=order,
                product_id=it.get('id'),
                name=it.get('name', ''),
                price=it.get('price', 0),
                quantity=it.get('qty', 1),
            )
        # Send email notification to admin
        from django.conf import settings
        from django.core.mail import send_mail
        admin_email = getattr(settings, 'ADMIN_EMAIL', None)
        if admin_email:
            subject = f"New Order #{order.id} from {order.customer_name}"
            item_lines = [f"- {oi.quantity} x {oi.name} @ Ksh {oi.price}" for oi in order.items.all()]
            message = (
                f"A new order has been placed.\n\n"
                f"Order ID: {order.id}\n"
                f"Customer: {order.customer_name} <{order.customer_email}>\n"
                f"Items:\n" + '\n'.join(item_lines) + "\n\n"
                f"View in admin: /admin/devloom/order/{order.id}/"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)
        # Clear cart
        request.session['cart_items'] = []
        request.session['cart_count'] = 0
        return render(request, 'devloom/order_success.html', {'items': cart_items, 'order': order})
    # If GET, show a simple form for name/email before placing order
    cart_items = request.session.get('cart_items', [])
    if not cart_items:
        return redirect('cart')
    return render(request, 'devloom/order_checkout.html', {'items': cart_items})


# About page view
def about(request):
    return render(request, 'devloom/about.html')
