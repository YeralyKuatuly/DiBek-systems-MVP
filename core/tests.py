from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Company, Item, Cart, CartItem, OrderRequest, Payment
from unittest.mock import patch


# Create your tests here.

class AuthTests(APITestCase):
    @patch('core.views.validate_bin', return_value=True)
    def test_signup_and_token(self, mock_validate_bin):
        resp = self.client.post(reverse('signup'), {
            'bin_number': '123456789012',
            'email': 'test@example.com',
            'password': 'Testpass123!'
        })
        self.assertEqual(resp.status_code, 201)
        resp = self.client.post(reverse('token_obtain_pair'), {
            'bin_number': '123456789012',
            'password': 'Testpass123!'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access', resp.data)


class CompaniesItemsTests(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='TestCo')
        self.item = Item.objects.create(title='Item1', price=10,
                                        company=self.company, category='cat')

    def test_list_companies(self):
        resp = self.client.get('/api/companies/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_list_items(self):
        resp = self.client.get('/api/items/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)


class CartTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(bin_number='111111111111',
                                             email='u@e.com', password='pass')
        self.company = Company.objects.create(name='TestCo')
        self.item = Item.objects.create(title='Item1', price=10,
                                        company=self.company, category='cat')
        self.client = APIClient()
        resp = self.client.post(
            reverse('token_obtain_pair'),
            {'bin_number': '111111111111', 'password': 'pass'}
        )
        self.token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_cart_add_and_remove(self):
        resp = self.client.post('/api/cart/add/', {'item': self.item.id,
                                                   'quantity': 2})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/cart/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['items']), 1)
        resp = self.client.post('/api/cart/remove/', {'item': self.item.id})
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get('/api/cart/')
        self.assertEqual(len(resp.data['items']), 0)


class OrderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(bin_number='222222222222',
                                             email='u2@e.com', password='pass')
        self.company = Company.objects.create(name='TestCo')
        self.item = Item.objects.create(title='Item1', price=10,
                                        company=self.company, category='cat')
        self.client = APIClient()
        resp = self.client.post(reverse('token_obtain_pair'),
                                {'bin_number': '222222222222',
                                'password': 'pass'})
        self.token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        self.client.post('/api/cart/add/', {'item': self.item.id,
                                            'quantity': 1})

    def test_create_order(self):
        resp = self.client.post('/api/orders/', {})
        if resp.status_code != 201:
            print(f"Order creation failed: {resp.status_code}")
            print(f"Response data: {resp.data}")
        self.assertEqual(resp.status_code, 201)
        self.assertIn('id', resp.data)

    def test_list_orders(self):
        resp = self.client.post('/api/orders/', {})
        if resp.status_code != 201:
            print(f"Order creation failed: {resp.status_code}")
            print(f"Response data: {resp.data}")
        resp = self.client.get('/api/orders/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)


class PaymentTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(bin_number='333333333333',
                                             email='u3@e.com', password='pass')
        self.company = Company.objects.create(name='TestCo')
        self.item = Item.objects.create(title='Item1', price=10,
                                        company=self.company, category='cat')
        self.client = APIClient()
        resp = self.client.post(reverse('token_obtain_pair'),
                                {'bin_number': '333333333333',
                                'password': 'pass'})
        self.token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        self.client.post('/api/cart/add/', {'item': self.item.id,
                                            'quantity': 1})
        order_resp = self.client.post('/api/orders/', {})
        if order_resp.status_code != 201:
            print(f"Order creation failed: {order_resp.status_code}")
            print(f"Response data: {order_resp.data}")
        self.order_id = order_resp.data['id']

    def test_create_payment(self):
        resp = self.client.post('/api/payments/',
                                {'user': self.user.id, 'order': self.order_id,
                                 'amount': 10, 'status': 'pending'})
        self.assertEqual(resp.status_code, 201)
        self.assertIn('id', resp.data)

    def test_list_payments(self):
        self.client.post('/api/payments/', {'user': self.user.id,
                                            'order': self.order_id,
                                            'amount': 10, 'status': 'pending'})
        resp = self.client.get('/api/payments/')
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 1)
