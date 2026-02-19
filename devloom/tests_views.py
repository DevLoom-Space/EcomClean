from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ViewsCartTests(TestCase):
    def test_home_renders(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'devloom/home.html')

    def test_add_to_cart_increments_session(self):
        cat = Category.objects.create(name='TestCat')
        p = Product.objects.create(category=cat, name='Widget', price='9.99', stock=10)

        # session should start empty for cart_count
        session = self.client.session
        self.assertNotIn('cart_count', session)

        resp = self.client.get(reverse('add_to_cart', args=[p.id]))
        # view redirects back to product detail
        self.assertEqual(resp.status_code, 302)

        session = self.client.session
        self.assertEqual(int(session.get('cart_count', 0)), 1)
