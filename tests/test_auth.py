import os
os.environ['MONGO_URI'] = ''
import unittest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from backend.database import Base, get_db
from backend.main import app
from backend.services.auth_service import Account, AccountSession

class AccountTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        def override(): yield self.db
        app.dependency_overrides[get_db] = override
        self.client = TestClient(app)
        self.details = {'name': 'Ananya Rao', 'email': 'ananya@example.com', 'password': 'secure-pass-123'}
    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()
    def test_signup_login_reload_logout_and_password_storage(self):
        response = self.client.post('/auth/signup', json=self.details)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()['name'], 'Ananya Rao')
        self.assertNotIn('password', response.text)
        self.assertIn('HttpOnly', response.headers['set-cookie'])
        self.assertNotEqual(self.db.query(Account).one().password_hash, self.details['password'])
        self.assertEqual(self.client.get('/auth/me').json()['name'], 'Ananya Rao')
        token = self.client.cookies.get('boli_session')
        self.assertEqual(self.client.post('/auth/logout').status_code, 204)
        self.assertEqual(self.client.get('/auth/me').status_code, 401)
        self.assertEqual(self.client.get('/auth/me', headers={'Cookie': 'boli_session='+token}).status_code, 401)
        response = self.client.post('/auth/login', json={**self.details, 'email':'ANANYA@example.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Ananya Rao')
    def test_unknown_incorrect_duplicate_and_invalid_accounts(self):
        self.assertEqual(self.client.post('/auth/login', json=self.details).status_code, 401)
        self.client.post('/auth/signup', json=self.details)
        self.assertEqual(self.client.post('/auth/signup', json={**self.details, 'email':'ANANYA@example.com'}).status_code, 409)
        self.assertEqual(self.client.post('/auth/login', json={**self.details, 'password':'wrong'}).status_code, 401)
        for fields in [{'name':'  '}, {'password':'short'}, {'email':'not-an-email'}]:
            self.assertEqual(self.client.post('/auth/signup', json={**self.details, **fields}).status_code, 422)
    def test_expired_session_and_different_account_identity(self):
        self.client.post('/auth/signup', json=self.details)
        session = self.db.query(AccountSession).one()
        session.expires_at = datetime.utcnow() - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.client.get('/auth/me').status_code, 401)
        response = self.client.post('/auth/signup', json={**self.details, 'name':'Kiran Kumar', 'email':'kiran@example.com'})
        self.assertEqual(response.json()['name'], 'Kiran Kumar')
        self.assertEqual(self.client.get('/auth/me').json()['name'], 'Kiran Kumar')

if __name__ == '__main__': unittest.main()
