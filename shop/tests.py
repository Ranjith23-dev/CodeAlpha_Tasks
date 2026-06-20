from django.test import TestCase
from django.urls import reverse
from .models import Product


class ShopSmokeTests(TestCase):
    def setUp(self):
        Product.objects.create(name='Demo Product', description='Test item', price='19.99', stock=5)

    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Demo Product')

