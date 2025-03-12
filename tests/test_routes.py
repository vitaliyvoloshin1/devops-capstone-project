"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from service import talisman
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Запускается один раз перед всеми тестами"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should Read an Account"""
        # Создаем новый аккаунт
        test_account = AccountFactory()
        resp = self.client.post(BASE_URL, json=test_account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Получаем ID созданного аккаунта
        new_account_id = resp.get_json()["id"]

        # Читаем этот аккаунт по ID
        resp = self.client.get(f"{BASE_URL}/{new_account_id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Проверяем, что данные совпадают
        data = resp.get_json()
        self.assertEqual(data["name"], test_account.name)
    def test_update_an_account(self):
        """It should Update an Account"""
        # Создаем новый аккаунт
        test_account = AccountFactory()
        resp = self.client.post(BASE_URL, json=test_account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Получаем ID созданного аккаунта
        new_account_id = resp.get_json()["id"]

        # Обновляем данные аккаунта
        updated_data = {"name": "Updated Name", "email": "updated@example.com"}
        resp = self.client.put(
            f"{BASE_URL}/{new_account_id}",
            json=updated_data,
            content_type="application/json"  # <-- Добавляем этот заголовок
        )

        
        # Проверяем, что статус HTTP_200_OK
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Проверяем, что обновленные данные сохранены
        updated_resp = self.client.get(f"{BASE_URL}/{new_account_id}")
        self.assertEqual(updated_resp.status_code, status.HTTP_200_OK)
        data = updated_resp.get_json()
        self.assertEqual(data["name"], "Updated Name")
        self.assertEqual(data["email"], "updated@example.com")
    def test_delete_an_account(self):
        """It should Delete an Account"""
        # Создаем тестовый аккаунт
        test_account = AccountFactory()
        resp = self.client.post(BASE_URL, json=test_account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Получаем ID созданного аккаунта
        new_account_id = resp.get_json()["id"]

        # Удаляем аккаунт
        resp = self.client.delete(f"{BASE_URL}/{new_account_id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Проверяем, что аккаунта больше нет
        resp = self.client.get(f"{BASE_URL}/{new_account_id}")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
    def test_list_all_accounts(self):
        """It should List all Accounts"""
        # Создаем несколько тестовых аккаунтов
        self._create_accounts(3)

        # Запрашиваем список всех аккаунтов
        resp = self.client.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Проверяем, что список не пустой
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)  # Убедимся, что получили 3 аккаунта
    def test_security_headers(self):
        """It should ensure that security headers are set by Flask-Talisman"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Frame-Options", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
        
        self.assertIn("X-Content-Type-Options", response.headers)
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertEqual(response.headers["Content-Security-Policy"], "default-src 'self'; object-src 'none'")

        self.assertIn("Referrer-Policy", response.headers)
        self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
    def test_security_headers(self):
        """It should return security headers"""
        # Убедитесь, что URL правильный (например, "/" или ваш фактический root URL)
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем заголовки безопасности
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; object-src 'none'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        # Проверяем, что все нужные заголовки присутствуют и их значения верные
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)
