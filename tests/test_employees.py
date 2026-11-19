"""Integration checks use a temporary database and never submit email forms."""
import io
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from PIL import Image

import employee_admin as admin
from main import app


class EmployeeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "EMPLOYEE_DATABASE": str(Path(self.temp.name) / "employees.sqlite3"),
            "ADMIN_PASSWORD": "", "ADMIN_USERNAME": "owner", "ADMIN_PASSWORD_HASH": admin.password_hash("a very strong test password"),
            "ADMIN_COOKIE_SECURE": "false",
        })
        self.env.start()
        self.client = TestClient(app, follow_redirects=False)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def csrf(self, response):
        return re.search(r'name="csrf" value="([^"]+)"', response.text).group(1)

    def login(self):
        page = self.client.get('/admin/login')
        anonymous = self.client.cookies.get(admin.COOKIE)
        response = self.client.post('/admin/login', data={
            'csrf': self.csrf(page), 'username': 'owner', 'password': 'a very strong test password',
        })
        self.assertEqual(response.status_code, 303)
        self.assertNotEqual(self.client.cookies.get(admin.COOKIE), anonymous)
        return self.csrf(self.client.get('/admin/employees'))

    def photo(self):
        image = Image.new('RGB', (1600, 800), '#19645b')
        output = io.BytesIO()
        image.save(output, format='PNG')
        return ('portrait.png', output.getvalue(), 'image/png')

    def test_new_pages_load_the_same_theme_assets_behind_https_proxy(self):
        # The reverse proxy terminates HTTPS while Uvicorn receives HTTP.
        headers = {'host': 'learnandplaycv.com', 'x-forwarded-proto': 'https'}
        css_links = lambda html: re.findall(r'<link[^>]+href="([^"]+)"[^>]+rel="stylesheet"', html)
        working_styles = css_links(self.client.get('/careers', headers=headers).text)
        csrf = self.login()
        self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': 'Jane'})
        employee_id = admin.employees()[0]['id']
        for path in ['/team', '/admin/employees', '/admin/employees/new', f'/admin/employees/{employee_id}/edit']:
            page = self.client.get(path, headers=headers)
            self.assertEqual(page.status_code, 200)
            styles = css_links(page.text)
            self.assertEqual(styles[:len(working_styles)], working_styles, path)
            for asset in styles + re.findall(r'<script[^>]+src="([^"]+)"', page.text):
                self.assertTrue(asset.startswith('/static/'), f'{path}: {asset}')
                response = self.client.get(asset)
                self.assertEqual(response.status_code, 200, asset)
                if '.css' in asset:
                    self.assertIn('text/css', response.headers['content-type'])
        self.client.post('/admin/logout', data={'csrf': csrf})
        login_page = self.client.get('/admin/login', headers=headers)
        self.assertEqual(css_links(login_page.text)[:len(working_styles)], working_styles)

    def test_employee_lifecycle_and_photo_persistence(self):
        csrf = self.login()
        response = self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': 'Jane Smith', 'title': 'Lead Teacher', 'sort_order': '4'}, files={'photo': self.photo()})
        self.assertEqual(response.status_code, 303)
        employee = admin.employees()[0]
        employee_id = employee['id']
        public = self.client.get('/team')
        self.assertIn('Jane Smith', public.text)
        self.assertIn('Lead Teacher', public.text)
        photo = self.client.get(f'/team/photos/{employee_id}')
        self.assertEqual(photo.headers['content-type'], 'image/jpeg')
        with Image.open(io.BytesIO(photo.content)) as image:
            self.assertEqual(image.size, (1200, 600))
        # A second application client reads the same durable record.
        with TestClient(app) as visitor:
            self.assertIn('Jane Smith', visitor.get('/team').text)
        self.assertEqual(self.client.get(f'/admin/employees/{employee_id}/edit').status_code, 200)
        response = self.client.post(f'/admin/employees/{employee_id}/edit', data={'csrf': csrf, 'name': 'Jane Updated', 'title': '', 'sort_order': '0'})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.client.get(f'/team/photos/{employee_id}').status_code, 200)
        previous_version = admin.employees()[0]['photo_version']
        self.client.post(f'/admin/employees/{employee_id}/edit', data={'csrf': csrf, 'name': 'Jane Updated'}, files={'photo': self.photo()})
        self.assertNotEqual(admin.employees()[0]['photo_version'], previous_version)
        self.assertIn('Jane Updated', self.client.get('/team').text)
        self.client.post(f'/admin/employees/{employee_id}/edit', data={'csrf': csrf, 'name': 'Jane Updated', 'sort_order': '0', 'remove_photo': 'true'})
        self.assertEqual(self.client.get(f'/team/photos/{employee_id}').status_code, 404)
        self.assertIsNone(admin.employees()[0]['photo_version'])
        response = self.client.post(f'/admin/employees/{employee_id}/delete', data={'csrf': csrf})
        self.assertEqual(response.status_code, 303)
        self.assertNotIn('Jane Updated', self.client.get('/team').text)
        self.assertEqual(len(admin.employees()), 0)

    def test_access_csrf_session_rotation_and_logout(self):
        for path in ['/admin/employees', '/admin/employees/new', '/admin/employees/1/edit']:
            self.assertEqual(self.client.get(path).headers['location'], '/admin/login')
        self.assertEqual(self.client.post('/admin/employees/new', data={'name': 'Intruder'}).status_code, 403)
        csrf = self.login()
        self.assertEqual(self.client.post('/admin/employees/new', data={'csrf': 'wrong', 'name': 'Intruder'}).status_code, 403)
        self.assertEqual(self.client.post('/admin/employees/1/delete', data={'csrf': 'wrong'}).status_code, 403)
        self.assertEqual(self.client.post('/admin/employees/new', data={'csrf': 'invalid ☀', 'name': 'Intruder'}).status_code, 403)
        self.assertEqual(self.client.post('/admin/logout', data={'csrf': csrf}).status_code, 303)
        self.assertEqual(self.client.get('/admin/employees').headers['location'], '/admin/login')
        self.assertEqual(self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': 'Intruder'}).status_code, 403)

    def test_invalid_photos_and_fields_preserve_existing_data(self):
        csrf = self.login()
        for data, files in [
            ({'name': ' '}, None),
            ({'name': 'Jane', 'sort_order': '-1'}, None),
            ({'name': 'Jane', 'title': 'x' * 121}, None),
            ({'name': 'Jane'}, {'photo': ('fake.jpg', b'<script>alert(1)</script>', 'image/jpeg')}),
            ({'name': 'Jane'}, {'photo': ('large.png', b'x' * (admin.MAX_PHOTO_BYTES + 1), 'image/png')}),
        ]:
            response = self.client.post('/admin/employees/new', data={'csrf': csrf, **data}, files=files)
            self.assertEqual(response.status_code, 400, response.text)
            self.assertEqual(len(admin.employees()), 0)
        self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': 'Jane'})
        employee_id = admin.employees()[0]['id']
        response = self.client.post(f'/admin/employees/{employee_id}/edit', data={'csrf': csrf, 'name': 'Changed'}, files={'photo': ('bad.jpg', b'bad', 'image/jpeg')})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(admin.employees()[0]['name'], 'Jane')

    def test_ordering_and_html_escaping(self):
        csrf = self.login()
        for name, order in [('Last', '5'), ('<script>alert(1)</script>', '0'), ('Same order', '0')]:
            self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': name, 'sort_order': order})
        public = self.client.get('/team').text
        self.assertNotIn('<script>alert(1)</script>', public)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', public)
        self.assertEqual([e['name'] for e in admin.employees()], ['<script>alert(1)</script>', 'Same order', 'Last'])

    def test_login_throttling_and_expired_session(self):
        csrf = self.csrf(self.client.get('/admin/login'))
        for _ in range(10):
            response = self.client.post('/admin/login', data={'csrf': csrf, 'username': 'owner', 'password': 'bad'})
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.client.post('/admin/login', data={'csrf': csrf, 'username': 'owner', 'password': 'bad'}).status_code, 429)
        with admin.database() as db:
            db.execute('DELETE FROM login_attempts')
        csrf = self.login()
        with admin.database() as db:
            db.execute('UPDATE admin_sessions SET expires = ?', (int(time.time()) - 1,))
        self.assertEqual(self.client.post('/admin/employees/new', data={'csrf': csrf, 'name': 'Expired'}).status_code, 403)

    def test_password_from_env_takes_precedence_over_legacy_hash(self):
        with patch.dict(os.environ, {'ADMIN_PASSWORD': 'my direct env password ☀'}):
            page = self.client.get('/admin/login')
            csrf = self.csrf(page)
            response = self.client.post('/admin/login', data={
                'csrf': csrf, 'username': 'owner', 'password': 'a very strong test password',
            })
            self.assertEqual(response.status_code, 401)
            response = self.client.post('/admin/login', data={
                'csrf': csrf, 'username': 'owner', 'password': 'my direct env password ☀',
            })
            self.assertEqual(response.status_code, 303)
            self.assertEqual(self.client.get('/admin/employees').status_code, 200)

    def test_password_from_env_needs_no_hash(self):
        with patch.dict(os.environ, {'ADMIN_PASSWORD': 'my direct env password', 'ADMIN_PASSWORD_HASH': ''}):
            page = self.client.get('/admin/login')
            response = self.client.post('/admin/login', data={
                'csrf': self.csrf(page), 'username': 'owner', 'password': 'my direct env password',
            })
            self.assertEqual(response.status_code, 303)

    def test_no_default_password_and_secure_cookie(self):
        with patch.dict(os.environ, {'ADMIN_PASSWORD': '', 'ADMIN_PASSWORD_HASH': '', 'ADMIN_COOKIE_SECURE': 'true'}):
            response = self.client.get('/admin/login')
            self.assertIn('hasn’t been configured', response.text)
            self.assertIn('Secure', response.headers['set-cookie'])
            self.assertIn('HttpOnly', response.headers['set-cookie'])
            self.assertIn('SameSite=strict', response.headers['set-cookie'])
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/careers').status_code, 200)


if __name__ == '__main__':
    unittest.main()
