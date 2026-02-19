from django.test import TestCase
from django.urls import reverse


class DevloomViewsTests(TestCase):
	def setUp(self):
		# create minimal objects needed for views
		from .models import Category, Product

		self.cat = Category.objects.create(name='Test Category')
		self.product = Product.objects.create(
			category=self.cat,
			name='Test Product',
			description='A product for tests',
			price=9.99,
			stock=5,
		)

	def test_home_renders(self):
		resp = self.client.get(reverse('home'))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'DevLoom')

	def test_product_list_shows_product(self):
		resp = self.client.get(reverse('product_list'))
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, self.product.name)

	def test_add_to_cart_increments_session_and_cart_view(self):
		# call add_to_cart (GET)
		resp = self.client.get(reverse('add_to_cart', args=[self.product.id]), follow=True)
		# session should have been updated
		self.assertEqual(int(self.client.session.get('cart_count', 0)), 1)

		# cart view should show the count
		resp = self.client.get(reverse('cart'))
		self.assertEqual(resp.status_code, 200)
		# the cart template shows the count (simple check)
		self.assertContains(resp, '1')

